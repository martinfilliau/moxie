import logging
import requests
import json

from moxie.core.search import SearchResponse, SearchServerException


logger = logging.getLogger(__name__)


class SolrSearch(object):

    DEFAULT_TIMEOUT = 1     # default timeout in seconds

    def __init__(self, core, server_url, return_type='json'):
        self.core = core
        self.return_type = return_type
        self.server_url = server_url
        # Default methods and paths to on Solr
        self.methods = {
            'update': 'update/',
            'select': 'select/',
            'get': 'get',
            'suggest': 'suggest',
        }
        self.content_types = {
                'json': 'application/json',
                'form': 'application/x-www-form-urlencoded',
                }

    def search_nearby(self, query, location, location_field='location'):
        lat, lon = location
        q = {'defType': 'edismax',
                'spellcheck.collate': 'true',
                'pf': query,
                'q': query,
                'sfield': location_field,
                'pt': '%s,%s' % (lon, lat),
                'sort': 'geodist() asc',
                'fl': '*,_dist_:geodist()',
                }
        return self.search(q)

    def search(self, query):
        l = []
        for k, v in query.items():
            l.append(k + '=' + v)
        data = "&".join(l)
        headers = {'Content-Type': self.content_types['form']}
        results = self.connection(self.methods['select'],
                data=data, headers=headers)
        return SolrSearchResponse(results.json)

    def suggest(self, query):
        params = {'q': query}
        results = self.connection(self.methods['suggest'],
            params=params)
        return results

    def get_by_ids(self, document_ids):
        """Get documents by their ID (using the real-time GET feature of Solr 4).
        Query string to build is as "?ids=oxpoints:23232805,oxpoints:23232801"
        (i.e. param is ids, and IDs are comma-separated.
        :param document_ids: list of document ids
        :return list of documents
        """
        ids = ",".join(document_ids)
        params = { 'ids': ids }
        results = self.connection(self.methods['get'],
            params=params)
        return SolrSearchResponse(results.json)

    def index(self, document, params=None, count_per_page=50):
        """Index a list of objects, do paging
        :param document: must be a list of objects to index
        :param params: additional parameters to add
        :param count_per_page: number of items per page to send
        """
        if len(document) < count_per_page:
            self.index_all(document, params)
        else:
            for i in range(0, len(document), count_per_page):
                self.index_all(document[i:i+count_per_page], params)

    def index_all(self, document, params=None):
        """Index a list of objects
        :param document: list of documents
        :param params: additional parameters
        """
        data = json.dumps(document)
        headers = {'Content-Type': self.content_types[self.return_type]}
        response = self.connection(self.methods['update'], params=params,
            data=data, headers=headers)
        if response.status_code != 200:
            raise SearchServerException("Server returned HTTP {code}".format(
                code=response.status_code))

    def commit(self):
        return self.connection(self.methods['update'],
                params={'commit': 'true'})

    def clear_index(self):
        """WARNING: This action will delete *all* documents in your index.
        TODO: This doesn't seem to work? Despite being the documented way
        """
        logger.warning("Clearing index!")
        data = json.dumps({'delete': {'query': '*:*'}})
        headers = {'Content-Type': self.content_types[self.return_type]}
        return self.connection(self.methods['update'], data=data,
                params={'commit': 'true'}, headers=headers)

    def search_for_ids(self, id_key, identifiers):
        """Search for documents by their identifiers (NB: this is not the unique ID used by Solr).
        """
        query = []
        for id in identifiers:
            query.append('%s:%s' % (id_key, self.solr_escape(id)))
        query_string = {'q': " OR ".join(query)}
        return self.search(query_string)

    def connection(self, method, params=None, data=None, headers=None):
        """Does a GET request if there is no data otherwise a POST
        :param params: URL parameters as a dict
        :param data: POST form
        """
        headers = headers or dict()
        params = params or dict()
        params['wt'] = self.return_type
        url = '{0}{1}/{2}'.format(self.server_url, self.core, method)
        logger.debug(data)
        if data:
            return requests.post(url, data, headers=headers,
                    params=params, timeout=self.DEFAULT_TIMEOUT)
        else:
            return requests.get(url, headers=headers,
                    params=params, timeout=self.DEFAULT_TIMEOUT)

    @staticmethod
    def solr_escape(string):
        return string.replace(':', '\:')


class SolrSearchResponse(SearchResponse):

    def __init__(self, solr_response):
        """Prepare a :py:class:`SearchResponse` object
        :param solr_response: response from Solr
        """
        try:
            query = solr_response['responseHeader']['params']['q']
        except:
            query = None
        try:
            results = solr_response['response']['docs']
        except:
            results = None
        try:
            suggestion = solr_response['spellcheck']['suggestions'][-1]
        except:
            suggestion = None

        super(SolrSearchResponse, self).__init__(solr_response, query, results, suggestion)