import w3lib.url
import w3lib.html

from lxml import etree
import re, sys
from hashlib import md5

from feedgenerator import Rss201rev2Feed, Enclosure
import datetime
from dateutil import parser as dateutil_parser

import psycopg2
from contextlib import closing
from settings import DATABASES, DOWNLOADER_USER_AGENT
from twisted.logger import Logger

from .db import get_conn


log = Logger()

class Feed(object):

    url_hash_regexp = re.compile('(#.*)?$')

    POST_TIME_DISTANCE = 15 # minutes, RSS Feed Reader skip same titles created in 10 min interval

    FIELD_IDS = {'title': 1, 'description': 2, 'link': 3, 'date': 4}

    def __init__(self, db_creds):
        self.db_creds = db_creds


    def save_post(self, conn, created, feed_id, post_fields):
        cur = conn.cursor()
        cur.execute("""insert into frontend_post (md5sum, created, feed_id)
                        values (%s, %s, %s) RETURNING id""", (post_fields['md5'], created, feed_id))
        post_id = cur.fetchone()[0]
        log.info('Post saved id:{id!r}', id=post_id)
        return post_id

    def fill_time(self, feed_id, items):
        if not items:
            return 0

        new_post_cnt = 0
        for item in items:
            #create md5
            h = md5(b'')
            for key in ['title', 'description', 'link']:
                if key in item:
                    h.update(item[key].encode('utf-8'))
            item['md5'] = h.hexdigest()

        #fetch dates from db
        fetched_dates = {}
        with closing(get_conn(self.db_creds)) as conn:
            cur = conn.cursor()
            # Use parameterized query with PostgreSQL
            placeholders = ','.join(['%s'] * len(items))
            hashes = [i['md5'] for i in items]
            
            cur.execute("""select p.md5sum, p.created, p.id
                           from frontend_post p
                           where p.md5sum in ({})
                           and p.feed_id=%s""".format(placeholders), hashes + [feed_id])
            rows = cur.fetchall()
            log.debug('Selected {count!r} posts', count=len(rows))
            for row in rows:
                md5hash = row[0]
                created = row[1]
                post_id = row[2]
                fetched_dates[md5hash] = created

            cur_time = datetime.datetime.utcnow()
            saved_times = {}
            for item in items:
                if item['md5'] in fetched_dates:
                    item['time'] = fetched_dates[item['md5']]
                else:
                    if item['md5'] in saved_times:
                        item['time'] = saved_times[item['md5']]
                    else:
                        self.save_post(conn, cur_time, feed_id, item)
                        saved_times[item['md5']] = cur_time
                        item['time'] = cur_time
                        new_post_cnt += 1
                    cur_time -= datetime.timedelta(minutes=self.POST_TIME_DISTANCE)
        return new_post_cnt

    def _build_link(self, html, doc_url, url):
        from urllib.parse import urljoin
        base_url = w3lib.html.get_base_url(html, doc_url)
        # Use urllib.parse.urljoin instead of deprecated w3lib.url.urljoin_rfc
        result = urljoin(base_url, url)
        # In Python 3, result is already a string
        return result if isinstance(result, str) else result.decode('utf-8')

    def _parse_date(self, date_str):
        """Parse date string to datetime object. Returns None if parsing fails."""
        if not date_str or not date_str.strip():
            return None
        try:
            # Try to parse the date string using dateutil parser which is quite flexible
            parsed_date = dateutil_parser.parse(date_str.strip())
            # Make sure the date has timezone info, if not, assume UTC
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=None)
            return parsed_date
        except (ValueError, TypeError, OverflowError):
            log.warn('Failed to parse date: {date!r}', date=date_str)
            return None

    def buildFeed(self, selector, page_unicode, feed_config):
        selector.remove_namespaces()

        selector = selector
        tree = selector.root.getroottree()
        # get data from html
        items = []
        for node in selector.xpath(feed_config['xpath']):
            item = {}
            required_count = 0
            required_found = 0
            for field_name in ['title', 'description', 'link', 'date']:
                if field_name in feed_config['fields']:
                    if feed_config['required'][field_name]:
                        required_count += 1

                    extracted = node.xpath(feed_config['fields'][field_name]).extract()
                    if extracted:
                        item[field_name] = u''.join(extracted)
                        if feed_config['required'][field_name]:
                            required_found += 1
                        if field_name == 'link':
                            item['link'] = self._build_link(page_unicode, feed_config['uri'], item[field_name])

            if required_count == required_found:
                items.append(item)

        title = selector.xpath('//title/text()').extract_first()

        #build feed
        feed = Rss201rev2Feed(
            title = title if title else 'PolitePol: ' + feed_config['uri'],
            link=feed_config['uri'],
            description="Generated by PolitePol.\n"+\
                "Source page: " + feed_config['uri'],
            language="en",
        )
        new_post_cnt = self.fill_time(feed_config['id'], items)

        for item in items:
            title = item['title'] if 'title' in item else ''
            desc = item['description'] if 'description' in item else ''
            
            # Use extracted date if available, otherwise use the generated time
            if 'date' in item and item['date']:
                parsed_date = self._parse_date(item['date'])
                time = parsed_date if parsed_date else (item['time'] if 'time' in item else datetime.datetime.utcnow())
            else:
                time = item['time'] if 'time' in item else datetime.datetime.utcnow()
            
            if 'link' in item:
                link = item['link']
            else:
                link = self.url_hash_regexp.sub('#' + md5((title+desc).encode('utf-8')).hexdigest(), feed_config['uri'])
            feed.add_item(
                title = title,
                link = link,
                unique_id = link,
                description = desc,
                #enclosure=Enclosure(fields[4], "32000", "image/jpeg") if  4 in fields else None, #"Image"
                pubdate = time
            )
        return [feed.writeString('utf-8'), len(items), new_post_cnt]

    def getFeedData(self, feed_id):
        # get url, xpathes
        feed = {}

        with closing(get_conn(self.db_creds, dict_result=True)) as conn:
            cur = conn.cursor()
            cur.execute("""select f.uri, f.xpath as feed_xpath, fi.name, ff.xpath, fi.required
                           from frontend_feed f
                           right join frontend_feedfield ff on ff.feed_id=f.id
                           left join frontend_field fi on fi.id=ff.field_id
                           where f.id=%s""", (feed_id,))
            rows = cur.fetchall()

            for row in rows:
                if not feed:
                    feed['id'] = feed_id
                    feed['uri'] = row['uri']
                    # In Python 3 with PostgreSQL, strings are already decoded
                    feed['xpath'] = row['feed_xpath'] if isinstance(row['feed_xpath'], str) else row['feed_xpath'].decode('utf-8')
                    feed['fields'] = {}
                    feed['required'] = {}
                xpath_val = row['xpath'] if isinstance(row['xpath'], str) else row['xpath'].decode('utf-8')
                feed['fields'][row['name']] = xpath_val
                feed['required'][row['name']] = row['required']

        if feed:
            return [feed['uri'], feed]
        else:
            return 'Feed generator error: config of feed is empty'
