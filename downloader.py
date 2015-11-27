import json

from twisted.web import server, resource
from twisted.internet import reactor, endpoints
from twisted.web.client import HTTPClientFactory, _makeGetterFactory 
from twisted.web.server import NOT_DONE_YET

from scrapy.http.response import Response
from scrapy.downloadermiddlewares.decompression import DecompressionMiddleware
from scrapy.selector import Selector

from lxml import etree


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


def setBaseAndRemoveScripts(selector, url):
    tree = selector._root.getroottree()
    
    # set base url to html document
    head = tree.xpath("//head")
    if head:
        head = head[0]
        base = head.xpath("./base")
        if base:
            base = base[0]
        else:
            base = etree.Element("base")
            head.append(base)
        base.set('href', url)

    for bad in tree.xpath("//*"):
        # remove scripts
        if bad.tag == 'script':
            bad.getparent().remove(bad)
        # remove html events
        for attr in bad.attrib:
            if attr.startswith('on'):
                del bad.attrib[attr]
    
    return etree.tostring(tree, pretty_print=True)

def downloadDone(response_str, request=None, page_factory=None, url=None):
    response = Response(url, body=response_str)
    response = DecompressionMiddleware().process_response(None, response, None)

    sel = Selector(response)
    response_str = setBaseAndRemoveScripts(sel, url)

    request.write(response_str)
    request.finish()

def downloadError(error, request=None, page_factory=None):
    import pdb; pdb.set_trace()
    request.write('Downloader error: ' + error.value)
    request.finish()


class Counter(resource.Resource):
    isLeaf = True

    def render_POST(self, request):
        obj = json.load(request.content)
        url = obj[0].encode('utf-8')

        page_factory = getPageFactory(url,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36'
                    },
                redirectLimit=13,
                timeout=5
                )
        d = page_factory.deferred
        d.addCallback(downloadDone, request=request, page_factory=page_factory, url=url)
        d.addErrback(downloadError, request=request, page_factory=page_factory)
        return NOT_DONE_YET

    def render_GET(self, request):
        '''
        Render page for frontend
        '''
        url = request.args['url'][0]

        page_factory = getPageFactory(url,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36'
                    },
                redirectLimit=13,
                timeout=5
                )
        d = page_factory.deferred
        d.addCallback(downloadDone, request=request, page_factory=page_factory, url=url)
        d.addErrback(downloadError, request=request, page_factory=page_factory)
        return NOT_DONE_YET



endpoints.serverFromString(reactor, "tcp:1234").listen(server.Site(Counter()))
reactor.run()
