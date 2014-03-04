import logging

from flask import url_for, jsonify
from shapely.wkt import loads as wkt_loads
from shapely.geometry import Point
from geojson import dumps as geojson_dumps
from geojson import Feature, FeatureCollection

from moxie.core.representations import Representation, HALRepresentation, get_nav_links, RELATIONS_CURIE
from moxie.places.importers.helpers import find_type_name
from moxie.transport.services import TransportService
from moxie.core.service import NoConfiguredService, ProviderException
from moxie.places.services import POIService

logger = logging.getLogger(__name__)

RTI_CURIE = "http://moxie.readthedocs.org/en/latest/http_api/rti.html#{type}"


class POIRepresentation(Representation):

    def __init__(self, poi):
        self.poi = poi

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        values = {
            'id': self.poi.id,
            'name': self.poi.name,
            'distance': self.poi.distance,
            'type': self.poi.type,
            'type_name': self.poi.type_name,
        }
        if self.poi.short_name:
            values['short_name'] = self.poi.short_name
        if self.poi.collection_times:
            values['collection_times'] = self.poi.collection_times
        if self.poi.opening_hours:
            values['opening_hours'] = self.poi.opening_hours
        if self.poi.website:
            values['website'] = self.poi.website
        if self.poi.phone:
            values['phone'] = self.poi.phone
        if self.poi.address:
            values['address'] = self.poi.address
        if self.poi.lat and self.poi.lon:
            values['lon'] = self.poi.lon
            values['lat'] = self.poi.lat
        if self.poi.alternative_names:
            values['alternative_names'] = self.poi.alternative_names
        if self.poi.shape:
            values['shape'] = self.poi.shape
        if getattr(self.poi, 'fields', False):
            for k, v in self.poi.fields.items():
                values[k] = v
        return values


class HALPOIRepresentation(POIRepresentation):

    def __init__(self, poi, endpoint, add_parent_children_links=True):
        """HAL+JSON representation of a POI
        :param poi: poi as a domain object
        :param endpoint: endpoint (URL) to represent a POI
        :param add_parent_children_links: (optional) add title (name of POI) to parent and children POIs
        :return HALRepresentation
        """
        super(HALPOIRepresentation, self).__init__(poi)
        self.endpoint = endpoint
        self.add_parent_children_links = add_parent_children_links

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        base = super(HALPOIRepresentation, self).as_dict()
        representation = HALRepresentation(base)
        representation.add_link('self', url_for(self.endpoint, ident=self.poi.id))
        
        try:
            poi_service = POIService.from_context()
        except NoConfiguredService:
            poi_service = None
        if poi_service and self.add_parent_children_links:
            # Merging all IDs (parent and children) into one set to
            # do only one query to the service
            pois_ids = set(self.poi.children)
            if self.poi.parent:
                pois_ids.add(self.poi.parent)
            if pois_ids:
                pois_objects = poi_service.get_places_by_identifiers(pois_ids)
                # ease lookup by having a dict with ID as key
                if pois_objects:
                    pois = dict((poi.id, poi) for poi in pois_objects)
                else:
                    pois = {}

                def add_link(relation, method, identifier):
                    """Add a link w/ or w/o title depending if we found a POI
                    :param relation: link rel (parent or child)
                    :param method: method to apply (add_link or update if it should be an array)
                    :param identifier: ID of the POI for lookup
                    """
                    poi = pois.get(identifier, None)
                    if poi and poi.name:
                        method(relation, url_for(self.endpoint, ident=identifier),
                            title=poi.name, type=poi.type, type_name=poi.type_name)
                    else:
                        method(relation, url_for(self.endpoint, ident=identifier))

                if self.poi.parent:
                    add_link('parent', representation.add_link, self.poi.parent)

                if self.poi.children:
                    for child in self.poi.children:
                        add_link('child', representation.update_link, child)

        try:
            transport_service = TransportService.from_context()
        except NoConfiguredService:
            # Transport service not configured so no RTI information
            logger.warning('No configured Transport service', exc_info=True)
        else:
            try:
                provider = transport_service.get_provider(self.poi)
            except ProviderException:
                logger.debug('No single provider found for: %s' % self.poi.id)
            else:
                representation.add_curie('rti', RTI_CURIE)
                for rtitype, title in provider.provides.items():
                    representation.add_link('rti:%s' % rtitype,
                        url_for('places.rti', ident=self.poi.id, rtitype=rtitype),
                        title=title)
        return representation.as_dict()


class POIsRepresentation(object):

    def __init__(self, search, results, size):
        """Represents a list of search result as JSON
        :param search: search query
        :param results: list of search results
        :param size: size of the results
        """
        self.search = search
        self.results = results
        self.size = size

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self, representation=POIRepresentation):
        """JSON representation of a list of POIs
        :param representation:
        :return dict with the representation as JSON
        """
        return {'query': self.search,
                'size': self.size,
                'results': [representation(r).as_dict() for r in self.results]}


