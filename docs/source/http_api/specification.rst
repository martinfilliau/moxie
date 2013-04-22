API specification
=================

Formats
-------

The API returns HAL+JSON at the moment (see the `HAL specification <http://tools.ietf.org/html/draft-kelly-json-hal-05>`_).

HAL+JSON
--------

Responses have a `_links` attribute containing links to help in the navigation (e.g. when results need pagination).

Each individual entity has a `self` attribute in `_links` that represents the path to itself.

It is highly recommended for clients to use these links (:doc:`/http_api/relations/overview`) to navigate between resources.

CORS
----

We use CORS (Cross-origin resource sharing). JSONP is not available (causes problem e.g. no custom header).

Pagination
----------

Standard parameters are available for pagination: start and count.
It is advised to use :doc:`/http_api/relations/overview` (:doc:`/http_api/relations/first`, :doc:`/http_api/relations/last`,
:doc:`/http_api/relations/prev` and :doc:`/http_api/relations/next`) to browse results.
