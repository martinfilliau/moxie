import logging

from itertools import izip

from moxie.core.service import Service
from moxie.core.search import searcher
from moxie.places.importers.helpers import get_types_dict
from moxie.places.solr import doc_to_poi


logger = logging.getLogger(__name__)


class POIService(Service):
    default_search = '*:*'

    def __init__(self, nearby_excludes=None):
        """POI service
        :param nearby_excludes: list of types to exclude in a nearby search
        """
        self.nearby_excludes = nearby_excludes or []

    def get_results(self, original_query, location, start, count, type=None,
            all_types=False):
        """Search POIs
        :param original_query: fts query
        :param location: latitude,longitude
        :param start: index of the first result of the page
        :param count: number of results for the page
        :param type: (optional) type from the hierarchy of types to look for
        :param all_types: (optional) display all types or excludes some types defined in configuration
        :return list of domain objects (POIs), total size of results and facets on type
        """
        query = original_query or self.default_search
        lat, lon = location
        q = {'defType': 'edismax',
             'spellcheck.collate': 'true',
             'pf': query,
             'q': query,
             'sfield': 'location',
             'pt': '%s,%s' % (lon, lat),
             'boost': 'recip(geodist(),2,200,20)',  # boost by geodist (linear function: 200/2*x+20)
             'sort': 'score desc',                  # sort by score
             'fl': '*,_dist_:geodist()',
             'facet': 'true',
             'facet.field': 'type',
             'facet.sort': 'index',
             'facet.mincount': '1',
             }
        filter_query = None
        if type:
            # filter on one specific type
            q['facet.prefix'] = type
            filter_query = 'type_exact:{type}*'.format(type=type.replace('/', '\/'))
        elif not all_types and len(self.nearby_excludes) > 0:
            # exclude some types based on configuration
            filter_query = "-type_exact:({types})".format(types=' OR '.join('"{type}"'.format(type=t) for t in self.nearby_excludes))

        response = searcher.search(q, fq=filter_query, start=start, count=count)

        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.query_suggestion:
                suggestion = response.query_suggestion
                return self.get_results(suggestion, location, start, count,
                        type=type, all_types=all_types)
            else:
                return [], 0, None
        if response.facets:
            facets_values = response.facets['facet_fields']['type']
            i = iter(facets_values)
            facets = dict(izip(i, i))
        else:
            facets = None
        return [doc_to_poi(r) for r in response.results], response.size, facets

    def get_place_by_identifier(self, ident):
        """Get a place by its main identifier
        Search in all identifiers if not found.
        :param ident: identifier to lookup
        :return POI or None if no result
        """
        response = searcher.get_by_ids([ident])
        # First do a GET request by its ID
        if response.results:
            return doc_to_poi(response.results[0])
        else:
            # If no result, do a SEARCH request on IDs
            response = searcher.search_for_ids("identifiers", [ident])
            if response.results:
                return doc_to_poi(response.results[0])
            else:
                return None

    def search_place_by_identifier(self, ident):
        """Search for a place by its identifiers
        :param ident: identifier to lookup
        :retur POI or None if no result
        """
        response = searcher.search_for_ids("identifiers", [ident])
        if response.results:
            return doc_to_poi(response.results[0])
        else:
            return None

    def get_types(self):
        """Get types of POI
        :return dict of types
        """
        return get_types_dict()
