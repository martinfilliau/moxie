API specification
=================

Formats
-------

The API returns only JSON at the moment.

HAL links
---------

Responses have a `_links` attribute containing links to help in the navigation (e.g. when results need pagination).

Each individual entity has a `self` attribute in `links` that represents the path to itself.

It is highly recommended for clients to use these links to navigate between resources.

CORS
----

We use CORS (Cross-origin resource sharing). JSONP is not available (causes problem e.g. no custom header).
