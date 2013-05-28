ServiceView
===========

Provides set of resources which can be accessed by defined routes. Currently most of our views represent data as json over HTTP.

Handles CORS, content-negotiation and geo-location awareness. Calls :doc:`services` to access data.

Caching headers
---------------

You can control the value of the HTTP headers `Expires` and `Cache-Control`
by setting the property `expires` of your view to either a `timedelta` or a `datetime`.

.. code-block:: python

    from datetime import timedelta, datetime
    from moxie.core.views import ServiceView

    class NearRealTimeInformation(ServiceView):

        expires = timedelta(seconds=5)
        # expires = datetime.utcnow().replace(hour=23, minute=59)

        def handle_request(self):
            return {'real': 'time'}
