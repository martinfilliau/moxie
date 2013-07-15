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
          "park_and_rides": [
            {
              "capacity": 1389,
              "identifier": "osm:2809915",
              "name": "Redbridge Park & Ride OX1 4XG",
              "percentage": 0,
              "spaces": 0,
              "unavailable": true   // real-time information not available
            },
            [...]
            {
              "capacity": 758,
              "identifier": "osm:4329908",
              "name": "Water Eaton Park & Ride OX2 8HA",
              "percentage": 48,
              "spaces": 390,
              "unavailable": false
            }
          ]
        }

    :statuscode 200: resource found
    :statuscode 503: Service not available
