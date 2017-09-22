from __future__ import print_function
import json
import time, sys
from hashlib import md5
from datetime import datetime

from twisted.logger import globalLogBeginner, formatEventAsClassicLogText, Logger
from twisted.web import server, resource
from twisted.internet import reactor, endpoints, defer
from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody, PartialDownloadError, HTTPConnectionPool
from twisted.web.server import NOT_DONE_YET
from twisted.web.http_headers import Headers
from twisted.web.html import escape
twisted_headers = Headers

from scrapy.http.response.text import TextResponse
from scrapy.downloadermiddlewares.httpcompression import HttpCompressionMiddleware
from scrapy.downloadermiddlewares.decompression import DecompressionMiddleware
from scrapy.selector import Selector

from scrapy.http.request import Request
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory

from lxml import etree
import re

from feed import getFeedData, buildFeed

from settings import DOWNLOADER_USER_AGENT, FEED_REQUEST_PERIOD_LIMIT, DEBUG, SNAPSHOT_DIR


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_log(event):
    if 'isError' in event and event['isError']:
        sys.stdout.write(bcolors.FAIL + formatEventAsClassicLogText(event) + bcolors.ENDC)
        sys.stderr.write(formatEventAsClassicLogText(event))
        sys.stderr.flush()
    else:
        sys.stdout.write(formatEventAsClassicLogText(event))
    sys.stdout.flush()

globalLogBeginner.beginLoggingTo([print_log], discardBuffer=True, redirectStandardIO=False) # requred, discardBuffer gets rid of the LimitedHistoryLogObserver, redirectStandardIO will loop print action

log = Logger()

if FEED_REQUEST_PERIOD_LIMIT:
    import redis

def check_feed_request_time_limit(url):
    if FEED_REQUEST_PERIOD_LIMIT:
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        previous_timestamp = r.get(url)
        if previous_timestamp:
            previous_timestamp = int(r.get(url))
            time_passed = int(time.time()) - previous_timestamp
            if time_passed <= FEED_REQUEST_PERIOD_LIMIT:
                # time left to wait
                return FEED_REQUEST_PERIOD_LIMIT - time_passed
        r.set(url, int(time.time()))
    return 0


#pool = HTTPConnectionPool(reactor, persistent=False)
#pool.cachedConnectionTimeout = 3

agent = BrowserLikeRedirectAgent(
            Agent(reactor,
                contextFactory=ScrapyClientContextFactory(), # skip certificate verification
                connectTimeout=10),
                #pool=pool),
            redirectLimit=5
        )

def html2json(el):
    return [
        el.tag,
        {"tag-id": el.attrib["tag-id"]},
        [html2json(e) for e in el.getchildren() if isinstance(e, etree.ElementBase)]
    ]

def setBaseAndRemoveScriptsAndMore(response, url):
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
        jsobj = html2json(tree.getroot())
        script = etree.Element('script', {'type': 'text/javascript'})
        script.text = '\n'.join((
                        'var html2json = ' + json.dumps(jsobj) + ';',
                        'var snapshot_time = "' + file_name + '";'
                    ))
        body[0].append(script)

    return (etree.tostring(tree, method='html'), file_name)

def buildScrapyResponse(response, body, url):
    status = response.code
    headers = Headers({k:','.join(v) for k,v in response.headers.getAllRawHeaders()})
    respcls = responsetypes.from_args(headers=headers, url=url)
    return respcls(url=url, status=status, headers=headers, body=body)

def buildScrapyRequest(url):
    return Request(url)

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
        if feed_config:
            response_str = buildFeed(response, feed_config)
            request.setHeader(b"Content-Type", b'text/xml; charset=utf-8')
        else:
            response_str, file_name = setBaseAndRemoveScriptsAndMore(response, url)

    request.write(response_str)
    request.finish()
    run_pgc()

from pympler import tracker
import gc

tr = tracker.SummaryTracker()
MON_PERIOD_SECONDS = 1 * 60 * 60 # 1 hours
mon_time = None
def mon(none):
    global mon_time
    tm = int(time.time())
    if not mon_time or tm - mon_time >= MON_PERIOD_SECONDS:
        #global pool
        #pool.closeCachedConnections()
        gc.collect()
        global tr
        for line in tr.format_diff():
            log.info(line)
    mon_time = tm

def run_pgc():
    d = defer.Deferred()
    reactor.callLater(0, d.callback, None)
    d.addCallback(mon)
    d.addErrback(lambda err: print("PGC error: %s\nPGC traceback: %s" % (err.getErrorMessage(), err.getTraceback())))

def error_html(msg):
    return "<html><body>%s</body></html" % escape(msg).replace("\n", "<br/>\n")

def downloadError(error, request=None, url=None, response=None, feed_config=None):
    # read for details: https://stackoverflow.com/questions/29423986/twisted-giving-twisted-web-client-partialdownloaderror-200-ok
    if error.type is PartialDownloadError and error.value.status == '200':
        d = defer.Deferred()
        reactor.callLater(0, d.callback, error.value.response) # error.value.response is response_str
        d.addCallback(downloadDone, request=request, response=response, feed_config=feed_config)
        d.addErrback(downloadError, request=request, url=url, response=response, feed_config=feed_config)
        return
    if DEBUG:
        request.write('Downloader error: ' + error.getErrorMessage())
        request.write('Traceback: ' + error.getTraceback())
    else:
        request.write(error_html('Something wrong. Contact us by email: politepol.com@gmail.com \n Scary mantra: ' + error.getErrorMessage()))
    sys.stderr.write('\n'.join([str(datetime.utcnow()), request.uri, url, 'Downloader error: ' + error.getErrorMessage(), 'Traceback: ' + error.getTraceback()]))
    request.finish()


class Downloader(resource.Resource):
    isLeaf = True

    feed_regexp = re.compile('^/feed1?/(\d{1,10})$')

    def startRequest(self, request, url, feed_config = None):
        d = agent.request(
            'GET',
            url,
            twisted_headers({
                'Accept': ['text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'],
                'Accept-Encoding': ['gzip, deflate, sdch'],
                'User-Agent': [DOWNLOADER_USER_AGENT]
            }),
            None
        )
        print('Request <GET %s> started' % (url,))
        d.addCallback(downloadStarted, request=request, url=url, feed_config=feed_config)
        d.addErrback(downloadError, request=request, url=url)

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
                res = getFeedData(request, feed_id)

                if isinstance(res, basestring): # error message
                    return res

                url, feed_config = res
                self.startRequest(request, url, feed_config)
                return NOT_DONE_YET
        else: # neither page and feed
            return 'Url is required'


port = sys.argv[1] if len(sys.argv) >= 2 else 1234

endpoints.serverFromString(reactor, "tcp:%s" % port).listen(server.Site(Downloader()))
print('Server starting at http://localhost:%s' % port)
reactor.run()
