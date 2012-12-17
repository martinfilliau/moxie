from moxie.core.service import Service
from moxie.core.search import searcher
from moxie.places.importers.helpers import get_types_dict
from moxie.places.solr import doc_to_poi


class POIService(Service):
    default_search = '*'

    def __init__(self, nearby_excludes=None):
        """POI service
        :param nearby_excludes: list of types to exclude in a nearby search
        """
        self.nearby_excludes = nearby_excludes or []

    def get_results(self, original_query, location, start, count, type=None):
        """Search POIs
        :param original_query: fts query
        :param location: latitude,longitude
        :param start: index of the first result of the page
        :param count: number of results for the page
        :return list of domain objects (POIs) and total size of results
        """
        query = original_query or self.default_search
        if type:
            type = 'type_exact:{type}*'.format(type=type.replace('/', '\/'))
        response = searcher.search_nearby(query, location, fq=type, start=start, count=count)
        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.query_suggestion:
                suggestion = response.query_suggestion
                return self.get_results(suggestion, location, start, count, type=type)
            else:
                return [], 0
        return [doc_to_poi(r) for r in response.results], response.size

    def get_nearby_results(self, location, start, count, all_types=False):
        """Get results around a location (nearby)
        :param location: latitude,longitude
        :param start: index of the first result of the page
        :param count: number of results for the page
        :param all_types: display all types or excludes some types defined in configuration
        :return: list of domain objects (POIs) and total size of results
        """
        lat, lon = location
        q = {'q': '*:*',
             'sfield': 'location',
             'pt': '%s,%s' % (lon, lat),
             'sort': 'geodist() asc',
             'fl': '*,_dist_:geodist()',
             'facet': 'true',
             'facet.field': 'type',
             'facet.sort': 'index'
             }
        fq = None
        if not all_types and len(self.nearby_excludes) > 0:
            fq = "-type_exact:({types})".format(types=' OR '.join('"{type}"'.format(type=t) for t in self.nearby_excludes))
        response = searcher.search(q, fq=fq, start=start, count=count)
        if response.results:
            return [doc_to_poi(r) for r in response.results], response.size
        else:
            return None, None

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