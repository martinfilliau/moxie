from requests import post, get
from urllib import urlencode
import logging

from moxie.core.search import AbstractSearch

logger = logging.getLogger(name=__name__)


class SolrSearch(AbstractSearch):

    DEFAULT_TIMEOUT = 1     # default timeout in seconds

    def __init__(self, core, return_type='json'):
        self.server_url = 'http://localhost:8983/solr/'
        self.core = core
        self.return_type = return_type
        # Default methods and paths to on Solr
        self.methods = {'update': 'update/', 'select': 'select/'}
        self.content_types = {'json': 'application/json'}
        super(SolrSearch, self).__init__(core)

    def search(self, query):
        results = self.connection(self.methods['search'], data=query)
        return results

    def index(self, document):
        params = {'commit': 'true'}
        results = self.connection(self.methods['update'], params=params,
                data=document)

    def commit(self):
        raise NotImplemented()

    def search_for_id(self, id):
        query = {'q': 'identifiers:{0}'.format(self.solr_escape(id))}
        return self.search(query)

    def connection(self, method, params=None, data=None, headers=None):
        """
        Does a GET request if there is no data otherwise a POST
        @param params GET parameters
        @param data POST form
        """
        if not params:
            params = dict()
        if data:
            data = urlencode(data)
        params['wt'] = self.return_type
        url = '{0}{1}/{2}'.format(self.server_url, self.core, method)
        logger.debug(url)
        if data:
            return post(url, data, params=params, timeout=self.DEFAULT_TIMEOUT)
        else:
            return get(url, params=params, timeout=self.DEFAULT_TIMEOUT)

    @staticmethod
    def solr_escape(string):
        return string.replace(':', '\:')
