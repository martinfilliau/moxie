import urlparse
import importlib

from moxie.core.service import Service
from werkzeug.local import LocalProxy

SEARCH_SCHEMES = {
        'solr': ('moxie.core.search.solr', 'SolrSearch'),
        }


class SearchService(Service):
    def __init__(self, backend_uri):
        self.backend = self._get_backend(backend_uri)

    @staticmethod
    def _get_backend(backend_uri):
        """Parse the URI and imports the appropriate AbstractSearch
        implementation
        """
        parsed = urlparse.urlparse(backend_uri)
        search_scheme, http_scheme = parsed.scheme.split('+')
        http_path, _, index_name = parsed.path.rpartition('/')
        parsed = list(parsed)
        parsed[0] = http_scheme
        parsed[2] = http_path + '/'
        searcher_url = urlparse.urlunparse(parsed)
        search_module, search_klass = SEARCH_SCHEMES[search_scheme]
        searcher = importlib.import_module(search_module)
        searcher = getattr(searcher, search_klass)
        return searcher(index_name, searcher_url)

    def search_nearby(self, query, location):
        return self.backend.search_nearby(query, location)

    def get_by_ids(self, ids):
        return self.backend.get_by_ids(ids)

    def search_for_ids(self, id_key, identifiers):
        return self.backend.search_for_ids(id_key, identifiers)

    def index(self, document):
        return self.backend.index(document)

    def commit(self):
        return self.backend.commit()


searcher = LocalProxy(SearchService.from_context)
