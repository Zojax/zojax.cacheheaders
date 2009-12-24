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
import md5
import time
import persistent
from zope import interface
from zope.cachedescriptors.property import Lazy

from interfaces import ISiteUID


class SiteUID(object):
    interface.implements(ISiteUID)

    @Lazy
    def uid(self):
        return self.generate()

    def generate(self):
        self.uid = md5.md5(time.ctime()).hexdigest()


class PersistentSiteUID(persistent.Persistent, SiteUID):
    """ persistent site uid """
