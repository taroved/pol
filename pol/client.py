from __future__ import division, absolute_import

import warnings

from twisted.python.failure import Failure
from twisted.internet import defer, protocol, reactor
from twisted.web._newclient import (
    HTTP11ClientProtocol,
    PotentialDataLoss,
    Request,
    RequestGenerationFailed,
    RequestNotSent,
    RequestTransmissionFailed,
    Response,
    ResponseDone,
    ResponseFailed,
    ResponseNeverReceived,
    _WrapperException,
    )
from twisted.web.client import PartialDownloadError

IGNORE_SIZE = 0

class _PpReadBodyProtocol(protocol.Protocol):
    """
    Protocol that collects data sent to it.

    This is a helper for L{IResponse.deliverBody}, which collects the body and
    fires a deferred with it.

    @ivar deferred: See L{__init__}.
    @ivar status: See L{__init__}.
    @ivar message: See L{__init__}.

    @ivar dataBuffer: list of byte-strings received
    @type dataBuffer: L{list} of L{bytes}
    """

    def __init__(self, status, message, deferred, max_size):
        """
        @param status: Status of L{IResponse}
        @ivar status: L{int}

        @param message: Message of L{IResponse}
        @type message: L{bytes}

        @param deferred: deferred to fire when response is complete
        @type deferred: L{Deferred} firing with L{bytes}
        """
        self.deferred = deferred
        self.status = status
        self.message = message
        self.dataBuffer = []

        self.max_size = max_size
        self.buffer_size = 0


    def dataReceived(self, data):
        """
        Accumulate some more bytes from the response.
        """
        self.dataBuffer.append(data)

        self.buffer_size += len(data)
        if self.max_size != IGNORE_SIZE and self.buffer_size > self.max_size:
            self.transport.stopProducing() # https://twistedmatrix.com/trac/ticket/8227


    def connectionLost(self, reason):
        """
        Deliver the accumulated response bytes to the waiting L{Deferred}, if
        the response body has been completely received without error.
        """
        if reason.check(ResponseDone):
            self.deferred.callback(b''.join(self.dataBuffer))
        elif reason.check(PotentialDataLoss):
            self.deferred.errback(
                PartialDownloadError(self.status, self.message,
                                     b''.join(self.dataBuffer)))
        else:
            self.deferred.errback(reason)



def ppReadBody(response, max_size):
    """
    Get the body of an L{IResponse} and return it as a byte string.

    This is a helper function for clients that don't want to incrementally
    receive the body of an HTTP response.

    @param response: The HTTP response for which the body will be read.
    @type response: L{IResponse} provider

    @return: A L{Deferred} which will fire with the body of the response.
        Cancelling it will close the connection to the server immediately.
    """
    def cancel(deferred):
        """
        Cancel a L{readBody} call, close the connection to the HTTP server
        immediately, if it is still open.

        @param deferred: The cancelled L{defer.Deferred}.
        """
        abort = getAbort()
        if abort is not None:
            abort()

    d = defer.Deferred(cancel)
    protocol = _PpReadBodyProtocol(response.code, response.phrase, d, max_size=max_size)
    def getAbort():
        return getattr(protocol.transport, 'abortConnection', None)

    response.deliverBody(protocol)

    if protocol.transport is not None and getAbort() is None:
        warnings.warn(
            'Using readBody with a transport that does not have an '
            'abortConnection method',
            category=DeprecationWarning,
            stacklevel=2)

    def respFailed(fail):
        if fail.type is ResponseFailed and max_size != IGNORE_SIZE and protocol.buffer_size > max_size:
            d = defer.Deferred()
            reactor.callLater(0, d.errback, ResponseIsTooBig('Response is too big', max_size))
            return d
        else:
            return fail

    d.addErrback(respFailed)

    return d


class ResponseIsTooBig(Exception):
    """
    Response is too big

    @ivar max_size: Max length for response in bytes
    """
    def __init__(self, reason, max_size):
        Exception.__init__(self, reason, max_size)
        self.max_size = max_size
