from flask import request, current_app, url_for, abort, redirect
from werkzeug.wrappers import BaseResponse

from moxie.core.views import ServiceView, accepts
from moxie.core.representations import JSON, HAL_JSON
from moxie.places.representations import HalJsonPoisRepresentation, HalJsonPoiRepresentation, JsonPoisRepresentation, JsonPoiRepresentation
from .services import POIService


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    cors_allow_headers = 'geo-position'

    def handle_request(self):
        response = dict()
        if 'Geo-Position' in request.headers:
            response['lat'], response['lon'] = request.headers['Geo-Position'].split(';')
        self.query = request.args.get('q', None)
        self.type = request.args.get('type', None)
        self.start = request.args.get('start', 0)
        self.count = request.args.get('count', 35)
        if 'lat' in response and 'lon' in response:
            location = response['lat'], response['lon']
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = request.args.get('lat', default_lat), request.args.get('lon', default_lon)

        poi_service = POIService.from_context()
        if self.query:
            # Try to match the query to identifiers, useful when querying for bus stop naptan number
            # TODO pass the location to have the distance from the point
            unique_doc = poi_service.search_place_by_identifier('*:{id}'.format(id=self.query))
            if unique_doc:
                self.size = 1
                return [unique_doc]
            results, self.size = poi_service.get_results(self.query, location, self.start, self.count, type=self.type)
        else:
            results, self.size = poi_service.get_nearby_results(location, self.start, self.count)
        return results

    @accepts(JSON)
    def as_json(self, response):
        return JsonPoisRepresentation(self.query, response).as_json()

    @accepts(HAL_JSON)
    def as_hal_json(self, response):
        return HalJsonPoisRepresentation(self.query, response, self.start, self.count, self.size, request.url_rule.endpoint).as_json()


class PoiDetail(ServiceView):

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            abort(404)
        if doc.id != ident:
            # redirection to the main ID
            path = url_for(request.url_rule.endpoint, ident=doc.id)
            return redirect(path, code=301)
        else:
            return doc

    @accepts(JSON)
    def as_json(self, response):
        if issubclass(type(response), BaseResponse):
            return response
        else:
            return JsonPoiRepresentation(response).as_json()

    @accepts(HAL_JSON)
    def as_hal_json(self, response):
        if issubclass(type(response), BaseResponse):
            return response
        else:
            return HalJsonPoiRepresentation(response, request.url_rule.endpoint).as_json()