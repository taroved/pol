from __future__ import print_function
from datetime import datetime
from hashlib import md5
import json
import pickle
import time, sys, traceback
import re

from lxml import etree

from twisted.web import server, resource
from twisted.internet import reactor, endpoints, defer
from twisted.web.client import Agent, BrowserLikeRedirectAgent, PartialDownloadError, HTTPConnectionPool
from twisted.web.server import NOT_DONE_YET
from twisted.web.http_headers import Headers
from twisted.web.http import INTERNAL_SERVER_ERROR
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
from scrapy.selector import Selector

from pol.log import LogHandler
from .feed import Feed
from .client import ppReadBody, IGNORE_SIZE

from twisted.logger import Logger


log = Logger()

class Downloader(object):

    def __init__(self, feed, debug, snapshot_dir, stat_tool, memon, request,
                 url, feed_config, selector_defer, sanitize, max_size):
        self.feed = feed
        self.debug = debug
        self.snapshot_dir = snapshot_dir
        self.stat_tool = stat_tool
        self.memon = memon
        self.request = request
        self.url = url
        self.feed_config=feed_config
        self.selector_defer = selector_defer
        self.sanitize = sanitize
        self.max_size = max_size

    def html2json(self, el):
        return [
            el.tag,
            {k: v for (k,v) in el.items() if k in ['tag-id', 'class']},  # attributes
            [self.html2json(e) for e in el.getchildren() if isinstance(e, etree.ElementBase)]
        ]

    def _saveResponse(self, headers, url, tree):
        # save html for extended selectors
        file_name = '%s_%s' % (time.time(), md5(url).hexdigest())
        file_path = self.snapshot_dir + '/' + file_name
        with open(file_path, 'w') as f:
            f.write(url + '\n')
            for k, v in headers.iteritems():
                for vv in v:
                    f.write('%s: %s\n' % (k, vv))
            f.write('\n\n' + etree.tostring(tree, encoding='utf-8', method='html'))
        return file_name

    def sanitizeAndNumerate(self, selector, numerate=True, sanitize_anchors=True):

        tree = selector.root.getroottree()

        i = 1
        for bad in tree.xpath("//*"):
            # remove scripts and iframes
            if bad.tag in ['script', 'iframe']:
                bad.getparent().remove(bad)
            elif numerate:
                # set tag-id attribute
                bad.attrib['tag-id'] = str(i)
                i += 1

            # sanitize anchors
            if sanitize_anchors and bad.tag == 'a' and 'href' in bad.attrib:
                bad.attrib['origin-href'] = bad.attrib['href']
                del bad.attrib['href']

            # remove html events
            for attr in bad.attrib:
                if attr.startswith('on'):
                    del bad.attrib[attr]

            # make clickable for mobile
            bad.attrib['onclick'] = ""

            # sanitize forms
            if bad.tag == 'form':
                bad.attrib['onsubmit'] = "return false"


    def setBaseAndRemoveScriptsAndMore(self, selector, headers, url):
        selector.remove_namespaces()

        tree = selector.root.getroottree()

        if self.snapshot_dir:
            file_name = self._saveResponse(headers, url, tree)
        else:
            file_name = 'DISABLED'

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
            base.set('href', url.decode('utf-8'))

        self.sanitizeAndNumerate(selector)

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

        return etree.tostring(tree, method='html')

    def buildScrapyResponse(self, response, body, url):
        status = response.code
        headers = Headers({k:','.join(v) for k,v in response.headers.getAllRawHeaders()})
        respcls = responsetypes.from_args(headers=headers, url=url)
        return respcls(url=url, status=status, headers=headers, body=body)

    def error_html(self, msg):
        return "<html><body>%s</body></html>" % msg.replace("\n", "<br/>\n")

    def downloadError(self, error):
        # read for details: https://stackoverflow.com/questions/29423986/twisted-giving-twisted-web-client-partialdownloaderror-200-ok
        if error.type is PartialDownloadError and error.value.status == '200':
            d = defer.Deferred()
            reactor.callLater(0, d.callback, error.value.response) # error.value.response is response_str
            d.addCallback(self.downloadDone)
            d.addErrback(self.downloadError)
            return

        if self.selector_defer:
            self.selector_defer.errback(error)
        else:
            try:
                if self.stat_tool:
                    feed_id = self.feed_config and self.feed_config['id']
                    s_url = None
                    if not feed_id:
                        feed_id = 0
                        s_url = self.url
                    self.stat_tool.trace(
                            ip = self.request.getHeader('x-real-ip') or self.request.client.host,
                            feed_id = feed_id,
                            post_cnt=0,
                            new_post_cnt=0,
                            url=s_url,
                            ex_msg=error.getErrorMessage(),
                            ex_callstack=error.getTraceback()
                        )
                else:
                    sys.stderr.write('\n'.join(
                        [str(datetime.utcnow()), self.request.uri, self.url, 'Downloader error: ' + error.getErrorMessage(),
                         'Traceback: ' + error.getTraceback()]))
            except:
                traceback.print_exc(file=sys.stdout)

            self.request.setResponseCode(INTERNAL_SERVER_ERROR)
            if self.debug:
                self.request.write('Downloader error: ' + error.getErrorMessage())
                self.request.write('Traceback: ' + error.getTraceback())
            else:
                err_message = self.error_html('<h1>PolitePol says: "Something wrong"</h1> <p><b>Try to refresh page or contact us by email: <a href="mailto:politepol.com@gmail.com">politepol.com@gmail.com</a></b>\n(Help us to improve our service with your feedback)</p> <p><i>Scary mantra: %s</i></p>' % escape(error.getErrorMessage()))
                self.request.write(err_message)

            self.request.finish()

    def downloadStarted(self, response):
        self.response = response

        d = ppReadBody(response, self.max_size)
        d.addCallback(self.downloadDone)
        d.addErrback(self.downloadError)
        return response

    def downloadDone(self, response_str):
        url = self.response.request.absoluteURI

        print('Response <%s> ready (%s bytes)' % (url, len(response_str)))
        sresponse = self.buildScrapyResponse(self.response, response_str, url)

        if self.selector_defer:
            self.selector_defer.callback(sresponse)
        else:
            self.writeResponse(sresponse)
            self.run_memon()

    def writeResponse(self, sresponse): #, response_str='PolitePol: Local page processing is failed'
        sresponse = HttpCompressionMiddleware().process_response(Request(sresponse.url), sresponse, None)
        sresponse = DecompressionMiddleware().process_response(None, sresponse, None)

        response_headers = self.prepare_response_headers(sresponse.headers)

        if (isinstance(sresponse, TextResponse)):
            ip = self.request.getHeader('x-real-ip') or self.request.client.host
            response_str = self.prepare_response_str(sresponse.selector, sresponse.headers, sresponse.body_as_unicode(), sresponse.url, ip)
            if self.feed_config:
                response_headers = {b"Content-Type": b'text/xml; charset=utf-8'}
        else: # images and such
            response_str = sresponse.body

        for k, v in response_headers.items():
            self.request.setHeader(k, v)

        self.request.write(response_str)
        self.request.finish()

    def prepare_response_headers(self, headers):
        return {}

    def prepare_response_str(self, selector, headers, page_unicode, url, ip=None):
        if self.feed_config:
            if self.sanitize:
                self.sanitizeAndNumerate(selector, numerate=False, sanitize_anchors=False)
            [response_str, post_cnt, new_post_cnt] = self.feed.buildFeed(selector, page_unicode, self.feed_config)
            if self.stat_tool:
                self.stat_tool.trace(ip=ip, feed_id=self.feed_config['id'], post_cnt=post_cnt, new_post_cnt=new_post_cnt)
        else:
            response_str = self.setBaseAndRemoveScriptsAndMore(selector, headers, url)
            if self.stat_tool:
                self.stat_tool.trace(ip=ip, feed_id=0, post_cnt=0, new_post_cnt=0, url=url)
        return response_str


    def run_memon(self):
        if self.memon:
            d = defer.Deferred()
            reactor.callLater(0, d.callback, None)
            d.addCallback(self.memon.show_diff)
            d.addErrback(lambda err: print("Memory Monitor error: %s\nPGC traceback: %s" % (err.getErrorMessage(), err.getTraceback())))


