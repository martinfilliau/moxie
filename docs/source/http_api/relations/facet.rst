facet
=====

Return an overview of your search results for a given field by listing the
possible values this field may take and the number of results with each value.

For example: ``/places/search?q=union&facet=type_exact``. Produces facets something like this::

    "facet:type_exact": [
      {
        "count": 9, 
        "href": "/places/search?q=union&facet=type_exact&type_exact=%2Funiversity%2Fsub-library", 
        "name": "/university/sub-library", 
        "title": "Sub-library", 
        "value": "/university/sub-library"
      }, 
      {
        "count": 1, 
        "href": "/places/search?q=union&facet=type_exact&type_exact=%2Funiversity%2Fsite", 
        "name": "/university/site", 
        "title": "Site", 
        "value": "/university/site"
      }, 
      {
        "count": 1, 
        "href": "/places/search?q=union&facet=type_exact&type_exact=%2Funiversity%2Flibrary", 
        "name": "/university/library", 
        "title": "Library", 
        "value": "/university/library"
      }, 
      {
        "count": 1, 
        "href": "/places/search?q=union&facet=type_exact&type_exact=%2Funiversity%2Fdepartment", 
        "name": "/university/department", 
        "title": "Department", 
        "value": "/university/department"
      }
    ],
