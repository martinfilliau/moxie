Library endpoint
================

Endpoint to search and retrieve information about media in libraries.

.. http:get:: /library/item:(string:id)

    Get details of a media by its ID

    **Example request**:

    .. sourcecode:: http

		GET /library/item:015044225 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json

        {
          "publisher": "[Paris] : Minist\u00e8re de la Reconstruction et de l'Urbanisme, 1951.",
          "description": "2 maps.",
          "author": null,
          "holdings": {
            "BODBL": {
              "holdings": [
                {
                  "materials_specified": null,
                  "shelfmark": "C21:50 Arreau (1)"
                }
              ]
            }
          },
          "control_number": "015044225",
          "copies": 1,
          "edition": null,
          "isbns": [],
          "title": "Arreau. [map]",
          "issns": []
        }

    :param id: ID of the resource
    :type id: string

    :statuscode 200: resource found
    :statuscode 404: no resource found

.. http:get:: /library/search

    Search for media by title and/or author or ISBN.

    **Example request**:

    .. sourcecode:: http

		GET /library/search?title=python HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

		HTTP/1.1 200 OK
		Content-Type: application/json

        {
          "results": [
            {
              "description": "x, 210 p : ill ; 24 cm",
              "links": {
                "self": "/library/item:010544419"
              },
              "edition": null,
              "publisher": "Jefferson, N.C ; London : McFarland, c1991",
              "author": "McCall, Douglas L., 1971-",
              "holdings": {
                "BODBL": {
                  "holdings": [
                    {
                      "materials_specified": null,
                      "shelfmark": "M92.E13408"
                    }
                  ],
                  "poi": {
                    "website": "http://www.bodleian.ox.ac.uk/bodley",
                    "name": "Bodleian Library",
                    "links": {
                      "self": "/places/oxpoints:32320008"
                    },
                    "lon": "-1.254023",
                    "address": "",
                    "lat": "51.754105",
                    "type": [
                      "Library"
                    ],
                    "id": "oxpoints:32320008"
                  }
                }
              },
              "control_number": "010544419",
              "copies": 1,
              "isbns": [
                "0899505597"
              ],
              "title": "Monty Python : a chronological listing of the troupe's creative output, and articles and reviews about them, 1969-1989 / by Douglas L. McCall",
              "issns": []
            },
            {
              "description": "xvi, 269 p : ill ; 28 cm",
              "links": {
                "self": "/library/item:010558467"
              },
              "edition": null,
              "publisher": "London : Plexus, 1990",
              "author": "Johnson, Kim, 1955-",
              "holdings": {
                "BODBL": {
                  "holdings": [
                    {
                      "materials_specified": null,
                      "shelfmark": "M93.C01206"
                    }
                  ],
                  "poi": {
                    "website": "http://www.bodleian.ox.ac.uk/bodley",
                    "name": "Bodleian Library",
                    "links": {
                      "self": "/places/oxpoints:32320008"
                    },
                    "lon": "-1.254023",
                    "address": "",
                    "lat": "51.754105",
                    "type": [
                      "Library"
                    ],
                    "id": "oxpoints:32320008"
                  }
                }
              },
              "control_number": "010558467",
              "copies": 1,
              "isbns": [
                "085965107X"
              ],
              "title": "The first 200 years of Monty Python / Kim \"Howard\" Johnson",
              "issns": []
            }
          ],
          "links": {
            "first": "/library/search?count=10&title=python",
            "last": "/library/search?count=10&start=176&title=python",
            "next": "/library/search?count=10&start=10&title=python"
          },
          "size": 186
        }

    The response contains a list of results, links to go to first, previous, next and last pages depending on current `start` and `count` parameters, and the total count of results.

    :query title: title to search for
    :type title: string
    :query author: author to search for
    :type author: string
    :query isbn: isbn to search for
    :type isbn: isbn
    :query start: first result to display
    :type start: int
    :query count: number of results to display
    :type count: int

    :statuscode 200: results found
