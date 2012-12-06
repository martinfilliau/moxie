from flask import request, current_app, url_for, abort, redirect

from moxie.core.views import ServiceView
from moxie.places.representations import HalJsonPoisRepresentation, HalJsonPoiRepresentation
from .services import POIService


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
        r = poi_service.get_results(query, location)
        return HalJsonPoisRepresentation(query, r, 0, 10, 10).as_dict()


class PoiDetail(ServiceView):

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            abort(404)
        if doc.id != ident:
            path = url_for('places.poidetail', ident=doc.id)
            return redirect(path, code=301)
        else:
            return HalJsonPoiRepresentation(doc).as_dict()