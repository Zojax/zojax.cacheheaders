=======================
Browser caching headers
=======================

`Publication` with support `304` response code

  >>> import time, datetime, pytz
  >>> from zope import component, interface
  >>> from zojax.cacheheaders import interfaces

  >>> from zojax.cacheheaders.publication import \
  ...    BrowserFactory, BrowserPublication

  >>> factory = BrowserFactory()
  >>> factory.canHandle({})
  True

  >>> rclass, pclass = factory()
  >>> pclass == BrowserPublication
  True

  >>> pub = BrowserPublication(None)

  >>> from zope.publisher.browser import TestRequest
  >>> from zope.publisher.interfaces.http import IHTTPRequest

  >>> request = TestRequest()
  >>> response = request.response

  >>> request.setPublication(pub)

We need object

  >>> class IContent(interface.Interface):
  ...   pass

  >>> class Content(object):
  ...   interface.implements(IContent)
  ...   marker = 0
  ...
  ...   def __call__(self):
  ...      self.marker = 1
  ...      return 'Content body'

  >>> ob = Content()

  >>> print pub.callObject(request, ob)
  Content body


If we want control caching headers we need define ICacheStrategy adapter.
this package predefine some cache strategies. Simplest is StatusCache, it's 
base on object modification date (IModificationInfo interface)
So to use static cache fist we need IModificationInfo adapter

  >>> from zojax.cacheheaders.staticcache import getStaticCache
  >>> getStaticCache(ob) is None
  True
  
  >>> class ModInfo(object):
  ...   interface.implements(interfaces.IModificationInfo)
  ...   component.adapts(IContent)
  ...
  ...   dt = datetime.datetime(2007, 10, 10, 0, 0, 0, 0, tzinfo=pytz.utc)
  ...
  ...   def __init__(self, context):
  ...      self.context = context
  ...
  ...   def modified(self):
  ...      return long(time.mktime(self.dt.utctimetuple()))

  >>> component.provideAdapter(ModInfo)

  >>> strategy = getStaticCache(ob).__bind__(request)
  >>> interfaces.ICacheStrategy.providedBy(strategy)
  True

This strategy uses 'If-Modified-Since' request header.

  >>> request._environ['IF_MODIFIED_SINCE'] = 'Mon, 10 Dec 2007 00:00:00 GMT'
  >>> strategy.isModified()
  False

  >>> request._environ['IF_MODIFIED_SINCE'] = 'Mon, 10 Sep 2007 00:00:00 GMT'
  >>> strategy.isModified()
  True

If format is wrong isModified is always True

  >>> request._environ['IF_MODIFIED_SINCE'] = 'wrong format'
  >>> strategy.isModified()
  True

  >>> request._environ['IF_MODIFIED_SINCE'] = 'Mon, 10 Dec 2007 00:00:00 GMT'


Static Cache set 'Cache-Control', 'Expires', 'Last-Modified' headers for browser

  >>> strategy.setCacheHeaders()

  >>> response.getHeader('Cache-Control')
  'public,max-age=86400'

  >>> response.getHeader('Expires')
  '..., ... GMT'

  >>> response.getHeader('Last-Modified')
  'Wed, 10 Oct 2007 01:00:00 GMT'

It also should automaticly convert modified date to utc timezone

  >>> ModInfo.dt = datetime.datetime(2007, 10, 10, 0, 0, 0, 0)

  >>> strategy = getStaticCache(ob).__bind__(request)
  >>> strategy.setCacheHeaders()
  >>> response.getHeader('Last-Modified')
  'Wed, 10 Oct 2007 01:00:00 GMT'

  >>> ModInfo.dt = datetime.datetime(
  ...   2007, 10, 9, 18, 0, 0, 0, pytz.timezone('Asia/Almaty'))

  >>> strategy = getStaticCache(ob).__bind__(request)
  >>> strategy.setCacheHeaders()
  >>> response.getHeader('Last-Modified')
  'Wed, 10 Oct 2007 01:00:00 GMT'

  >>> ModInfo.dt = datetime.datetime(2007, 10, 10, 0, 0, 0, 0, tzinfo=pytz.utc)

To use this cache we have to register adater

  >>> component.provideAdapter(getStaticCache, (IContent,))

Now we can use this strategy in publication.
If content doesn't changed we should get just 304 response code

  >>> print pub.callObject(request, ob)
  <BLANKLINE>

  >>> response.getStatus()
  304

Or content

  >>> response.setStatus('200')
  >>> request._environ['IF_MODIFIED_SINCE'] = 'Mon, 10 Sep 2007 00:00:00 GMT'

  >>> print pub.callObject(request, ob)
  Content body

  >>> response.getStatus()
  200

  >>> response.getHeader('Last-Modified')
  'Wed, 10 Oct 2007 01:00:00 GMT'


Additional feature, calculating duration of call.

  >>> pub.beforeTraversal(request)
  >>> time.sleep(2)
  >>> pub.afterCall(request, ob)

  >>> response.getHeader('X-Generated-Time')
  '... sec'
