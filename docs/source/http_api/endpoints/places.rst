Places endpoint
===============

Endpoint to search and retrieve information about places.

.. http:get:: /places/(string:id)[,(string:id)...]

    Get details of one or multiple places by their ID

    **Example request**:

    .. sourcecode:: http

		GET /places/osm:3646652 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example request for multiple POIs**:

    .. sourcecode:: http

		GET /places/osm:3646652,oxpoints:23232392 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json

		{
			"id": "osm:3646652",
			"name": "Tesco Metro",
			"type": "Supermarket",
			"lat": 0.232,
			"lng": 51.456,
			"address": "example"
		}

    :param id: ID of the resource, if multiple resources, separated by a comma
    :type id: string

    :statuscode 200: resource found
    :statuscode 301: redirection to the resource by its main ID
    :statuscode 404: no resource found
    :statuscode 503: Service not available

    If multiple resources are requested, as much documents as possible will be returned (i.e. if one of
    the identifier requested is not found, all other documents will be returned).

.. http:get:: /places/search

    Search for places using full-text search on name, tags and type of place.
    Also searches in identifiers (e.g. searching "69326473" will return the bus stop corresponding to this Naptan ID).
    Results can be filtered by a type and its subtypes or can be filtered by specific types (both options cannot be used at the same time).
    Note that the result might be using a different search as spellchecking is done (e.g. searching for "Wolverkote" will return results with "Wolvercote").

    **Example request**:

    .. sourcecode:: http

		GET /places/search?q=aldates&type=/transport HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json
		Geo-Position: 0.232, 51.347

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json
		{
			"query": "aldates",
			"results": [
            {
              "website": "",
              "phone": "",
              "address": "",
              "lat": "51.7508834555",
              "id": "stoparea:340G00003140",
              "distance": 0.28500558122592606,
              "name": "St Aldates",
              "opening_hours": "",
              "type_name": [
                "Bus stop area"
              ],
              "lon": "-1.2571120376",
              "collection_times": "",
              "type": [
                "/transport/stop-area"
              ]
            },
            [...]
			]
		}

    :query q: what to search for
    :type q: string
    :query type: filter by a specific type in the hierarchy of types (will search within subtypes too)
    :type type: string
    :query type_exact: filter by exact types (as opposite to the type parameter), you can have this parameter multiple times.
    :type type_exact: string
    :query start: first result to retrieve
    :type start: int
    :query count: number of results to retrieve
    :type count: int
    :query lat: latitude (as an alternative to the Geo-Position header if spatial search required)
    :type lat: string
    :query lon: longitude (as an alternative to the Geo-Position header if spatial search required)
    :type lon: string

    If no geolocation is passed (either by header or query parameters), and if there is no full-text search (``q`` parameter),
    the result will be sorted by name (A-Z).

    :statuscode 200: query found
    :statuscode 400: Bad request (could happen if some parameters are used in combination e.g. type and type_exact)
    :statuscode 503: Service not available

.. http:get:: /places/types

    Display a list of types.

    :statuscode 200: display a list of types
