from requests import post, get
from urllib import urlencode
import logging

from moxie.core.search import AbstractSearch

logger = logging.getLogger(name=__name__)


class SolrSearch(AbstractSearch):

    UPDATE = "update/"
    SEARCH = "select/"
    DEFAULT_TIMEOUT = 1     # default timeout in seconds

    def __init__(self, core, return_type='json'):
        self.server_url = 'http://localhost:8983/solr/'
        self.core = core
        self.return_type = return_type
        super(SolrSearch, self).__init__(core)

    def search(self, query):
        results = self.connection(self.SEARCH, data=query)
        return results

    def index(self, document):
        pass

    def commit(self):
        pass

    def search_for_id(self, id):
        query = {'q': 'identifiers:{0}'.format(self.solr_escape(id))}
        return self.search(query)

    def connection(self, method, params=None, data=None):
        """
        Does a GET request if there is no data otherwise a POST
        @param params GET parameters
        @param data POST form
        """
        if not params:
            params = {}
        if data:
            data = urlencode(data)
        params['wt'] = self.return_type
        url = '{0}{1}/{2}{3}'.format(self.server_url, self.core, method,
                                     urlencode(params))
        logger.debug(url)
        if data:
            return post(url, data, timeout=self.DEFAULT_TIMEOUT)
        else:
            return get(url, timeout=self.DEFAULT_TIMEOUT)

    @staticmethod
    def solr_escape(string):
        return string.replace(':', '\:')