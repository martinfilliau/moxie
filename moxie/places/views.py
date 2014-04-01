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


ADDITIONAL_FILTERS_KEYS = [('accessibility', '_accessibility')]


class Search(ServiceView):
    """Search query for full-text search and context-aware search (geo-position)
    """
    methods = ['GET', 'OPTIONS']
    cors_allow_headers = 'geo-position'

    def handle_request(self):
        arguments = request.args.copy()
        if 'Geo-Position' in request.headers:
            location = request.headers['Geo-Position'].split(';')
        elif 'lat' in arguments and 'lon' in arguments:
            location = (arguments.pop('lat'), arguments.pop('lon'))
        else:
            location = None

        self.query = arguments.pop('q', '')
        self.type = arguments.pop('type', None)
        self.types_exact = arguments.poplist('type_exact')
        self.start = arguments.pop('start', 0)
        self.count = arguments.pop('count', 35)

        additional_filters = self._get_additional_filters(arguments, ADDITIONAL_FILTERS_KEYS)

        if self.query:
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
                                                                  self.start, self.count,
                                                                  pois_type=self.type,
                                                                  types_exact=self.types_exact,
                                                                  filter_queries=additional_filters)
        return results

    @accepts(HAL_JSON, JSON)
    def as_hal_json(self, response):
        return HALPOISearchRepresentation(self.query, response, self.start, self.count, self.size,
                                          request.url_rule.endpoint, types=self.facets, type=self.type,
                                          type_exact=self.types_exact).as_json()

    @staticmethod
    def _get_additional_filters(arguments, acceptable_values, default_value='true'):
        """Check if the key starts with one of the authorized key defined in acceptable_values,
        then replace it (eventually) by its internal representation
        :param arguments: dictionary of key/values as arguments from an HTTP request
        :param acceptable_values: list of tuples of acceptable values (key starts with, to be replaced)
        :param default_value: value to set for a filter if there is no value
        :return list of filters (as string)
        """
        additional_filters = []
        for k, v in arguments.iteritems():
            for acceptable_key, transformed_key in acceptable_values:
                if k.startswith(acceptable_key):
                    if not v:
                        v = default_value
                    additional_filters.append('{key}:{value}'.format(key=k.replace(acceptable_key, transformed_key),
                                                                     value=v))
                    break
        return additional_filters


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
