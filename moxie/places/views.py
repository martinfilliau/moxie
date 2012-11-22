from flask import request, current_app, url_for, abort, redirect

from moxie.core.views import ServiceView

from .importers.helpers import simplify_doc_for_render
from .services import POIService
from moxie.transport.services import TransportService


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    cors_allow_headers = 'geo-position'

    def handle_request(self):
        response = dict()
        if 'Geo-Position' in request.headers:
            response['lat'], response['lon'] = request.headers['Geo-Position'].split(';')
        query = request.args.get('q', '')
        if 'lat' in response and 'lon' in response:
            location = response['lat'], response['lon']
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = request.args.get('lat', default_lat), request.args.get('lon', default_lon)
        poi_service = POIService.from_context()
        transport_service = TransportService.from_context()
        r = poi_service.get_results(query, location)
        simplified_results = []
        for doc in r.results:
            if transport_service.get_provider(doc):
                # Add a property hasRti if one provider is able to handle
                # this document for real-time information
                doc['hasRti'] = url_for('places.rti', ident=doc['id'])
            simplified_results.append(simplify_doc_for_render(doc))
        response['results'] = simplified_results
        response['query'] = r.query
        return response


class PoiDetail(ServiceView):

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        transport_service = TransportService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            abort(404)
        if doc['id'] != ident:
            path = url_for('places.poidetail', ident=doc['id'])
            return redirect(path, code=301)
        else:
            if transport_service.get_provider(doc):
                doc['hasRti'] = url_for('places.rti', ident=doc['id'])
            return simplify_doc_for_render(doc)
