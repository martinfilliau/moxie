import urlparse
import importlib

from moxie.core.service import Service
from werkzeug.local import LocalProxy

SEARCH_SCHEMES = {
        'solr': ('moxie.core.search.solr', 'SolrSearch'),
        }


class SearchService(Service):
    """Represents the abstraction between our Search implementation
    (by default, Apache Solr) and the public API. For configuration
    details, see the :class:`~moxie.core.service.Service` documentation.

    All Search requests should be made through this service.
    """
    def __init__(self, backend_uri):
        self._backend = self._get_backend(backend_uri)

    @staticmethod
    def _get_backend(backend_uri):
        """Parse the URI and imports the appropriate Search implementation
        The ``backend_uri`` schema is as follows:
        ``implementation+transport://domain/path/collection`` where:

        ``implementation``
            is the name of a supported scheme in
            :py:data:`moxie.core.search.SEARCH_SCHEMES`.
        ``collection``
            name used by the backend to identify your index.


        :param backend_uri: URI Representing your search implementation
                            e.g. ``solr+http://example.com/solr/collection``
        :returns: Searcher implementation.
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
        return self._backend.search_nearby(query, location)

    def get_by_ids(self, ids):
        return self._backend.get_by_ids(ids)

    def search_for_ids(self, id_key, identifiers):
        return self._backend.search_for_ids(id_key, identifiers)

    def index(self, document):
        return self._backend.index(document)

    def commit(self):
        return self._backend.commit()


searcher = LocalProxy(SearchService.from_context)


class SearchResponse(object):

    def __init__(self, response):
        """
        Init a SearchResponse object
        :param response: raw response from a Request
        """
        raise Exception("This class should be sub-classed and init by its subclass.")

    def __repr__(self):
        return "<SearchResponse ['{0}']>".format(self.query)

    @property
    def query(self):
        """String of the query (FTS)
        :rtype string
        """
        return self._query

    @property
    def results(self):
        """Response documents
        :return list of dict or None if no results
        :rtype list of dict
        """
        return self._results

    @property
    def facets(self):
        """Facets of the query
        :rtype list of facets"""
        return self.facets

    @property
    def spellchecks(self):
        """Spellchecks for the query
        :return list of spellchecks or None
        :rtype list of dict"""
        return self._spellchecks

    @property
    def as_json(self):
        """Raw response as JSON
        :rtype string of JSON
        """
        import json
        return json.loads(self._raw_response)

    @property
    def as_dict(self):
        """Raw response as a dict
        :rtype dict
        """
        return self._raw_response