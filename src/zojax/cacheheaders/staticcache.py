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
""" static cache

$Id$
"""
import time
from pytz import utc
from datetime import datetime

from zope import interface
from zope.datetime import rfc1123_date, parseDatetimetz
from zope.datetime import time as timeFromDateTimeString
from zope.datetime import weekday_abbr, monthname

from interfaces import IModificationInfo
from interfaces import IStaticCacheStrategy


@interface.implementer(IStaticCacheStrategy)
def getStaticCache(context):
    info = IModificationInfo(context, None)
    if info is not None:
        return StaticCache(context, info)
    else:
        return None


class StaticCache(object):
    interface.implements(IStaticCacheStrategy)

    maxage = 86400

    def __init__(self, context, info):
        self.context = context
        self.info = info
        self.modified = info.modified()

    def __bind__(self, request):
        self.request = request
        self.response = request.response
        return self

    def isModified(self):
        if self.modified == 0:
            return True

        request = self.request
        header = request.getHeader('IF_MODIFIED_SINCE', None, True)

        if header is not None:
            header = header.split(';')[0]
            try:    mod_since=long(timeFromDateTimeString(header))
            except: mod_since=None

            if mod_since is not None:
                lmt = self.info.modified()
                if lmt > 0 and lmt <= mod_since:
                    return False

        return True

    def setNotModifiedHeaders(self):
        pass

    def setCacheHeaders(self):
        modified = self.modified
        if modified == 0:
            return

        response = self.response

        response.setHeader('Cache-Control', 'public,max-age=%s' % self.maxage)

        t = time.time() + self.maxage

        response.setHeader(
            'Expires', time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                     time.gmtime(t)))

        if not response.getHeader('Last-Modified', None):
            year, month, day, hh, mm, ss, wd, y, z = time.localtime(modified)

            lmod = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekday_abbr[wd],
                                                            day, monthname[month],
                                                            year, hh, mm, ss)
            response.setHeader('Last-Modified', lmod)
