from datetime import datetime
from hashlib import md5
import json
import time, sys, traceback
import re

from lxml import etree

from twisted.web import server, resource
from twisted.internet import reactor, endpoints, 
from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody, PartialDownloadError, HTTPConnectionPool
from twisted.web.server import 
from twisted.web.http_headers import Headers
from twisted.web.html import escape
twisted_headers = Headers
from twisted.logger import Logger

from scrapy.http.response.text import TextResponse
from scrapy.downloadermiddlewares.httpcompression import HttpCompressionMiddleware
from scrapy.downloadermiddlewares.decompression import DecompressionMiddleware
from scrapy.http.request import Request
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory

from .feed import Feed

class Downloader(object):

    def __init__(self, debug, stat_tool=None, mem_mon=None):
        self.debug = debug
        self.stat_tool = stat_tool
        self.mem_mon = mem_mon

    def html2json(self, el):
        return [
            el.tag,
            {"tag-id": el.attrib["tag-id"]},
            [html2json(e) for e in el.getchildren() if isinstance(e, etree.ElementBase)]
        ]

    def setBaseAndRemoveScriptsAndMore(self, response, url):
        response.selector.remove_namespaces()

        tree = response.selector.root.getroottree()

        # save html for extended selectors
        file_name = '%s_%s' % (time.time(), md5(url).hexdigest())
        file_path = SNAPSHOT_DIR + '/' + file_name
        with open(file_path, 'w') as f:
            f.write(url + '\n')
            for k, v in response.headers.iteritems():
                for vv in v:
                    f.write('%s: %s\n' % (k, vv))
            f.write('\n\n' + etree.tostring(tree, encoding='utf-8', method='html'))

        # set base url to html document
        head = tree.xpath("//head")
        if head:
            head = head[0]
            base = head.xpath("./base")
            if base:
                base = base[0]
            else:
                base = etree.Element("base")
                head.insert(0, base)
            base.set('href', url)

        i = 1
        for bad in tree.xpath("//*"):
            # remove scripts
            if bad.tag == 'script':
                bad.getparent().remove(bad)
            else:
                # set tag-id attribute
                bad.attrib['tag-id'] = str(i)
                i += 1

            # sanitize anchors
            if bad.tag == 'a' and 'href' in bad.attrib:
                bad.attrib['origin-href'] = bad.attrib['href']
                del bad.attrib['href']

            # remove html events
            for attr in bad.attrib:
                if attr.startswith('on'):
                    del bad.attrib[attr]

            # sanitize forms
            if bad.tag == 'form':
                bad.attrib['onsubmit'] = "return false"

        body = tree.xpath("//body")
        if body:
            # append html2json js object
            jsobj = self.html2json(tree.getroot())
            script = etree.Element('script', {'type': 'text/javascript'})
            script.text = '\n'.join((
                            'var html2json = ' + json.dumps(jsobj) + ';',
                            'var snapshot_time = "' + file_name + '";'
                        ))
            body[0].append(script)

        return (etree.tostring(tree, method='html'), file_name)

    def buildScrapyResponse(self, response, body, url):
        status = response.code
        headers = Headers({k:','.join(v) for k,v in response.headers.getAllRawHeaders()})
        respcls = responsetypes.from_args(headers=headers, url=url)
        return respcls(url=url, status=status, headers=headers, body=body)

    def error_html(self, msg):
        return "<html><body>%s</body></html" % escape(msg).replace("\n", "<br/>\n")

    def downloadError(self, error, request=None, url=None, response=None, feed_config=None):
        # read for details: https://stackoverflow.com/questions/29423986/twisted-giving-twisted-web-client-partialdownloaderror-200-ok
        if error.type is PartialDownloadError and error.value.status == '200':
            d = defer.Deferred()
            reactor.callLater(0, d.callback, error.value.response) # error.value.response is response_str
            d.addCallback(downloadDone, request=request, response=response, feed_config=feed_config)
            d.addErrback(downloadError, request=request, url=url, response=response, feed_config=feed_config)
            return

        if self.debug:
            request.write('Downloader error: ' + error.getErrorMessage())
            request.write('Traceback: ' + error.getTraceback())
        else:
            request.write(self.error_html('Something wrong. Contact us by email: politepol.com@gmail.com \n Scary mantra: ' + error.getErrorMessage()))
        sys.stderr.write('\n'.join([str(datetime.utcnow()), request.uri, url, 'Downloader error: ' + error.getErrorMessage(), 'Traceback: ' + error.getTraceback()]))
        request.finish()
        
        try:
            feed_id = feed_config and feed_config['id']
            s_url = None
            if not feed_id:
                feed_id = 0
                s_url = url
            log.info('Stat: ip={request.ip} feed_id={request.feed_id} url="{request.url}" error="{request.ex_msg}"', request=RequestStat(
                    ip = request.getHeader('x-real-ip') or request.client.host,
                    feed_id = feed_id,
                    post_cnt=0,
                    new_post_cnt=0,
                    url=s_url,
                    ex_msg=error.getErrorMessage(),
                    ex_callstack=error.getTraceback()
                ),
                stat=True
            )
        except:
            traceback.print_exc(file=sys.stdout)


    def downloadStarted(response, request, url, feed_config):
        d = readBody(response)
        d.addCallback(downloadDone, request=request, response=response, feed_config=feed_config)
        d.addErrback(downloadError, request=request, url=url, response=response, feed_config=feed_config)
        return response

    def downloadDone(response_str, request, response, feed_config):
        url = response.request.absoluteURI

        print('Response <%s> ready (%s bytes)' % (url, len(response_str)))
        response = buildScrapyResponse(response, response_str, url)

        response = HttpCompressionMiddleware().process_response(Request(url), response, None)
        response = DecompressionMiddleware().process_response(None, response, None)

        if (isinstance(response, TextResponse)):
            ip = request.getHeader('x-real-ip') or request.client.host
            if feed_config:
                [response_str, post_cnt, new_post_cnt] = self.feed.buildFeed(response, feed_config)
                request.setHeader(b"Content-Type", b'text/xml; charset=utf-8')
                log.info('Stat: ip={request.ip} feed_id={request.feed_id} post_cnt={request.post_cnt} new_post_cnt={request.new_post_cnt}', request=RequestStat(
                        ip=ip,
                        feed_id=feed_config['id'],
                        post_cnt=post_cnt,
                        new_post_cnt=new_post_cnt
                    ),
                    stat=True
                )
            else:
                response_str, file_name = setBaseAndRemoveScriptsAndMore(response, url)
                log.info('Stat: ip={request.ip} url={request.url}', request=RequestStat(
                        ip=ip,
                        feed_id=0,
                        post_cnt=0,
                        new_post_cnt=0,
                        url=url                    
                    ),
                    stat=True
                )

        request.write(response_str)
        request.finish()
        run_mem_mon()

    def run_mem_mon():
        global mem_mon
        if mem_mon:
            d = defer.Deferred()
            reactor.callLater(0, d.callback, None)
            d.addCallback(mem_mon.show_diff)
            d.addErrback(lambda err: print("Memory Monitor error: %s\nPGC traceback: %s" % (err.getErrorMessage(), err.getTraceback())))


