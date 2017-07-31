import json
import time, sys
from hashlib import md5
from datetime import datetime

from twisted.web import server, resource
from twisted.internet import reactor, endpoints, defer
from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody, PartialDownloadError
from twisted.web.server import NOT_DONE_YET
from twisted.web.http_headers import Headers
from twisted.web.html import escape
twisted_headers = Headers

from scrapy.http.response.text import TextResponse
from scrapy.downloadermiddlewares.decompression import DecompressionMiddleware
from scrapy.selector import Selector

from scrapy.http import Headers
from scrapy.responsetypes import responsetypes

from lxml import etree
import re

from feed import getFeedData, buildFeed

from settings import DOWNLOADER_USER_AGENT, FEED_REQUEST_PERIOD_LIMIT, DEBUG, SNAPSHOT_DIR


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

agent = BrowserLikeRedirectAgent(Agent(reactor, connectTimeout=10), redirectLimit=5)

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

def downloadStarted(response, request, url, feed_config):
    d = readBody(response)
    d.addCallback(downloadDone, request=request, response=response, feed_config=feed_config)
    d.addErrback(downloadError, request=request, url=url, response=response, feed_config=feed_config)
    return response

def downloadDone(response_str, request, response, feed_config):
    url = response.request.absoluteURI

    print 'Response <%s> ready (%s bytes)' % (url, len(response_str))
    response = buildScrapyResponse(response, response_str, url)

    response = DecompressionMiddleware().process_response(None, response, None)

    if (isinstance(response, TextResponse)):
        if feed_config:
            response_str = buildFeed(response, feed_config)
            request.setHeader(b"Content-Type", b'text/xml')
        else:
            response_str, file_name = setBaseAndRemoveScriptsAndMore(response, url)

    request.write(response_str)
    request.finish()

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
    sys.stderr.write('\n'.join([str(datetime.utcnow()), url, 'Downloader error: ' + error.getErrorMessage(), 'Traceback: ' + error.getTraceback()]))
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
        print 'Request <GET %s> started' % (url,)
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


endpoints.serverFromString(reactor, "tcp:1234").listen(server.Site(Downloader()))
print 'Server starting at http://localhost:1234'
reactor.run()
