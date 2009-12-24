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
from types import MethodType
from datetime import datetime

import transaction

from zope import interface
from zope.event import notify
from zope.component import queryUtility
from zope.proxy import removeAllProxies

from zope.publisher.publish import mapply
from zope.publisher.browser import BrowserRequest

from zope.app.publication import browser
from zope.app.publication import zopepublication
from zope.app.publication.interfaces import IBrowserRequestFactory
from zope.app.publication.interfaces import IRequestPublicationFactory

from interfaces import ICacheStrategy, AfterCallEvent, AfterExceptionCallEvent


class BrowserPublication(browser.BrowserPublication):

    def beforeTraversal(self, request):
        self.dt = datetime.now()
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

    def handleException(self, object, request, exc_info, retry_allowed=True):
        super(BrowserPublication, self).handleException(
            object, request, exc_info, retry_allowed)

        orig = removeAllProxies(object)
        if type(orig) is MethodType:
            notify(AfterExceptionCallEvent(orig.im_self, request))
        else:
            notify(AfterExceptionCallEvent(orig, request))
        

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
    if type(orig) is MethodType:
        notify(AfterCallEvent(orig.im_self, request))
    else:
        notify(AfterCallEvent(orig, request))

    txn = transaction.get()
    if txn.isDoomed():
        txn.abort()
    else:
        self.annotateTransaction(txn, request, ob)
        txn.commit()

zopepublication.ZopePublication.afterCall = afterCall
