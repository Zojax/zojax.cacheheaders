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
import time
from zope import interface
from zope.component import getUtility
from zope.datetime import time as timeFromDateTimeString

from interfaces import ISiteUID
from interfaces import IModificationInfo
from interfaces import IETagCacheStrategy


class ETagBased(object):
    interface.implements(IETagCacheStrategy)

    def __init__(self, context):
        self.context = context

    def __bind__(self, request):
        self.request = request
        self.response = request.response
        self.buildETag()
        return self

    def buildETag(self):
        raise NotImplemented

    def isModified(self):
        request = self.request
        header = request.getHeader('HTTP_IF_NONE_MATCH', None, True)
        if header is not None:
            if self.etag == header:
                return False

        return True

    def setNotModifiedHeaders(self):
        response = self.response

        secs = 86400
        response.setHeader('Cache-Control', 'public,max-age=%s' % secs)
        response.setHeader('ETag', self.etag)

    def setCacheHeaders(self):
        response = self.response

        secs = 86400
        response.setHeader('Cache-Control', 'public,max-age=%s' % secs)
        t = time.time() + secs
        response.setHeader('Expires',
                           time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                         time.gmtime(t)))
        response.setHeader('ETag', self.etag)


class ETagWithSiteUID(ETagBased):

    def buildETag(self):
        """ etag format: {Last modified}|{site uid}"""
        context = self.context
        siteuid = getUtility(ISiteUID)

        modinfo = IModificationInfo(context, None)
        if modinfo is not None:
            self.etag = 'W/"%d|%s"'%(modinfo.modified(), siteuid.uid)
        else:
            self.etag = 'W/"%s|%s"'%(context.__name__, siteuid.uid)


class ETagForPrincipal(ETagBased):

    def buildETag(self):
        """ etag format: {Last modified}|{site uid}"""
        context = self.context
        siteuid = getUtility(ISiteUID)

        pid = self.request.principal.id

        modinfo = IModificationInfo(context, None)
        if modinfo is not None:
            self.etag = 'W/"%s|%d|%s"'%(pid, modinfo.modified(), siteuid.uid)
        else:
            self.etag = 'W/"%s|%s|%s"'%(pid, context.__name__, siteuid.uid)

    def setNotModifiedHeaders(self):
        response = self.response

        response.setHeader('ETag', self.etag)
        response.setHeader('Cache-Control', 'public,must-revalidate')
        response.setHeader('Vary', 'Accept-Encoding, Accept-Language')

    def setCacheHeaders(self):
        response = self.response

        response.setHeader('ETag', self.etag)
        response.setHeader('Cache-Control', 'public,must-revalidate')
        response.setHeader('Vary', 'Accept-Encoding, Accept-Language')
