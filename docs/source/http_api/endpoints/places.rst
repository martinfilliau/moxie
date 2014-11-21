Places endpoint
===============

Endpoint to search and retrieve information about places.

All the responses are conform to the `HAL specification <http://stateless.co/hal_specification.html>`_.

.. http:get:: /places/(string:id)[,(string:id)...]

    Get details of one or multiple places by their ID

    **Example request**:

    .. sourcecode:: http

		GET /places/oxpoints:23232339 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example request for multiple POIs**:

    The response representation for multiple POIs will be equivalent to the
    search method.

    .. sourcecode:: http

		GET /places/osm:3646652,oxpoints:23232392 HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "_embedded": {
            "files": [
              {
                "location": "oxpoints/54559254/depiction/original/primary.jpg",
                "primary": true,
                "type": "depiction",
                "url": "//mox-static-files.oucs.ox.ac.uk/oxpoints/54559254/depiction/original/primary.jpg"
              },
            ]
          },
          "_links": {
            "child": [
              {
                "href": "/places/oxpoints:32320005",
                "title": "Balliol College Library",
                "type": [
                  "/university/library"
                ],
                "type_name": [
                  "Library"
                ]
              }
            ],
            "primary_place": {
              "href": "/places/oxpoints:23232339",
              "title": "Balliol College",
              "type": [
                "/university/college"
              ],
              "type_name": [
                "College"
              ]
            },
            "self": {
              "href": "/places/oxpoints:23232339"
            }
          },
          "address": "Broad Street OX1 3BJ",
          "distance": 0,
          "id": "oxpoints:23232339",
          "identifiers": [
            "oxpoints:54559254",
            "oxpoints:23232339",
            "obn:851",
            "osm:187925177",
            "oucs:ball",
            "finance:RB"
          ],
          "lat": "51.754425",
          "lon": "-1.257216",
          "name": "Balliol College",
          "name_sort": "Balliol College",
          "shape": "POLYGON ((... 51.755528699999999 0,-1.2584285 51.755520099999998 0))",
          "social_facebook": [
            "https://www.facebook.com/balliolcollege"
          ],
          "social_twitter": [
            "https://www.twitter.com/BalliolOxford"
          ],
          "type": [
            "/university/college"
          ],
          "type_name": [
            "College"
          ],
          "website": "http://www.balliol.ox.ac.uk/"
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
          "_embedded": {
            "pois": [
              {
                "_links": {
                  "child": [
                    {
                      "href": "/places/atco:340000004H5",
                      "title": "Stop H5 St Aldates",
                      "type": [
                        "/transport/bus-stop"
                      ],
                      "type_name": [
                        "Bus stop"
                      ]
                    },
                  ],
                  "parent": {
                    "href": "/places/stoparea:340G00004000",
                    "title": "Oxford City Centre",
                    "type": [
                      "/transport/stop-area"
                    ],
                    "type_name": [
                      "Bus stop area"
                    ]
                  },
                  "self": {
                    "href": "/places/stoparea:340G00003140"
                  }
                },
                "distance": 0,
                "id": "stoparea:340G00003140",
                "identifiers": [
                  "stoparea:340G00003140"
                ],
                "lat": "51.7508834555",
                "lon": "-1.2571120376",
                "name": "St Aldates",
                "name_sort": "St Aldates",
                "type": [
                  "/transport/stop-area"
                ],
                "type_name": [
                  "Bus stop area"
                ]
              },
              {
                "_links": {
                  "curie": {
                    "href": "http://moxie.readthedocs.org/en/latest/http_api/rti.html#{type}",
                    "name": "rti",
                    "templated": true
                  },
                  "parent": {
                    "href": "/places/stoparea:340G00003140",
                    "title": "St Aldates",
                    "type": [
                      "/transport/stop-area"
                    ],
                    "type_name": [
                      "Bus stop area"
                    ]
                  },
                  "rti:bus": {
                    "href": "/places/atco:340000004H5/rti/bus",
                    "title": "Live bus departure times"
                  },
                  "self": {
                    "href": "/places/atco:340000004H5"
                  }
                },
                "distance": 0,
                "id": "atco:340000004H5",
                "identifiers": [
                  "atco:340000004H5",
                  "naptan:69326543"
                ],
                "lat": "51.7502787977",
                "lon": "-1.2567597994",
                "name": "Stop H5 St Aldates",
                "name_sort": "Stop H5 St Aldates",
                "type": [
                  "/transport/bus-stop"
                ],
                "type_name": [
                  "Bus stop"
                ]
              },
            ]
          },
          "_links": {
            "curies": [
              {
                "href": "http://moxie.readthedocs.org/en/latest/http_api/relations/{rel}.html",
                "name": "hl",
                "templated": true
              },
              {
                "href": "http://moxie.readthedocs.org/en/latest/http_api/relations/facet.html",
                "name": "facet"
              }
            ],
            "hl:first": {
              "href": "/places/search?q=aldates&facet=type&type=%2Ftransport&count=35"
            },
            "hl:last": {
              "href": "/places/search?q=aldates&facet=type&type=%2Ftransport&count=35"
            },
            "hl:types": [
              {
                "count": 10,
                "href": "/places/search?q=aldates&facet=type&type=%2Ftransport%2Fbus-stop",
                "name": "/transport/bus-stop",
                "title": [
                  "Bus stop"
                ],
                "value": "/transport/bus-stop"
              },
              {
                "count": 1,
                "href": "/places/search?q=aldates&facet=type&type=%2Ftransport%2Fstop-area",
                "name": "/transport/stop-area",
                "title": [
                  "Bus stop area"
                ],
                "value": "/transport/stop-area"
              }
            ],
            "self": {
              "href": "/places/search?q=aldates&facet=type&type=%2Ftransport&count=35&start=0"
            }
          },
          "query": "aldates",
          "size": 11
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
    :query inoxford: only get results within Oxford (value will be ignored)
    :type inoxford: string
    :query university_only: only get results from the University (value will be ignored)
    :type university_only: string
    :query exclude_university: exclude results from the University (value will be ignored) i.e. only amenities, transport...
    :type exclude_university: string

    **Accessibility filtering**

    Below are filters specific to accessibility features, coming from the university' access guide.

    :query accessibility_has_adapted_furniture: only get POIs known to have "adapted furniture"
    :type accessibility_has_adapted_furniture: boolean
    :query accessibility_has_cafe_refreshments: only get POIs known to have "accessible cafe / refreshments"
    :type accessibility_has_cafe_refreshments: boolean
    :query accessibility_has_computer_access: only get POIs known to have "accessible computer access"
    :type accessibility_has_computer_access: boolean
    :query accessibility_has_hearing_system: only get POIs known to have a "hearing system"
    :type accessibility_has_hearing_system: boolean
    :query accessibility_has_lifts_to_all_floors: only get POIs known to have "lift access to all floors"
    :type accessibility_has_lifts_to_all_floors: boolean
    :query accessibility_has_quiet_space: only get POIs known to have "accessible quiet space"
    :type accessibility_has_quiet_space: boolean
    :query accessibility_has_accessible_toilets: only get POIs known to have "accessible toilets"
    :type accessibility_has_accessible_toilets: boolean
    :query accessibility_has_accessible_parking_spaces: only get POIs known to have "accessible parking spaces"
    :type accessibility_has_accessible_parking_spaces: boolean

    **Application specific filtering**

    Below are filters made specifically for an application. It is not recommended to use these parameters, as it
    is mainly experimental and might change to be generic in the future.

    :query is_display_in_maps_department_list: only get POIs manually selected / curated as "featured" university departments
    :type is_display_in_maps_department_list: boolean

    If no geolocation is passed (either by header or query parameters), and if there is no full-text search (``q`` parameter),
    the result will be sorted by name (A-Z).

    :statuscode 200: query found
    :statuscode 400: Bad request (could happen if some parameters are used in combination e.g. type and type_exact)
    :statuscode 503: Service not available

