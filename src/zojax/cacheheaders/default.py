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
from zope.security.proxy import removeSecurityProxy
from zope.dublincore.interfaces import ICMFDublinCore

from interfaces import IModificationInfo


class ModificationInfo(object):
    interface.implements(IModificationInfo)

    def __init__(self, context):
        dc = ICMFDublinCore(context, None)
        if dc is not None:
            self.time = long(time.mktime(dc.modified.utctimetuple()))
        else:
            context = removeSecurityProxy(context)
            mtime = getattr(context, '_p_mtime', 0)
            self.time = long(mtime)

    def modified(self, default=long(0)):
        return self.time


@interface.implementer(IModificationInfo)
def viewModificationInfo(view):
    return IModificationInfo(view.context)
