from flask import url_for, jsonify

from moxie.core.representations import Representation, HALRepresentation, get_nav_links
from moxie.places.importers.helpers import find_type_name
from moxie.transport.services import TransportService
from moxie.core.service import NoConfiguredService
from moxie.places.services import POIService


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
            'address': self.poi.address,
            'phone': self.poi.phone,
            'website': self.poi.website,
            'opening_hours': self.poi.opening_hours,
            'collection_times': self.poi.collection_times,
        }
        if self.poi.lat and self.poi.lon:
            values['lon'] = self.poi.lon
            values['lat'] = self.poi.lat
        if self.poi.alternative_names:
            values['alternative_names'] = self.poi.alternative_names
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
        if self.poi.parent:
            if poi_service and self.add_parent_children_links:
                parent = poi_service.get_place_by_identifier(self.poi.parent)
            else:
                parent = None
            if parent and parent.name:
                representation.add_link('parent', url_for(self.endpoint, ident=self.poi.parent),
                    title=parent.name, type=parent.type, type_name=parent.type_name)
            else:
                representation.add_link('parent', url_for(self.endpoint, ident=self.poi.parent))

        if len(self.poi.children) > 0:
            # TODO GET with multiple documents, to do at service level
            for child in self.poi.children:
                if poi_service and self.add_parent_children_links:
                    p = poi_service.get_place_by_identifier(child)
                else:
                    p = None
                if p and p.name:
                    representation.update_link('child', url_for(self.endpoint, ident=child), 
                        title=p.name, type=p.type, type_name=p.type_name)
                else:
                    representation.update_link('child', url_for(self.endpoint, ident=child))

        try:
            transport_service = TransportService.from_context()
        except NoConfiguredService:
            # Transport service not configured so no RTI information
            transport_service = None
        if transport_service and transport_service.get_provider(self.poi):
            representation.add_curie('hl', 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}')
            representation.add_link('hl:rti', url_for('places.rti', ident=self.poi.id),
                title="Real-time information")
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


class HALPOIsRepresentation(POIsRepresentation):

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
        super(HALPOIsRepresentation, self).__init__(search, results, size)
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
        representation.add_embed([HALPOIRepresentation(r, 'places.poidetail').as_dict() for r in self.results])
        if self.types:
            # add faceting links for types
            for facet in self.types:
                representation.update_link('hl:types', url_for(self.endpoint, q=self.search, type=facet),
                    name=facet, title=find_type_name(facet))
        return representation.as_dict()


class TypesRepresentation(Representation):

    def __init__(self, types):
        self.types = types

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        types = []
        for k, v in self.types.iteritems():
            values = {'type': k, 'type_name': v['name_singular'],
                    'type_name_plural': v['name_plural']}
            if 'types' in v:
                values.update(TypesRepresentation(v['types']).as_dict())
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
        representation.add_curie('hl', 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}')
        representation.add_link('hl:search', url_for('places.search') + "?type={type}")
        return representation.as_dict()
