from moxie.core.service import Service
from moxie.core.search import searcher


class POIService(Service):
    default_search = '*'

    def get_results(self, original_query, location):
        query = original_query or self.default_search
        response = searcher.search_nearby(query, location)
        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.spellchecks:
                suggestion = response.spellchecks[-1]
                return self.get_results(suggestion, location)
        return response

    def get_place_by_identifier(self, ident):
        response = searcher.get_by_ids([ident])
        # First do a GET request by its ID
        if response.results:
            return response.results[0]
        else:
            # If no result, do a SEARCH request on IDs
            response = searcher.search_for_ids("identifiers", [ident])
            if response.results:
                return response.results[0]
            else:
                return None