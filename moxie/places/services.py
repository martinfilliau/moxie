from moxie.core.service import Service
from moxie.core.search import searcher
from moxie.places.solr import doc_to_poi


class POIService(Service):
    default_search = '*'

    def get_results(self, original_query, location):
        """Search POIs
        :param original_query: fts query
        :param location: latitude,longitude
        :return `py`class:SearchResponse` object
        """
        query = original_query or self.default_search
        response = searcher.search_nearby(query, location)
        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.query_suggestion:
                suggestion = response.query_suggestion
                return self.get_results(suggestion, location)
        return response

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