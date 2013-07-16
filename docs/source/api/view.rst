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

Exceptions
----------

You should raise exceptions in case of an error in your application.

Moxie provides `ServiceUnavailable`, `BadRequest` and `NotFound` in `moxie.core.exceptions`,
to respectfully provide 503, 400 and 404 responses.

The generic `ApplicationException` is also available, `message` and `status_code` parameters
can be passed to have a more personalised exception.

.. code-block:: python

    from moxie.core.exceptions import NotFound, ApplicationException

    class DetailView(ServiceView):

        def handle_request(self, uuid):
            # pseudo logic: book = service.get(uuid)
            if not book:
                raise NotFound()    # HTTP 404

            # pseudo logic:
            # user = view.get_user()
            # authorized = service.view_book(user, book)
            if not authorized:
                raise ApplicationException(message="You are not authorized to see this book",
                                            status_code=401)