class HALPOISearchRepresentation(POIsRepresentation):

    def __init__(self, search, results, start, count, size, endpoint, types=None, type=None, type_exact=None):
        """Represents a list of search result as HAL+JSON
        :param search: search query
        :param results: list of results
        :param start: int as the first result of the page
        :param count: int as the size of the page
        :param size: int as total size of results
        :param endpoint: endpoint (URL) to represent the search resource
        :param types: (optional) types of the POIs, used for faceting
        :param type: (optional) type of the POIs (if search has been restricted to this type)
        :param type_exact: (optional) exact types of the POIs (if search has been restricted to this exact type)
        """
        super(HALPOISearchRepresentation, self).__init__(search, results, size)
        self.start = start
        self.count = count
        self.size = size
        self.endpoint = endpoint
        self.types = types
        self.type = type
        self.type_exact = type_exact

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        representation = HALRepresentation({
            'query': self.search,
            'size': self.size,
        })
        representation.add_link('self', url_for(self.endpoint, q=self.search, type=self.type, type_exact=self.type_exact,
            start=self.start, count=self.count))
        representation.add_links(get_nav_links(self.endpoint, self.start, self.count, self.size,
            q=self.search, type=self.type, type_exact=self.type_exact))
        representation.add_embed('pois', [HALPOIRepresentation(r, 'places.poidetail').as_dict() for r in self.results])
        if self.types:
            # add faceting links for types
            for facet in self.types:
                representation.update_link('hl:types', url_for(self.endpoint, q=self.search, type=facet),
                    name=facet, title=find_type_name(facet))
        return representation.as_dict()


class HALPOIsRepresentation(POIsRepresentation):

    def __init__(self, results, count, endpoint, pois_ids):
        """Represents a list of POIs as HAL+JSON
        :param results: list of results
        :param count: int as the size of the page
        :param endpoint: endpoint (URL) to represent the search resource
        :param pois_ids: list of POIs IDs in the representation
        """
        super(HALPOIsRepresentation, self).__init__(None, results, count)
        self.count = count
        self.endpoint = endpoint
        self.pois_ids = pois_ids

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        representation = HALRepresentation({
            'count': self.count,
        })
        representation.add_link('self', url_for(self.endpoint, ident=','.join(self.pois_ids)))
        representation.add_embed('pois', [HALPOIRepresentation(r, 'places.poidetail').as_dict() for r in self.results])
        return representation.as_dict()


class TypesRepresentation(Representation):

    def __init__(self, types):
        self.types = types

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self, prefix='/'):
        """Recursively step through the "types" tree, depth-first.

        Prefix is passed as a '/' delimited string of types preceeding the one
        currently being processed.
        """
        types = []
        for k, v in self.types.iteritems():
            values = {'type': k,
                      'type_name': v['name_singular'],
                      'type_name_plural': v['name_plural'],
                      'type_prefixed': prefix + k,
                      }
            if 'description' in v:
                values['description'] = v['description']
            if 'types' in v:
                values.update(TypesRepresentation(v['types']).as_dict(prefix=prefix + k + '/'))
            types.append(values)
        return {'types': types}


class HALTypesRepresentation(TypesRepresentation):

    def __init__(self, types, endpoint):
        super(HALTypesRepresentation, self).__init__(types)
        self.endpoint = endpoint

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        base = super(HALTypesRepresentation, self).as_dict()
        representation = HALRepresentation(base)
        representation.add_link('self', url_for(self.endpoint))
        representation.add_curie('hl', RELATIONS_CURIE)
        representation.add_link('hl:search', url_for('places.search') + "?type={type}")
        return representation.as_dict()


class GeoJsonPointsRepresentation(object):

    def __init__(self, results):
        self.results = results

    def as_dict(self):
        features = []
        for result in self.results:
            if result.shape:
                f = Feature(id=result.id,
                            geometry=wkt_loads(result.shape),
                            properties=self._get_feature_properties(result))
                features.append(f)
            elif result.lat and result.lon:
                # if a result does not have a shape, attempt to
                # fallback on latitude / longitude
                f = Feature(id=result.id,
                            # Point coordinates are in x, y order (longitude, latitude for geographic coordinates)
                            geometry=Point(float(result.lon), float(result.lat)),
                            properties=self._get_feature_properties(result))
                features.append(f)
        return FeatureCollection(features)

    def _get_feature_properties(self, result):
        """Get properties from a POI object
        :param result: POI object
        :return dict
        """
        # only returns the first type atm, was
        # causing issues with some GeoJSON software
        return {'name': result.name,
                'short_name': result.short_name or result.name,     # not ideal but our map software would not be
                'type_name': result.type_name[0],                   # able to do the "fallback" so it has to
                'type': result.type[0]}                             # happen here

    def as_json(self):
        return geojson_dumps(self.as_dict())
