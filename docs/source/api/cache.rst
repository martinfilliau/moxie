Cache
=====

Moxie provides cache using `Flask-Cache <https://github.com/thadeusb/flask-cache>`_.

Configuration
-------------

See `Flask-Cache documentation <https://github.com/thadeusb/flask-cache/blob/master/docs/index.rst#configuring-flask-cache>`_.

Caching the result of a function
--------------------------------

To use it on a view, you have to decorate your method with `@cache.cached`
(imported from `moxie.core.cache`) and specify a `timeout` (in seconds).

.. code-block:: python

    from moxie.core.views import ServiceView
    from moxie.core.cache import cache

    class NearRealTimeInformation(ServiceView):

        @cache.cached(timeout=10)
        def handle_request(self):
            return {'near': 'real-time'}

.. warning::

    This acts on the path of the request only, **not** the arguments of the request. See below for more information on
    that topic.

Cache key that includes arguments as well
-----------------------------------------

You can customize the cache key used depending on your requirements by passing
the keyword argument `key_prefix` to `@cache.cached`.

We provide an helper to create the key from the path of the request **and** the arguments,
you can use it by importing `args_cache_key` from `moxie.core.cache`. See example below.

.. code-block:: python

    from flask import request

    from moxie.core.views import ServiceView
    from moxie.core.cache import cache, args_cache_key

    class LookupView(ServiceView):

        @cache.cached(timeout=60, key_prefix=args_cache_key)
        def handle_request(self):
            identifier = request.args.get('identifier', None)
            return {'lookup': identifier}