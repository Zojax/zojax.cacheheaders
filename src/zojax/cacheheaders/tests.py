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
"""test setup

$Id$
"""
__docformat__ = "reStructuredText"

import doctest, unittest
from zope import component
from zope.traversing import testing
from zope.app.testing import placelesssetup
from zope.traversing.interfaces import ITraversable
from zope.app.security import principalregistry
from zope.security.management import endInteraction
from zope.app.security.interfaces import IAuthentication
from zope.app.security.interfaces import IFallbackUnauthenticatedPrincipal

def setUp(test):
    placelesssetup.setUp()
    testing.setUp()

    endInteraction()

    principal = principalregistry.UnauthenticatedPrincipal('anon','anon','')
    component.provideUtility(
        principal, IFallbackUnauthenticatedPrincipal)
    component.provideUtility(
        principalregistry.principalRegistry, IAuthentication)

def tearDown(test):
    placelesssetup.tearDown()

def test_suite():
    return unittest.TestSuite((
            doctest.DocFileSuite(
                'README.txt',
                setUp=setUp, tearDown=tearDown,
                optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
         ))
