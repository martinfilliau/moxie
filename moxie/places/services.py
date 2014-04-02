import logging
import urllib

from itertools import izip

from moxie.core.service import Service
from moxie.core.search import searcher
from moxie.places.importers.helpers import get_types_dict
from moxie.places.solr import doc_to_poi


logger = logging.getLogger(__name__)

TYPE_FACET = 'type'


class POIService(Service):
    default_search = '*:*'

    def __init__(self, prefix_keys="_"):
        """POI service
        :param prefix_keys: prefix used for keys not being in the schema of the search engine
        """
        self.prefix_keys = prefix_keys

    def get_results(self, original_query, location, start, count,
                    pois_type=None, types_exact=None, filter_queries=None,
                    facets=(TYPE_FACET,)):
        """Search POIs
        :param original_query: fts query
        :param location: latitude,longitude
        :param start: index of the first result of the page
        :param count: number of results for the page
        :param pois_type: (optional) type from the hierarchy of types to look for
        :param types_exact: (optional) exact types to search for (cannot be used in combination of type atm)
        :param facets: (optional) list of fields to be returned as facets defaults to the `type` facet.
        :return list of domain objects (POIs), total size of results and facets on type
        """
        filter_queries = filter_queries or []
        query = original_query or self.default_search
        q = {'defType': 'edismax',
             'spellcheck.collate': 'true',
             'pf': query,
             'q': query,
             }
        if facets:
            q.update({'facet': 'true',
                      'facet.sort': 'index',
                      'facet.mincount': '1',
                      'facet.field': facets})
        if location:
            lat, lon = location
            q['sfield'] = 'location'
            q['pt'] = '%s,%s' % (lat, lon)
            q['boost'] = 'recip(geodist(),2,200,20)'  # boost by geodist (linear function: 200/2*x+20)
            q['sort'] = 'score desc'                  # sort by score
            q['fl'] = '*,_dist_:geodist()'
        elif original_query:
            # no location provided but full-text search query provided
            q['sort'] = 'score desc'
        else:
            # no full-text query provided, sorting by name
            q['sort'] = 'name_sort asc'

        # TODO make a better filter query to handle having type and types_exact at the same time
        if pois_type:
            # filter on one specific type (and its subtypes)
            q['f.type.facet.prefix'] = pois_type + "/"  # we only want to display sub-types as the facet
            filter_queries.append('type_exact:{pois_type}*'.format(pois_type=pois_type.replace('/', '\/')))
        elif types_exact:
            # filter by a list of specific types (exact match)
            filter_queries.append('type_exact:({types})'.format(types=" OR ".join('"{t}"'.format(t=t)
                                                                                  for t in types_exact)))

        response = searcher.search(q, fq=filter_queries, start=start, count=count)

        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.query_suggestion:
                suggestion = response.query_suggestion
                return self.get_results(suggestion, location, start, count,
                                        pois_type=pois_type, types_exact=types_exact)
            else:
                return [], 0, None
        if response.facets:
            facet_values = {}
            for facet_field in facets:
                vals = response.facets['facet_fields'].get(facet_field, None)
                if vals:
                    # Place in iterator so zip steps through vals
                    vals = iter(vals)
                    vals = dict(zip(vals, vals))
                    facet_values[facet_field] = vals
        else:
            facet_values = None
        return [doc_to_poi(r, self.prefix_keys) for r in response.results], response.size, facet_values

    def get_place_by_identifier(self, ident):
        """Get place by identifier
        :param ident: identifier to lookup
        :return one POI or None if no result
        """
        results = self.get_places_by_identifiers([ident])
        if results:
            return results[0]
        else:
            return None

    def get_places_by_identifiers(self, idents):
        """Get places by identifiers
        Search in all identifiers if not found.
        :param idents: identifiers to lookup
        :return list of POI or None if no result
        """
        response = searcher.get_by_ids(idents)
        # First do a GET request by IDs
        if response.results:
            return [doc_to_poi(result, self.prefix_keys) for result in response.results]
        else:
            # If no result, do a SEARCH request on IDs
            return self.search_places_by_identifiers(idents)

    def search_place_by_identifier(self, ident):
        """Search for a place by an identifier
        :param ident: identifier to lookup
        :return a POI or None if no result
        """
        results = self.search_places_by_identifiers([ident])
        if results:
            return results[0]
        else:
            return None

    def search_places_by_identifiers(self, idents):
        """Search for a place by its identifiers
        :param ident: identifier to lookup
        :return POI or None if no result
        """
        response = searcher.search_for_ids("identifiers", idents)
        if response.results:
            return [doc_to_poi(result, self.prefix_keys) for result in response.results]
        else:
            return None

    def get_types(self):
        """Get types of POI
        :return dict of types
        """
        return get_types_dict()
