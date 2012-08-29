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
        self.methods = {
            'update': 'update/',
            'select': 'select/',
            'get': 'get'
        }
        self.content_types = {
                'json': 'application/json',
                'form': 'application/x-www-form-urlencoded',
                }
        super(SolrSearch, self).__init__(core)

    def search_nearby(self, query, location, location_field='location'):
        lat, lon = location
        q = {'defType': 'edismax',
                'qf': 'name',
                'pf': query,
                'q': query,
                'sfield': location_field,
                'pt': '%s,%s' % (lon, lat),
                'sort': 'geodist() asc',
                'fl': '*,_dist_:geodist()',
                }
        results = self.search(q)
        return results

    def search(self, query):
        l = []
        for k, v in query.items():
            l.append(k + '=' + v)
        data = "&".join(l)
        headers = {'Content-Type': self.content_types['form']}
        results = self.connection(self.methods['select'],
                data=data, headers=headers)
        return results

    def get_by_ids(self, document_ids):
        """
        Get documents by their ID (using the real-time GET feature of Solr 4).
        Query string to build is as "?ids=5a9b4f27-310f-4207-8a97-1dce48fdf31d,a791b6e9-e532-461f-8ae1-12218f0db81e"
        (i.e. param is ids, and IDs are comma-separated.
        @param document_ids list of document ids
        @return list of documents
        """
        ids = ",".join(document_ids)
        params = { 'ids': ids }
        results = self.connection(self.methods['get'],
            params=params)
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
        @param params URL parameters as a dict
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