.. http:get:: /places/types

    Display a list of types.

    :statuscode 200: display a list of types

.. http:get:: /places/suggest

    Suggest places based on name and alternative names.
    Results can be filtered by specific types.

    **Example request**:

    .. sourcecode:: http

		GET /places/suggest?q=sec&type_exact=/university/department HTTP/1.1
		Host: api.m.ox.ac.uk
		Accept: application/json

    **Example response**:

    The response only contains a subset of properties available in the search method to reduce the
    length of the response.

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "_embedded": {
            "pois": [
              {
                "_links": {
                  "self": {
                    "href": "/places/oxpoints:23233517"
                  }
                },
                "address": "Wellington Square OX1 2JD",
                "distance": 0,
                "id": "oxpoints:23233517",
                "identifiers": [],
                "name": "Council Secretariat",
                "type": [
                  "/university/department"
                ],
                "type_name": [
                  "Department"
                ]
              },
              {
                "_links": {
                  "self": {
                    "href": "/places/oxpoints:59801811"
                  }
                },
                "address": "Parks Road OX1 3QD",
                "distance": 0,
                "id": "oxpoints:59801811",
                "identifiers": [],
                "name": "Cyber Security Centre",
                "type": [
                  "/university/department"
                ],
                "type_name": [
                  "Department"
                ]
              },
              {
                "_links": {
                  "self": {
                    "href": "/places/oxpoints:58455192"
                  }
                },
                "address": "off South Parks Road OX1 3RQ",
                "distance": 0,
                "id": "oxpoints:58455192",
                "identifiers": [],
                "name": "Oxford University Security Services",
                "type": [
                  "/university/department"
                ],
                "type_name": [
                  "Department"
                ]
              },
            ]
          },
          "_links": {
            "curies": [
              {
                "href": "http://moxie.readthedocs.org/en/latest/http_api/relations/{rel}.html",
                "name": "hl",
                "templated": true
              }
            ],
            "hl:first": {
              "href": "/places/suggest?q=sec&count=20"
            },
            "hl:last": {
              "href": "/places/suggest?q=sec&count=20"
            },
            "self": {
              "href": "/places/suggest?q=sec&count=20&start=0"
            }
          },
          "query": "sec",
          "size": 13
        }

    :query q: what to search for
    :type q: string
    :query type_exact: filter by exact types (as opposite to the type parameter), you can have this parameter multiple times.
    :type type_exact: string
    :query start: first result to retrieve
    :type start: int
    :query count: number of results to retrieve
    :type count: int

    :statuscode 200: query found
    :statuscode 400: Bad request (e.g. missing parameters)
    :statuscode 503: Service not available
