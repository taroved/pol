import json

from twisted.web import server, resource
from twisted.internet import reactor, endpoints
from twisted.web.client import HTTPClientFactory, _makeGetterFactory 
from twisted.web.server import NOT_DONE_YET

from decompression import DecompressionMiddleware


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


def downloadDone(response, request=None, page_factory=None):
    response = DecompressionMiddleware().process_response(response)

    request.write(response)
    request.finish()

def downloadError(error, request=None, page_factory=None):
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
                    })
        d = page_factory.deferred
        d.addCallback(downloadDone, request=request, page_factory=page_factory)
        d.addErrback(downloadError, request=request, page_factory=page_factory)
        return NOT_DONE_YET

endpoints.serverFromString(reactor, "tcp:8080").listen(server.Site(Counter()))
reactor.run()
