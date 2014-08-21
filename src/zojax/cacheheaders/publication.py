##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""

$Id$
"""
import logging
import sys
import transaction

from types import MethodType
from datetime import datetime

from zope import interface
from zope.event import notify
from zope.component import queryUtility, queryMultiAdapter, getUtility
from zope.location import LocationProxy
from zope.proxy import removeAllProxies
from zope.security.checker import ProxyFactory
from zope.security.proxy import removeSecurityProxy

from zope.publisher.browser import BrowserRequest
from zope.publisher.interfaces import Retry
from zope.publisher.publish import mapply

from zope.app.exception.interfaces import ISystemErrorView
from zope.app.publication import browser
from zope.app.publication import zopepublication
from zope.app.publication.interfaces import IBrowserRequestFactory
from zope.app.publication.interfaces import IRequestPublicationFactory
from zope.app.publication.zopepublication import tryToLogWarning, tryToLogException
from zope.app.publisher.browser import queryDefaultViewName
from zope.publisher.interfaces import IExceptionSideEffects

from ZODB.POSException import ConnectionStateError, ReadOnlyError, ConflictError
from ZODB.interfaces import IDatabase
#from ZODB.POSException import ReadOnlyError
from zope.cachedescriptors.property import Lazy

from interfaces import ICacheStrategy, AfterCallEvent #, AfterExceptionCallEvent


class BrowserPublication(browser.BrowserPublication):

    def beforeTraversal(self, request):
        self.dt = datetime.now()

        if self.isReadonly:
            request.response.setHeader('X-Readonly', 'true')

        super(BrowserPublication, self).beforeTraversal(request)

    def callObject(self, request, ob):
        if request.method == 'GET':
            orig = removeAllProxies(ob)
            if type(orig) is MethodType:
                strategy = ICacheStrategy(orig.im_self, None)
            else:
                strategy = ICacheStrategy(orig, None)

            if strategy is not None:
                strategy = strategy.__bind__(request)
                if not strategy.isModified():
                    request.response.setStatus(304)
                    strategy.setNotModifiedHeaders()
                    return ''

                result = mapply(ob, request.getPositionalArguments(), request)
                strategy.setCacheHeaders()
                return result

        return mapply(ob, request.getPositionalArguments(), request)

    def afterCall(self, request, ob):
        td = datetime.now() - self.dt
        secs = (td.days * 86400 + td.seconds) + (0.000001 * td.microseconds)

        request.response.setHeader('X-Generated-Time', '%0.5f sec'%secs)

        return super(BrowserPublication, self).afterCall(request, ob)

    @Lazy
    def isReadonly(self):
        readonly = False

        db = getUtility(IDatabase)
        conn = db.open()

        if conn.isReadOnly():
            readonly = True

        conn.close()

        return readonly


class BrowserFactory(object):
    interface.implements(IRequestPublicationFactory)

    def canHandle(self, environment):
        return True

    def __call__(self):
        request_class = queryUtility(
            IBrowserRequestFactory, default=BrowserRequest)
        return request_class, BrowserPublication


def afterCall(self, request, ob):
    orig = removeAllProxies(ob)
    try:
        if type(orig) is MethodType:
            notify(AfterCallEvent(orig.im_self, request))
        else:
            notify(AfterCallEvent(orig, request))
    except ConnectionStateError:
        pass

    txn = transaction.get()
    if txn.isDoomed():
        txn.abort()
    else:
        self.annotateTransaction(txn, request, ob)
        try:
            txn.commit()
        except ReadOnlyError:
            txn.abort()

#oldHandleException = zopepublication.ZopePublication.handleException

def handleException(self, object, request, exc_info, retry_allowed=True):
    #orig = removeAllProxies(object)

    transaction.abort()

    if retry_allowed and isinstance(exc_info[1], Retry):
        raise

    if retry_allowed and isinstance(exc_info[1], ConflictError):
        tryToLogWarning(
            'ZopePublication',
            'Competing writes/reads at %s: %s'
            % (request.get('PATH_INFO', '???'),
               exc_info[1],
               ),
            )
        raise Retry(exc_info)

    self._logErrorWithErrorReportingUtility(object, request, exc_info)

    response = request.response
    response.reset()
    exception = None
    legacy_exception = not isinstance(exc_info[1], Exception)
    if legacy_exception:
        response.handleException(exc_info)
        if isinstance(exc_info[1], str):
            tryToLogWarning(
                'Publisher received a legacy string exception: %s.'
                ' This will be handled by the request.' %
                exc_info[1])
        else:
            tryToLogWarning(
                'Publisher received a legacy classic class exception: %s.'
                ' This will be handled by the request.' %
                exc_info[1].__class__)
    else:
        self.beginErrorHandlingTransaction(
            request, object, 'application error-handling')
        view = None
        try:
            loc = object
            if not hasattr(object, '__parent__'):
                loc = removeSecurityProxy(object)
                loc = getattr(loc, 'im_self', loc)
                loc = getattr(loc, '__self__', loc)
                loc = ProxyFactory(loc)

            exception = LocationProxy(exc_info[1], loc, '')
            name = queryDefaultViewName(exception, request)
            if name is not None:
                view = queryMultiAdapter(
                    (exception, request), name=name)
        except:
            tryToLogException('Exception while getting view on exception')

        if view is not None:
            try:
                body = mapply(view, (), request)
                response.setResult(body)
                transaction.commit()
                if (ISystemErrorView.providedBy(view)
                    and view.isSystemError()):
                    try:
                        raise exc_info[0], exc_info[1], exc_info[2]
                    except:
                        logging.getLogger('SiteError').exception(
                            str(request.URL),
                            )
            except ReadOnlyError:
                transaction.abort()
            except:
                tryToLogException('Exception while rendering view on exception')
                self._logErrorWithErrorReportingUtility(
                    object, request, sys.exc_info())
                view = None

        if view is None:
            response.handleException(exc_info)
            transaction.abort()
        try:
            adapter = IExceptionSideEffects(exception, None)
        except:
            tryToLogException(
                'Exception while getting IExceptionSideEffects adapter')
            adapter = None

        if adapter is not None:
            self.beginErrorHandlingTransaction(
                request, object, 'application error-handling side-effect')
            try:
                adapter(object, request, exc_info)
                transaction.commit()
            except ReadOnlyError:
                transaction.abort()
            except:
                tryToLogException('Exception while calling'
                    ' IExceptionSideEffects adapter')
                transaction.abort()

    #if type(orig) is MethodType:
    #    notify(AfterExceptionCallEvent(orig.im_self, request))
    #else:
    #   notify(AfterExceptionCallEvent(orig, request))

zopepublication.ZopePublication.afterCall = afterCall

zopepublication.ZopePublication.handleException = handleException
