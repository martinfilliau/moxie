from moxie.core.service import Service
from moxie.core.search import searcher

from .importers.helpers import simplify_doc_for_render


class POIService(Service):
    default_search = '*'

    def get_results(self, original_query, location):
        query = original_query or self.default_search
        response = searcher.search_nearby(query, location)
        results = response.json
        if results['response']['numFound'] == 0:
            if results['spellcheck']['suggestions']:
                suggestion = str(results['spellcheck']['suggestions'][-1])
                results = self.get_results(suggestion, location)
                return results
            else:
                return {}
        out = []
        for doc in results['response']['docs']:
            out.append(simplify_doc_for_render(doc))
        return {'query': query, 'results': out}

    def get_place_by_identifier(self, ident):
        response = searcher.get_by_ids([ident])
        results = response.json
        # First do a GET request by its ID
        if results['response']['docs']:
            doc = results['response']['docs'][0]
            return doc
        else:
            # If no result, do a SEARCH request on IDs
            response = searcher.search_for_ids("identifiers", [ident])
            results = response.json
            if results['response']['docs']:
                doc = results['response']['docs'][0]
                return doc
            else:
                return None
