Transport endpoint
==================

Endpoint to retrieve information about transport.

.. http:get:: /transport/park-and-rides

    Get real-time information about status of park and rides

    **Example request**:

    .. sourcecode:: http

		GET /transport/park-and-rides HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "osm:24719725": {
            "capacity": 855,
            "name": "Thornhill Park & Ride OX3 8DP",
            "percentage": 100,
            "spaces": 0,
            "unavailable": true
          },
          "osm:2809915": {
            "capacity": 1389,
            "name": "Redbridge Park & Ride OX1 4XG",
            "percentage": 45,
            "spaces": 754,
            "unavailable": false
          },
          [...]

    :statuscode 200: resource found
    :statuscode 503: Service not available
