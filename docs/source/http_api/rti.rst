Real-time Information
=====================

Moxie supports an API for providing RTI from Service providers. Currently all RTI is represented in a similar way:

.. code-block:: javascript
   {mesages: [],
    services: [],
    type: '',
    title: ''}

The ``type`` attribute should be a unique identifier for that RTI representation and the ``title`` attribute should be a human readable title for the information. Here are examples of RTI representations.

rail-arrivals
-------------
Rail live arrivals board information, for example:

.. code-block:: javascript

    {
      "messages": [], 
      "services": [
        {
          "destination": {
            "location": [
              {
                "crs": "PAD", 
                "futureChangeTo": null, 
                "locationName": "London Paddington", 
                "via": null
              }
            ]
          }, 
          "eta": "11:54", 
          "operator": "First Great Western", 
          "operatorCode": "GW", 
          "origin": {
            "location": [
              {
                "crs": "GMV", 
                "futureChangeTo": null, 
                "locationName": "Great Malvern", 
                "via": null
              }
            ]
          }, 
          "platform": "1", 
          "serviceID": "kgCLsr4sZvhigTZPO8doPQ==", 
          "sta": "11:28"
        }, 
            ]
          }, 
          "serviceID": "bMcFsZG5AMloV3FVpYkZpA==", 
          "sta": "13:02"
        }
      ], 
      "type": "rail-arrivals",
      "title": "Arrivals"
    }

rail-departures
---------------
Rail live departures board information, for example:

.. code-block:: javascript

    {
      "messages": [], 
      "services": [
        {
          "destination": {
            "location": [
              {
                "crs": "PAD", 
                "futureChangeTo": null, 
                "locationName": "London Paddington", 
                "via": null
              }
            ]
          }, 
          "etd": "11:55", 
          "operator": "First Great Western", 
          "operatorCode": "GW", 
          "origin": {
            "location": [
              {
                "crs": "GMV", 
                "futureChangeTo": null, 
                "locationName": "Great Malvern", 
                "via": null
              }
            ]
          }, 
          "platform": "1", 
          "serviceID": "kgCLsr4sZvhigTZPO8doPQ==", 
          "std": "11:31"
        }
      ], 
      "type": "rail-departures",
      "title": "Departures"
    }

bus
---
Bus stop current real time information, for example:

.. code-block:: javascript

    {
      "messages": [
        "traffic incidents in Oxford some delays to X39/X40 possible<div class=\"stopLine\">-traffic incidents in Oxford some delays to X39/X40 possible<br/></div>"
      ], 
      "services": [
        {
          "destination": "Didcot & Harwell", 
          "following": [], 
          "next": "10 mins", 
          "service": "X32"
        }, 
        {
          "destination": "Gloucester Green", 
          "following": [
            "30 mins", 
            "55 mins", 
            "65 mins", 
          ], 
          "next": "15 mins", 
          "service": "X90"
        }, 
        {
          "destination": "City Centre", 
          "following": [
            "27 mins", 
            "41 mins", 
            "67 mins", 
            "72 mins", 
            "82 mins", 
            "91 mins", 
          ], 
          "next": "19 mins", 
          "service": "TUBE"
        }, 
        {
          "destination": "Oxford City Centre", 
          "following": [
            "69 mins", 
            "126 mins", 
            "156 mins", 
          ], 
          "next": "30 mins", 
          "service": "OXF"
        }, 
        {
          "destination": "Reading", 
          "following": [], 
          "next": "30 mins", 
          "service": "X39"
        }, 
        {
          "destination": "Reading via W'dcote", 
          "following": [], 
          "next": "60 mins", 
          "service": "X40"
        }
      ], 
      "type": "bus",
      "title": "Live bus timetable information"
    }
