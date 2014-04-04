from datetime import timedelta
from flask import request, url_for, redirect
from werkzeug.wrappers import BaseResponse

from moxie.core.views import ServiceView, accepts
from moxie.core.representations import JSON, HAL_JSON
from moxie.core.exceptions import BadRequest, NotFound
from moxie.places.representations import (HALPOISearchRepresentation, HALPOIsRepresentation,
                                          HALPOIRepresentation, HALTypesRepresentation,
                                          GeoJsonPointsRepresentation)
from .services import POIService


class Search(ServiceView):
    """Search query for full-text search and context-aware search (geo-position)
    """
    methods = ['GET', 'OPTIONS']
    cors_allow_headers = 'geo-position'

    def handle_request(self):
        arguments = request.args.copy()

        # Always remove lat lon from arguments so they are not accidentally
        # passed to POIService.get_results in other_args
        lat, lon = arguments.pop('lat', None), arguments.pop('lon', None)
        if 'Geo-Position' in request.headers:
            location = request.headers['Geo-Position'].split(';')
        elif lat and lon:
            location = (lat, lon)
        else:
            location = None

        self.query = arguments.pop('q', '').encode('utf8')
        self.type = arguments.pop('type', None)
        self.types_exact = arguments.poplist('type_exact')
        self.start = arguments.pop('start', 0)
        self.count = arguments.pop('count', 35)
        self.facet_fields = arguments.poplist('facet')
        self.other_args = arguments

        additional_filters = ["%s:%s" % (key, val or True) for (key, val) in arguments.iteritems()]

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

        kwargs = {
            'pois_type': self.type,
            'types_exact': self.types_exact,
            'filter_queries': additional_filters
        }

        # Only pass `facets` if we have user-speciified facets
        if self.facet_fields:
            kwargs['facets'] = self.facet_fields
        results, self.size, self.facets = poi_service.get_results(
            self.query, location, self.start, self.count, **kwargs)
        return results

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, response):
        return HALPOISearchRepresentation(
            self.query, response, self.start, self.count, self.size,
            request.url_rule.endpoint, facets=self.facets, type=self.type,
            type_exact=self.types_exact,
            other_args=self.other_args).as_json()


class GeoJsonSearch(Search):

    @accepts(HAL_JSON, JSON)
    def as_json(self, response):
        return GeoJsonPointsRepresentation(response).as_json()


class PoiDetail(ServiceView):
    """Details of one or multiple POIs separated by a comma
    """

    def handle_request(self, ident):
        if ident.endswith('/'):
            ident = ident.split('/')[0]
        poi_service = POIService.from_context()
        # split identifiers on comma if there is more than
        # one identifier requested
        self.idents = ident.split(',')
        if len(self.idents) == 1:
            doc = poi_service.get_place_by_identifier(ident)
            if not doc:
                raise NotFound()
            if doc.id != ident:
                # redirection to the same URL but with the main ID of the doc
                path = url_for(request.url_rule.endpoint, ident=doc.id)
                return redirect(path, code=301)
            else:
                return doc
        else:
            documents = poi_service.get_places_by_identifiers(self.idents)
            if not documents:
                raise NotFound()
            else:
                return documents

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, response):
        if issubclass(type(response), BaseResponse):
            # to handle 301 redirections and 404
            return response
        elif type(response) == list:
            # if more than one POI has been requested
            size = len(response)
            return HALPOIsRepresentation(response, size, request.url_rule.endpoint, self.idents).as_json()
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
