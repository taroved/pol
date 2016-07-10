import json

from twisted.web import server, resource
from twisted.internet import reactor, endpoints
from twisted.web.client import HTTPClientFactory, _makeGetterFactory 
from twisted.web.server import NOT_DONE_YET

from scrapy.http.response.text import TextResponse
from scrapy.downloadermiddlewares.decompression import DecompressionMiddleware
from scrapy.selector import Selector

from scrapy.http import Headers
from scrapy.responsetypes import responsetypes

from lxml import etree
import re

from feed import startFeedRequest

def getPageFactory(url, contextFactory=None, *args, **kwargs):
    """
    Download a web page as a string.
    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.
    See L{HTTPClientFactory} to see what extra arguments can be passed.
    """
    return _makeGetterFactory(
        url,
        HTTPClientFactory,
        contextFactory=contextFactory,
        *args, **kwargs)


def setBaseAndRemoveScriptsAndMore(response, url):
    tree = response.selector._root.getroottree()
    
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
        # set tag-id attribute
        bad.attrib['tag-id'] = str(i)
        i += 1
        
        # remove scripts
        if bad.tag == 'script':
            bad.getparent().remove(bad)
        # sanitize anchors
        elif bad.tag == 'a' and 'href' in bad.attrib:
            bad.attrib['origin-href'] = bad.attrib['href']
            del bad.attrib['href']

        # remove html events
        for attr in bad.attrib:
            if attr.startswith('on'):
                del bad.attrib[attr]
        
        # sanitize forms
        if bad.tag == 'form':
            bad.attrib['onsubmit'] = "return false"
    
    return etree.tostring(tree, method='html')

def buildScrapyResponse(page_factory, body):
    status = int(page_factory.status)
    headers = Headers(page_factory.response_headers)
    respcls = responsetypes.from_args(headers=headers, url=page_factory.url)
    return respcls(url=page_factory.url, status=status, headers=headers, body=body)

def downloadDone(response_str, request=None, page_factory=None, url=None):
    response = buildScrapyResponse(page_factory, response_str)

    response = DecompressionMiddleware().process_response(None, response, None)

    if (isinstance(response, TextResponse)):
        response_str = setBaseAndRemoveScriptsAndMore(response, url)

    request.write(response_str)
    request.finish()

def downloadError(error, request=None, page_factory=None):
    request.write('Downloader error: ' + error.value)
    request.finish()


class Downloader(resource.Resource):
    isLeaf = True

    feed_regexp = re.compile('^/feed/(\d+)$')

    def startRequest(self, request, url):
        page_factory = getPageFactory(url,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36'
                    },
                redirectLimit=5,
                timeout=10
                )
        d = page_factory.deferred
        d.addCallback(downloadDone, request=request, page_factory=page_factory, url=url)
        d.addErrback(downloadError, request=request, page_factory=page_factory)

    def render_POST(self, request):
        obj = json.load(request.content)
        url = obj[0].encode('utf-8')

        self.startRequest(request, url)
        return NOT_DONE_YET

    def render_GET(self, request):
        '''
        Render page for frontend or RSS feed
        '''
        if 'url' in request.args:
            url = request.args['url'][0]

            self.startRequest(request, url)
            return NOT_DONE_YET
        elif self.feed_regexp.match(request.uri) is not None:
            feed_id = self.feed_regexp.match(request.uri).groups()[0]
            startFeedRequest(request, feed_id)
            return NOT_DONE_YET
        else:
            return 'Url is required'


endpoints.serverFromString(reactor, "tcp:1234").listen(server.Site(Downloader()))
print 'Server starting at http://localhost:1234'
reactor.run()
