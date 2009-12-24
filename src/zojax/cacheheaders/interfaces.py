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
from zope import schema, interface
from zope.component.interfaces import IObjectEvent


class IAfterCallEvent(IObjectEvent):
    """ after call event """

    request = interface.Attribute('Request')


class AfterCallEvent(object):
    interface.implements(IAfterCallEvent)

    def __init__(self, object, request):
        self.object = object
        self.request = request


class IAfterExceptionCallEvent(IObjectEvent):
    """ after call event """

    request = interface.Attribute('Request')


class AfterExceptionCallEvent(object):
    interface.implements(IAfterExceptionCallEvent)

    def __init__(self, object, request):
        self.object = object
        self.request = request


class IModificationInfo(interface.Interface):

    def modified():
        """modification date (long)"""


class ISiteUID(interface.Interface):

    uid = schema.TextLine(
        title = u'UID',
        readonly = True)

    def generate():
        """ regenate uid """


class ICacheStrategy(interface.Interface):
    """ cache strategy """

    def __bind__(request):
        """ bind strategry for specific request """

    def isModified():
        """ check view modification """

    def setCacheHeaders():
        """ add cache headers to response """

    def setNotModifiedHeaders():
        """ add cache headers for not modified content """


class IStaticCacheStrategy(ICacheStrategy):
    """ caching for static resources,
    based on Last-Modified header """


class IETagCacheStrategy(ICacheStrategy):
    """ caching based on ETag """

    etag = schema.TextLine(
        title = u'ETag',
        description = u'ETag for context.',
        required = True)

    def buildETag():
        """ build etag for current context """
