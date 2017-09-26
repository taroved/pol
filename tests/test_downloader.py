from __future__ import print_function

from twisted.internet import reactor, defer
from twisted.logger import Logger

from pol.log import LogHandler


class MFTests(object):

    def __init__(self):
        self.log = Logger()
        pass

    def stop_callback(self, none):
        reactor.stop()
        pass

    def test_log_handler(self):
        handler = LogHandler()
        self.log.info('Test msg with {parameter} is OK', parameter="value")
        self.log.error('Test error with {parameter} is OK', parameter="value", isError=True)

        d = defer.Deferred()
        reactor.callLater(0, d.callback, None)
        d.addCallback(self.stop_callback)
        d.addErrback(lambda err: print("callback error: %s\ncallback traceback: %s" % (err.getErrorMessage(), err.getTraceback())))

        reactor.run()

