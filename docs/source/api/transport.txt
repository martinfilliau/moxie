Transport endpoint
==================

Endpoint to search and retrieve information about transport.

.. http:get:: /transport/bus/rti

    Get real-time information about services stopping by a bus-stop. 

    **Example request**:

	.. sourcecode:: http

		GET /transport/bus/rti?id=1983458 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json

		{
			"services": {},
			"messages": {}
		}

    :query id: Naptan ID of the bus stop
    :type id: int

    :statuscode 200: resource found
    :statuscode 404: no resource found
