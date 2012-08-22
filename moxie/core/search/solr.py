import logging
import requests
import json

from urllib import urlencode

from moxie.core.search import AbstractSearch


logger = logging.getLogger(name=__name__)


class SolrSearch(AbstractSearch):

    DEFAULT_TIMEOUT = 1     # default timeout in seconds

    def __init__(self, core, return_type='json',
            server_url='http://localhost:8983/solr/'):
        self.core = core
        self.return_type = return_type
        self.server_url = server_url
        # Default methods and paths to on Solr
        self.methods = {'update': 'update/', 'select': 'select/'}
        self.content_types = {
                'json': 'application/json',
                'form': 'application/x-www-form-urlencoded',
                }
        super(SolrSearch, self).__init__(core)

    def search(self, query):
        l = []
        for k,v in query.items():
            l.append(k+'='+v)
        data = "&".join(l)
        headers = {'Content-Type': self.content_types['form']}
        results = self.connection(self.methods['select'],
                data=data, headers=headers)
        return results

    def index(self, document, params=None):
        data = json.dumps(document)
        headers = {'Content-Type': self.content_types[self.return_type]}
        response = self.connection(self.methods['update'], params=params,
                data=data, headers=headers)
        if response.status_code != 200:
            raise Exception

    def commit(self):
        raise NotImplemented()

    def search_for_ids(self, id_key, identifiers):
        query = []
        for id in identifiers:
            query.append('%s:%s' % (id_key, self.solr_escape(id)))
        query_string = {'q': " OR ".join(query)}
        results = self.search(query_string)
        return results

    def connection(self, method, params=None, data=None, headers=None):
        """
        Does a GET request if there is no data otherwise a POST
        @param params URL parameters
        @param data POST form
        """
        headers = headers or dict()
        params = params or dict()
        params['wt'] = self.return_type
        url = '{0}{1}/{2}'.format(self.server_url, self.core, method)
        logger.debug(url)
        if data:
            return requests.post(url, data, headers=headers,
                    params=params, timeout=self.DEFAULT_TIMEOUT)
        else:
            return requests.get(url, headers=headers,
                    params=params, timeout=self.DEFAULT_TIMEOUT)

    @staticmethod
    def solr_escape(string):
        return string.replace(':', '\:')