class Site(resource.Resource):
    isLeaf = True

    feed_regexp = re.compile('^/feed1?/(\d{1,10})$')

    def __init__(self, db_creds, snapshot_dir, user_agent, debug):
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent

        self.downloader = Downloader(debug)
        self.feed = Feed(db_creds, log)

    def startRequest(self, request, url, feed_config = None):
        agent = BrowserLikeRedirectAgent(
            Agent(reactor,
                contextFactory=ScrapyClientContextFactory(), # skip certificate verification
                connectTimeout=10),
                #pool=pool),
            redirectLimit=5
        )

        d = agent.request(
            'GET',
            url,
            twisted_headers({
                'Accept': ['text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'],
                'Accept-Encoding': ['gzip, deflate, sdch'],
                'User-Agent': [self.user_agent]
            }),
            None
        )
        print('Request <GET %s> started' % (url,))
        d.addCallback(self.downloader.downloadStarted, request=request, url=url, feed_config=feed_config)
        d.addErrback(self.downloader.downloadError, request=request, url=url)

    def render_GET(self, request):
        '''
        Render page for frontend or RSS feed
        '''
        if 'url' in request.args: # page for frontend
            url = request.args['url'][0]

            self.startRequest(request, url)
            return NOT_DONE_YET
        elif self.feed_regexp.match(request.uri) is not None: # feed
            feed_id = self.feed_regexp.match(request.uri).groups()[0]

            time_left = check_feed_request_time_limit(request.uri)
            if time_left:
                request.setResponseCode(429)
                request.setHeader('Retry-After', str(time_left) + ' seconds')
                return 'Too Many Requests. Retry after %s seconds' % (str(time_left))
            else:
                res = self.feed.getFeedData(request, feed_id)

                if isinstance(res, basestring): # error message
                    return res

                url, feed_config = res
                self.startRequest(request, url, feed_config)
                return NOT_DONE_YET
        else: # neither page and feed
            return 'Url is required'


class Server(object):

    def __init__(self, port, db_creds, snapshot_dir, user_agent, debug):
        self.port = port
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent

    def setMemMonitor(_mem_mon=None)
        global mem_mon
        mem_mon = _mem_mon

    def run(self):
        endpoints.serverFromString(reactor, "tcp:%s" % self.port).listen(server.Site(Site(self.db_creds, self.snapshot_dir, self.user_agent, self.debug)))
        reactor.run()