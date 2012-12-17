from flask import url_for, jsonify

from moxie.core.representations import JsonRepresentation, HalJsonRepresentation, get_nav_links
from moxie.transport.services import TransportService
from moxie.core.service import NoConfiguredService
from moxie.places.services import POIService


class JsonPoiRepresentation(JsonRepresentation):

    def __init__(self, poi):
        self.poi = poi

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        return {
            'id': self.poi.id,
            'name': self.poi.name,
            'lat': self.poi.lat,
            'lon': self.poi.lon,
            'distance': self.poi.distance,
            'type': self.poi.type,
            'type_name': self.poi.type_name,
            'address': self.poi.address,
            'phone': self.poi.phone,
            'website': self.poi.website,
            'opening_hours': self.poi.opening_hours,
            'collection_times': self.poi.collection_times,
        }


class HalJsonPoiRepresentation(JsonPoiRepresentation):

    def __init__(self, poi, endpoint):
        """HAL+JSON representation of a POI
        :param poi: poi as a domain object
        :param endpoint: endpoint (URL) to represent a POI
        :return HalJsonRepresentation
        """
        super(HalJsonPoiRepresentation, self).__init__(poi)
        self.endpoint = endpoint

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        base = super(HalJsonPoiRepresentation, self).as_dict()
        links = {'self': {
                    'href': url_for(self.endpoint, ident=self.poi.id)
                }
        }
        try:
            poi_service = POIService.from_context()
        except NoConfiguredService:
            poi_service = None
        if self.poi.parent:
            if poi_service:
                parent = poi_service.get_place_by_identifier(self.poi.parent)
            else:
                parent = None
            links['parent'] = {
                'href': url_for(self.endpoint, ident=self.poi.parent),
            }
            if parent and parent.name:
                links['parent']['title'] = parent.name

        if len(self.poi.children) > 0:
            links['child'] = []
            # TODO GET with multiple documents, to do at service level
            for child in self.poi.children:
                c = {'href': url_for(self.endpoint, ident=child)}
                if poi_service:
                    p = poi_service.get_place_by_identifier(child)
                else:
                    p = None
                if p and p.name:
                    c['title'] = p.name
                links['child'].append(c)

        try:
            transport_service = TransportService.from_context()
        except NoConfiguredService:
            # Transport service not configured so no RTI information
            transport_service = None
        if transport_service and transport_service.get_provider(self.poi):
            links['curie'] = {
                'name': 'hl',
                'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
                'templated': True,
            }
            links['hl:rti'] = {
                'href': url_for('places.rti', ident=self.poi.id),
                'title': 'Real-time information'
            }
        return HalJsonRepresentation(base, links).as_dict()


class JsonPoisRepresentation(object):

    def __init__(self, search, results):
        """Represents a list of search result as JSON
        :param search: search query
        :param results: list of search results
        """
        self.search = search
        self.results = results

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self, representation=JsonPoiRepresentation):
        """JSON representation of a list of POIs
        :param representation:
        :return dict with the representation as JSON
        """
        return {'query': self.search,
                'results': [representation(r).as_dict() for r in self.results]}


class HalJsonPoisRepresentation(JsonPoisRepresentation):

    def __init__(self, search, results, start, count, size, endpoint):
        """Represents a list of search result as HAL+JSON
        :param search: search query
        :param results: list of results
        :param start: int as the first result of the page
        :param count: int as the size of the page
        :param size: int as total size of results
        :param endpoint: endpoint (URL) to represent the search resource
        :return HalJsonRepresentation
        """
        super(HalJsonPoisRepresentation, self).__init__(search, results)
        self.start = start
        self.count = count
        self.size = size
        self.endpoint = endpoint

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        response = {
            'query': self.search,
            'size': self.size,
        }
        pois = [HalJsonPoiRepresentation(r, 'places.poidetail').as_dict() for r in self.results]
        links = {'self': {
                    'href': url_for(self.endpoint, q=self.search)
                }
        }
        links.update(get_nav_links(self.endpoint, self.start, self.count, self.size, q=self.search))
        return HalJsonRepresentation(response, links, {'results': pois }).as_dict()


class JsonTypesRepresentation(JsonRepresentation):

    def __init__(self, types):
        self.types = types

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        types = []
        for k, v in self.types.iteritems():
            values = {'type': k, 'type_name': v['name_singular']}
            if 'types' in v:
                values['types'] = JsonTypesRepresentation(v['types']).as_dict()
            types.append(values)
        return {'types': types }


class HalJsonTypesRepresentation(JsonTypesRepresentation):

    def __init__(self, types, endpoint):
        super(HalJsonTypesRepresentation, self).__init__(types)
        self.endpoint = endpoint

    def as_json(self):
        return jsonify(self.as_dict())

    def as_dict(self):
        base = super(HalJsonTypesRepresentation, self).as_dict()
        links = {'self': {
                    'href': url_for(self.endpoint),
                },
                 'curie': {
                    'name': 'hl',
                    'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
                    'templated': True,
                },
                'hl:search': {
                    'href': url_for('places.search') + "?type={type}"
                }
        }
        return HalJsonRepresentation(base, links).as_dict()