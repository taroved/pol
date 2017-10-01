from __future__ import print_function

import os

from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor, defer, endpoints
from twisted.logger import Logger

from pol.log import LogHandler
from pol.server import Server


class MFTests(object):

    def __init__(self):
        self.log = Logger()

    def start_static(self):
        resource = File(os.getcwd() + '/tests/pages')
        factory = Site(resource)
        endpoint = endpoints.TcP4ServerEndpoint(reactor, 0)
        endpoint.listen(factory)
        # reactor.run()

    def send_request(self):
        pass

    def stop_callback(self, none):
        reactor.stop()

    def test_log_handler(self):
        handler = LogHandler()
        self.log.info('Test msg with {parameter} is OK', parameter="value")
        self.log.error('Test error with {parameter} is OK', parameter="value")
        self.log.error('Test error with {parameter} (isError={isError}) is OK', parameter="value", isError=False)
        self.log.error('Test error with {parameter} (isError={isError}) is OK', parameter="value", isError=True)

        d = defer.Deferred()
        reactor.callLater(0, d.callback, None)
        d.addCallback(self.stop_callback)
        d.addErrback(lambda err: print("callback error: %s\ncallback traceback: %s" % (err.getErrorMessage(), err.getTraceback())))

        reactor.run()

    def test_server(self):
        d = defer.Deferred()
        reactor.callLater(3, d.callback, None)
        d.addCallback(self.stop_callback)
        #d.addCallback(self.send_request)
        d.addErrback(lambda err: print("callback error: %s\ncallback traceback: %s" % (err.getErrorMessage(), err.getTraceback())))

        Server(port=1234, db_creds=None, snapshot_dir='~/tmp', user_agent='', debug=False).run()