class Site(resource.Resource):
    isLeaf = True

    feed_regexp = re.compile(b'^/feed/(\d{1,10})')


    def __init__(self, db_creds, snapshot_dir, user_agent, debug=False, limiter=None, memon=None, stat_tool=None, prefetch_dir=None, feed=None, downloadercls=None, max_size=IGNORE_SIZE):
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent
        self.limiter = limiter
        self.prefetch_dir = prefetch_dir

        self.feed = feed or Feed(db_creds)
        self.debug = debug
        self.stat_tool = stat_tool
        self.memon= memon
        self.max_size = max_size
        self.downloadercls = downloadercls or Downloader

    def startRequest(self, request, url, feed_config = None, selector_defer=None, sanitize=False):
        downloader = self.downloadercls(self.feed, self.debug, self.snapshot_dir, self.stat_tool, self.memon,
                                        request=request, url=url, feed_config=feed_config,
                                        selector_defer=selector_defer, sanitize=sanitize, max_size=self.max_size)

        sresponse = self.tryLocalPage(url)
        if sresponse:
            if selector_defer:
                reactor.callLater(0, selector_defer.callback, sresponse)
            else:
                downloader.writeResponse(request, sresponse, feed_config)
        else:
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
            d.addCallback(downloader.downloadStarted)
            d.addErrback(downloader.downloadError)

    def tryLocalPage(self, url):
        if self.prefetch_dir:
            m = md5(url).hexdigest()
            domain = urlparse(url).netloc
            try:
                with open(self.prefetch_dir + '/' + m + '.' + domain) as f:
                    return pickle.load(f)
            except IOError:
                pass
        return None

    def render_GET(self, request):
        '''
        Render page for frontend or RSS feed
        '''
        if b'url' in request.args: # page for frontend
            url = request.args[b'url'][0]

            self.startRequest(request, url, sanitize=True)
            return NOT_DONE_YET
        elif self.feed_regexp.match(request.uri) is not None: # feed

            feed_id = self.feed_regexp.match(request.uri).groups()[0]
            sanitize = request.uri.endswith(b'?sanitize=Y')

            time_left = self.limiter.check_request_time_limit(request.uri) if self.limiter else 0
            if time_left:
                request.setResponseCode(429)
                request.setHeader('Retry-After', str(time_left) + ' seconds')
                return b'Too Many Requests. Retry after %s seconds' % (str(time_left))
            else:
                res = self.feed.getFeedData(feed_id)

                if isinstance(res, basestring): # error message
                    return res

                url, feed_config = res
                self.startRequest(request, url, feed_config, sanitize=sanitize)
                return NOT_DONE_YET
        else: # neither page and feed
            return 'Url is invalid'


class Server(object):

    def __init__(self, port, db_creds, snapshot_dir, user_agent, debug=False, limiter=None, memon=None, stat_tool=None, prefetch_dir=None, feed=None, sitecls=None, downloadercls=None, max_size=IGNORE_SIZE):
        self.port = port
        self.db_creds = db_creds
        self.snapshot_dir = snapshot_dir
        self.user_agent = user_agent
        self.debug = debug
        self.limiter = limiter
        self.memon = memon
        self.stat_tool=stat_tool
        self.prefetch_dir = prefetch_dir

        self.log_handler = LogHandler()

        if not sitecls:
            sitecls = Site

        self.site = sitecls(self.db_creds, self.snapshot_dir, self.user_agent, self.debug, self.limiter, self.memon, self.stat_tool, self.prefetch_dir, feed, downloadercls=downloadercls, max_size=max_size)

    def requestSelector(self, url=None, feed_config=None):
        d = defer.Deferred()
        self.site.startRequest(None, url, feed_config=feed_config, selector_defer=d)
        return d

    def run(self):
        endpoints.serverFromString(reactor, "tcp:%s" % self.port).listen(server.Site(self.site))
        reactor.run()
