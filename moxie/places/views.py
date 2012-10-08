import json

from flask import request, current_app, url_for, abort, redirect, jsonify
from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher
from moxie.core.kv import kv_store
from moxie.places.importers.helpers import simplify_doc_for_render


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    default_search = '*'
    default_allow_headers = 'geo-position'

    def get_results(self, original_query, location):
        query = original_query or self.default_search
        results = searcher.search_nearby(query, location)
        if results.json['response']['numFound'] == 0:
            if results.json['spellcheck']['suggestions']:
                suggestion = str(results.json['spellcheck']['suggestions'][-1])
                results = self.get_results(suggestion, location)
                return results
            else:
                return {}
        out = []
        for doc in results.json['response']['docs']:
            out.append(simplify_doc_for_render(doc))
        return {'query': query, 'results': out}

    def handle_request(self):
        response = dict()
        if 'Geo-Position' in request.headers:
            response['lat'], response['lon'] = request.headers['Geo-Position'].split(';')
        query = request.args.get('q', None)
        if 'lat' in response and 'lon' in response:
            location = response['lat'], response['lon']
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = request.args.get('lat', default_lat), request.args.get('lon', default_lon)
        response.update(self.get_results(query, location))
        return response


class PoiDetail(ServiceView):

    def handle_request(self, id):
        if id.endswith('/'):
            id = id.split('/')[0]
        results = searcher.get_by_ids([id])
        # First do a GET request by its ID
        if results.json['response']['docs']:
            doc = results.json['response']['docs'][0]
            return jsonify(simplify_doc_for_render(doc))
        else:
            # If no result, do a SEARCH request on IDs
            results = searcher.search_for_ids("identifiers", [id])
            if results.json['response']['docs']:
                doc = results.json['response']['docs'][0]
                path = url_for('places.poidetail', id=doc['id'])
                return redirect(path, code=301)
            else:
                abort(404)

    @accepts('application/json')
    def as_json(self, response):
        return response


class BusRti(ServiceView):
    methods = ['GET', 'OPTIONS']

    CACHE_KEY_FORMAT = '{0}_naptan_{1}'
    CACHE_EXPIRE = 10   # seconds for cache to expire

    def __init__(self, service):
        self.service = service

    def handle_request(self, id):
        cache = kv_store.get(self.CACHE_KEY_FORMAT.format(__name__, id))
        if cache:
            return json.loads(cache)
        else:
            services, messages = self.service.get_rti(id)
            response = {
                'services': services,
                'messages': messages
            }
            kv_store.setex(self.CACHE_KEY_FORMAT.format(__name__, id),
                    self.CACHE_EXPIRE, json.dumps(response))
            return response
