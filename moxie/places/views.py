from datetime import timedelta
from flask import request, current_app, url_for, redirect
from werkzeug.wrappers import BaseResponse

from moxie.core.views import ServiceView, accepts
from moxie.core.representations import JSON, HAL_JSON
from moxie.core.exceptions import BadRequest, NotFound
from moxie.places.representations import (HALPOIsRepresentation, HALPOIRepresentation, HALTypesRepresentation)
from .services import POIService


class Search(ServiceView):
    """Search query for full-text search and context-aware search (geo-position)
    """
    methods = ['GET', 'OPTIONS']
    cors_allow_headers = 'geo-position'

    def handle_request(self):
        if 'Geo-Position' in request.headers:
            location = request.headers['Geo-Position'].split(';')
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = (request.args.get('lat', default_lat),
                        request.args.get('lon', default_lon))

        location = (float(location[0]), float(location[1]))

        if location[0] < -90 or location[0] > 90 or location[1] < -180 or location[1] > 180:
            # attempt to reverse lat and lon as it seems that it does happen sometimes?
            print "reversing"
            location = (location[1], location[0])

        print location

        if (location[0] < -90 or location[0] > 90) or (location[1] < -180 or location[1] > 180):
            raise BadRequest("Latitude should range between -90 and 90, Longitude should range between -180 and 180")

        self.query = request.args.get('q', '')
        self.type = request.args.get('type', None)
        self.types_exact = request.args.getlist('type_exact')
        self.start = request.args.get('start', 0)
        self.count = request.args.get('count', 35)
        all_types = False
        if self.query:
            all_types = True
            self.query = self.query.encode('utf8')
        if self.type and self.types_exact:
            raise BadRequest("You cannot have both 'type' and 'type_exact' parameters at the moment.")

        poi_service = POIService.from_context()
        # Try to match the query to identifiers if it's a one word query,
        # useful when querying for bus stop naptan number
        # TODO pass the location to have the distance from the point

        if ' ' not in self.query:
            unique_doc = poi_service.search_places_by_identifiers(['*:{id}'.format(id=self.query)])
            if unique_doc:
                self.size = 1
                self.facets = None
                return unique_doc
        results, self.size, self.facets = poi_service.get_results(self.query, location,
            self.start, self.count, type=self.type, types_exact=self.types_exact, all_types=all_types)
        return results

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, response):
        return HALPOIsRepresentation(self.query, response, self.start, self.count, self.size,
            request.url_rule.endpoint, types=self.facets, type=self.type, type_exact=self.types_exact).as_json()


class PoiDetail(ServiceView):
    """Details of one POI
    """

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        doc = poi_service.get_place_by_identifier(ident)
        if not doc:
            raise NotFound()
        if doc.id != ident:
            # redirection to the same URL but with the main ID of the doc
            path = url_for(request.url_rule.endpoint, ident=doc.id)
            return redirect(path, code=301)
        else:
            return doc

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, response):
        if issubclass(type(response), BaseResponse):
            # to handle 301 redirections and 404
            return response
        else:
            return HALPOIRepresentation(response, request.url_rule.endpoint).as_json()


class Types(ServiceView):
    """Display list of all types from the configuration.
    """

    expires = timedelta(days=1)

    def handle_request(self):
        poi_service = POIService.from_context()
        return poi_service.get_types()

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, types):
        return HALTypesRepresentation(types, request.url_rule.endpoint).as_json()
