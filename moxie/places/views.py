import json

from flask import request, current_app, url_for, abort, redirect, jsonify

from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher
from moxie.core.kv import kv_store

from moxie.transport.services import TransportService

from .importers.helpers import simplify_doc_for_render
from .services import POIService


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    default_allow_headers = 'geo-position'

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
        poi_service = POIService.from_context()
        results = poi_service.get_results(query, location)
        response.update(results)
        return response


class PoiDetail(ServiceView):

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            abort(404)
        if doc['id'] != ident:
            path = url_for('places.poidetail', ident=doc['id'])
            return redirect(path, code=301)
        else:
            current_app.logger.info(doc)
            return simplify_doc_for_render(doc)


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    CACHE_KEY_FORMAT = '{0}_naptan_{1}'
    CACHE_EXPIRE = 10   # seconds for cache to expire

    def handle_request(self, ident):
        cache = kv_store.get(self.CACHE_KEY_FORMAT.format(__name__, ident))
        if cache:
            return json.loads(cache)
        else:
            transport_service = TransportService.from_context()
            services, messages = transport_service.get_rti(ident)
            response = {
                'services': services,
                'messages': messages
            }
            kv_store.setex(self.CACHE_KEY_FORMAT.format(__name__, ident),
                    self.CACHE_EXPIRE, json.dumps(response))
            return response
