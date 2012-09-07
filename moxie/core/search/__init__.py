import urlparse
import importlib

from flask import _app_ctx_stack
from werkzeug.local import LocalProxy

SEARCH_SCHEMES = {
        'solr': ('moxie.core.search.solr', 'SolrSearch'),
        }


def get_searcher():
    """Sets the searcher instance on the application context.
    This is done for each application, so they can be configured with
    different search indexes. Eg. Places on one collection, events in another.

    The searcher is configured by setting a SEARCHER_URL in your config file.
    """
    ctx = _app_ctx_stack.top
    searcher = getattr(ctx, 'moxie_searcher', None)
    if searcher is None:
        searcher_url = ctx.app.config['SEARCHER_URL']
        searcher = _find_searcher(searcher_url)
        ctx.moxie_searcher = searcher
    return searcher
searcher = LocalProxy(get_searcher)


def _find_searcher(searcher_url):
    """Parse the URL and imports the appropriate AbstractSearch implementation"""
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
        raise NotImplementedError

    def search(self, query):
        raise NotImplementedError

    def clear_index(self):
        raise NotImplementedError

    def get_by_ids(self, document_ids):
        """
        Get documents by their unique ID
        """
        raise NotImplementedError
