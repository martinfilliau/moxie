import urlparse
import importlib

from flask import _app_ctx_stack

SEARCH_SCHEMES = {
        'solr': ('moxie.core.search.solr', 'SolrSearch'),
        }


def get_searcher():
    ctx = _app_ctx_stack.top
    searcher = getattr(ctx, 'moxie_searcher', None)
    if searcher is None:
        searcher_url = ctx.app.config.get('SEARCHER_URL',
            'solr+http://localhost:8983/solr/collection1')  # Defaults to Solr
        ctx.moxie_searcher = _find_searcher(searcher_url)
    return searcher


def _find_searcher(searcher_url):
    parsed = urlparse.urlparse(searcher_url)
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


class AbstractSearch(object):

    def __init__(self, index):
        """
        @param index name of the index / collection / core
        """
        pass

    def index(self, document):
        pass

    def search(self, query):
        pass

    def get_by_ids(self, document_ids):
        """
        Get documents by their unique ID
        """
        pass
