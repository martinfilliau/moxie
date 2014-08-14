import logging
import requests
import json
import time

from urllib import urlencode
from requests.exceptions import RequestException

from moxie.core.search import SearchResponse, SearchServerException
from moxie.core.metrics import statsd


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
            'healthcheck': 'admin/ping',
        }
        self.content_types = {
                'json': 'application/json',
                'form': 'application/x-www-form-urlencoded',
                }

    def __repr__(self):
        return '<{name} {url}{core}>'.format(name=__name__,
            url=self.server_url, core=self.core)

    def search(self, query, fq=None, start=0, count=10):
        query['start'] = str(start)
        query['rows'] = str(count)
        if fq:
            query['fq'] = fq
        # doseq=True will add multiple time the same parameter if there's an array
        data = urlencode(query, doseq=True)
        headers = {'Content-Type': self.content_types['form']}
        results = self.connection(self.methods['select'],
                data=data, headers=headers)
        return SolrSearchResponse(results.json())

    def suggest(self, query, fq=None, start=0, count=10):
        query['start'] = str(start)
        query['rows'] = str(count)
        if fq:
            query['fq'] = fq
        results = self.connection(self.methods['suggest'],
                params=query)
        return SolrSearchResponse(results.json())

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
        return SolrSearchResponse(results.json())

    def index(self, document, params=None, count_per_page=100):
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
                time.sleep(1)

    def index_all(self, document, params=None):
        """Index a list of objects
        :param document: list of documents
        :param params: additional parameters
        """
        data = json.dumps(document)
        headers = {'Content-Type': self.content_types[self.return_type]}
        self.connection(self.methods['update'], params=params,
                        data=data, headers=headers, timeout=120)

    def commit(self):
        return self.connection(self.methods['update'],
                               timeout=120,
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
        return self.search(query_string, start=0, count=100)

    def connection(self, method, params=None, data=None, headers=None, timeout=None):
        """Does a GET request if there is no data otherwise a POST
        :param params: URL parameters as a dict
        :param data: POST form
        :param headers: custom headers to pass to Solr as a dict
        :param timeout: custom timeout
        """
        headers = headers or dict()
        timeout = timeout or self.DEFAULT_TIMEOUT
        params = params or dict()
        params['wt'] = self.return_type
        url = '{0}{1}/{2}'.format(self.server_url, self.core, method)
        logger.debug(data)
        try:
            with statsd.timer('core.search.solr.request'):
                if data:
                    response = requests.post(url, data, headers=headers,
                                             params=params, timeout=timeout)
                else:
                    response = requests.get(url, headers=headers,
                                            params=params, timeout=timeout)
        except RequestException as re:
            logger.error('Error in request to Solr', exc_info=True,
                         extra={
                             'data': {'url': url,
                                      'params': params,
                                      'headers': headers}})
            # has to cast to str as sometimes the message is not a string..
            raise SearchServerException(str(re.message))
        else:
            if response.ok:
                return response
            else:
                try:
                    json = response.json()
                except:
                    json = None
                message = "Search server (Solr) exception"
                if json and 'error' in json and 'msg' in json['error']:
                    solr_message = json['error']['msg']
                else:
                    solr_message = message
                logger.error(message, extra={
                    'data': {
                        'url': url,
                        'solr_message': solr_message,
                        'solr_status_code': response.status_code,
                        'params': params,
                        'headers': headers}})
                raise SearchServerException(solr_message, status_code=response.status_code)

    def healthcheck(self):
        try:
            response = requests.get('{url}{core}/{method}'.format(url=self.server_url,
                core=self.core, method=self.methods['healthcheck']), timeout=2)
            return response.ok, response.json()['status']
        except Exception as e:
            logger.error('Error while checking health of Solr', exc_info=True)
            return False, e

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
            size = solr_response['response']['numFound']
        except:
            size = None
        try:
            results = solr_response['response']['docs']
        except:
            results = None
        try:
            suggestion = solr_response['spellcheck']['suggestions'][-1]
        except:
            suggestion = None
        try:
            # WARNING: differents types of facets: counts, query, ranges, this has to be
            # handled in your code for now
            facets = solr_response['facet_counts']
        except:
            facets = None

        super(SolrSearchResponse, self).__init__(solr_response, query, size,
            results=results, query_suggestion=suggestion, facets=facets)
