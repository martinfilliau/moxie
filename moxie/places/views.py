from flask import request, current_app, url_for, abort, redirect
from werkzeug.wrappers import BaseResponse

from moxie.core.views import ServiceView, accepts
from moxie.core.representations import JSON, HAL_JSON
from moxie.places.representations import (HalJsonPoisRepresentation, HalJsonPoiRepresentation, JsonPoisRepresentation,
                                          JsonPoiRepresentation, JsonTypesRepresentation, HalJsonTypesRepresentation)
from .services import POIService


class Search(ServiceView):
    """Search query for full-text search and context-aware search (geo-position)
    """
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
        # if there is an actual search query
        if self.query:
            # Try to match the query to identifiers if it's a one word query, useful when querying for bus stop naptan number
            # TODO pass the location to have the distance from the point
            if ' ' not in self.query:
                unique_doc = poi_service.search_place_by_identifier('*:{id}'.format(id=self.query))
                if unique_doc:
                    self.size = 1
                    self.facets = None
                    return [unique_doc]
            results, self.size, self.facets = poi_service.get_results(self.query, location, self.start, self.count, type=self.type)
        else:
            # no search query, return results nearby the given location
            results, self.size, self.facets = poi_service.get_nearby_results(location, self.start, self.count)
        return results

    @accepts(JSON)
    def as_json(self, response):
        return JsonPoisRepresentation(self.query, response).as_json()

    @accepts(HAL_JSON)
    def as_hal_json(self, response):
        return HalJsonPoisRepresentation(self.query, response, self.start, self.count, self.size,
            request.url_rule.endpoint, types=self.facets).as_json()


class PoiDetail(ServiceView):
    """Details of one POI
    """

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            abort(404)
        if doc.id != ident:
            # redirection to the same URL but with the main ID of the doc
            path = url_for(request.url_rule.endpoint, ident=doc.id)
            return redirect(path, code=301)
        else:
            return doc

    @accepts(JSON)
    def as_json(self, response):
        if issubclass(type(response), BaseResponse):
            # to handle 301 redirections and 404
            return response
        else:
            return JsonPoiRepresentation(response).as_json()

    @accepts(HAL_JSON)
    def as_hal_json(self, response):
        if issubclass(type(response), BaseResponse):
            # to handle 301 redirections and 404
            return response
        else:
            return HalJsonPoiRepresentation(response, request.url_rule.endpoint).as_json()


class Types(ServiceView):
    """Display list of all types from the configuration.
    """

    def handle_request(self):
        poi_service = POIService.from_context()
        return poi_service.get_types()

    @accepts(JSON)
    def as_json(self, types):
        return JsonTypesRepresentation(types).as_json()

    @accepts(HAL_JSON)
    def as_hal_json(self, types):
        return HalJsonTypesRepresentation(types, request.url_rule.endpoint).as_json()