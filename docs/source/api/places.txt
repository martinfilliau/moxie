Places endpoint
===============

Endpoint to search and retrieve information about places.

.. http:get:: /places/(string:id)

    Get details of a place by its ID

    **Example request**:

    .. sourcecode:: http

		GET /places/osm:3646652 HTTP/1.1
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

    :param id: ID of the resource
    :type id: string

    :statuscode 200: resource found
    :statuscode 301: redirection to the resource by its main ID
    :statuscode 404: no resource found

.. http:get:: /places/search

    Search for places using full-text search on name, tags and type of place.
    Note that the result might be using a different search as spellchecking is done (e.g. searching for "Wolverkote" will return results with "Wolvercote").

    **Example request**:

    .. sourcecode:: http

		GET /places/search?q=pharmacy HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json
		Geo-Position: 0.232, 51.347

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json
		{
			"query": "pharmacy",
			"results": [
			{
				"id": "osm:18383",
				"name": "Bliep",
				"type": "Pharmacy",
			},
			]
		}

    :query q: what to search for
    :type q: string

    :statuscode 200: query found
