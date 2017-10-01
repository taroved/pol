from __future__ import print_function
from datetime import datetime
from hashlib import md5
import json
import time, sys, traceback
import re

from lxml import etree

from twisted.web import server, resource
from twisted.internet import reactor, endpoints
from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody, PartialDownloadError, HTTPConnectionPool
from twisted.web.server import NOT_DONE_YET
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

from pol.log import LogHandler
from .feed import Feed

from twisted.logger import Logger


log = Logger()

class Downloader(object):

    def __init__(self, feed, debug, snapshot_dir='/tmp', stat_tool=None, mem_mon=None):
        self.feed = feed
        self.debug = debug
        self.snapshot_dir = snapshot_dir
        self.stat_tool = stat_tool
        self.mem_mon = mem_mon

    def html2json(self, el):
        return [
            el.tag,
            {"tag-id": el.attrib["tag-id"]},
            [self.html2json(e) for e in el.getchildren() if isinstance(e, etree.ElementBase)]
        ]

    def _saveResponse(self, response, url, tree):
        # save html for extended selectors
        file_name = '%s_%s' % (time.time(), md5(url).hexdigest())
        file_path = self.snapshot_dir + '/' + file_name
        with open(file_path, 'w') as f:
            f.write(url + '\n')
            for k, v in response.headers.iteritems():
                for vv in v:
                    f.write('%s: %s\n' % (k, vv))
            f.write('\n\n' + etree.tostring(tree, encoding='utf-8', method='html'))
        return file_name


    def setBaseAndRemoveScriptsAndMore(self, response, url):
        response.selector.remove_namespaces()

        tree = response.selector.root.getroottree()

        file_name = self._saveResponse(response, url, tree)

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
        return "<html><body>%s</body></html" % msg.replace("\n", "<br/>\n")

    def downloadError(self, error, request=None, url=None, response=None, feed_config=None):
        # read for details: https://stackoverflow.com/questions/29423986/twisted-giving-twisted-web-client-partialdownloaderror-200-ok
        if error.type is PartialDownloadError and error.value.status == '200':
            d = defer.Deferred()
            reactor.callLater(0, d.callback, error.value.response) # error.value.response is response_str
            d.addCallback(self.downloadDone, request=request, response=response, feed_config=feed_config)
            d.addErrback(self.downloadError, request=request, url=url, response=response, feed_config=feed_config)
            return

        if self.debug:
            request.write('Downloader error: ' + error.getErrorMessage())
            request.write('Traceback: ' + error.getTraceback())
        else:
            request.write(self.error_html('<h1>PolitePol says: "Something wrong"</h1> <p><b>Try to refresh page or contact us by email: <a href="mailto:politepol.com@gmail.com">politepol.com@gmail.com</a></b>\n(Help us to improve our service with your feedback)</p> <p><i>Scary mantra: %s</i></p>' % escape(error.getErrorMessage())))
        sys.stderr.write('\n'.join([str(datetime.utcnow()), request.uri, url, 'Downloader error: ' + error.getErrorMessage(), 'Traceback: ' + error.getTraceback()]))
        request.finish()
        
        try:
            feed_id = feed_config and feed_config['id']
            s_url = None
            if not feed_id:
                feed_id = 0
                s_url = url
            if self.stat_tool:
                self.stat_tool.trace(
                        ip = request.getHeader('x-real-ip') or request.client.host,
                        feed_id = feed_id,
                        post_cnt=0,
                        new_post_cnt=0,
                        url=s_url,
                        ex_msg=error.getErrorMessage(),
                        ex_callstack=error.getTraceback()
                    )
        except:
            traceback.print_exc(file=sys.stdout)


    def downloadStarted(self, response, request, url, feed_config):
        d = readBody(response)
        d.addCallback(self.downloadDone, request=request, response=response, feed_config=feed_config)
        d.addErrback(self.downloadError, request=request, url=url, response=response, feed_config=feed_config)
        return response

    def downloadDone(self, response_str, request, response, feed_config):
        url = response.request.absoluteURI

        print('Response <%s> ready (%s bytes)' % (url, len(response_str)))
        response = self.buildScrapyResponse(response, response_str, url)

        response = HttpCompressionMiddleware().process_response(Request(url), response, None)
        response = DecompressionMiddleware().process_response(None, response, None)

        if (isinstance(response, TextResponse)):
            ip = request.getHeader('x-real-ip') or request.client.host
            if feed_config:
                [response_str, post_cnt, new_post_cnt] = self.feed.buildFeed(response, feed_config)
                request.setHeader(b"Content-Type", b'text/xml; charset=utf-8')
                if self.stat_tool:
                    self.stat_tool.trace(ip=ip, feed_id=feed_config['id'], post_cnt=post_cnt, new_post_cnt=new_post_cnt)
            else:
                response_str, file_name = self.setBaseAndRemoveScriptsAndMore(response, url)
                if self.stat_tool:
                    self.stat_tool.trace(ip=ip, feed_id=0, post_cnt=0, new_post_cnt=0, url=url)

        request.write(response_str)
        request.finish()
        self.run_mem_mon()

    def run_mem_mon(self):
        if self.mem_mon:
            d = defer.Deferred()
            reactor.callLater(0, d.callback, None)
            d.addCallback(self.mem_mon.show_diff)
            d.addErrback(lambda err: print("Memory Monitor error: %s\nPGC traceback: %s" % (err.getErrorMessage(), err.getTraceback())))


class Site(resource.Resource):
    isLeaf = True

    feed_regexp = re.compile('^/feed1?/(\d{1,10})$')

    def __init__(self, db_creds, snapshot_dir, user_agent, debug=False, limiter=None, mem_mon=None, stat_tool=None):
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent
        self.limiter = limiter

        self.feed = Feed(db_creds)
        self.downloader = Downloader(self.feed, debug, snapshot_dir, stat_tool, mem_mon)

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

            time_left = self.limiter.check_request_time_limit(request.uri) if self.limiter else 0
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

    def __init__(self, port, db_creds, snapshot_dir, user_agent, debug=False, limiter=None, mem_mon=None):
        self.port = port
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent
        self.debug = debug
        self.limiter = limiter
        self.mem_mon = mem_mon

        self.log_handler = LogHandler()

    def run(self):
        endpoints.serverFromString(reactor, "tcp:%s" % self.port).listen(server.Site(Site(self.db_creds, self.snapshot_dir, self.user_agent, self.debug, self.limiter, self.mem_mon)))
        reactor.run()