from flask import url_for

from moxie.transport.services import TransportService


class JsonPoiRepresentation(object):

    def __init__(self, poi):
        self.poi = poi

    def as_dict(self):
        return {
            'id': self.poi.id,
            'name': self.poi.name,
            'lat': self.poi.lat,
            'lon': self.poi.lon,
            'type': self.poi.type_name,
        }


class HalJsonPoiRepresentation(JsonPoiRepresentation):

    def __init__(self, poi, endpoint):
        super(HalJsonPoiRepresentation, self).__init__(poi)
        self.endpoint = endpoint

    def as_dict(self):
        base = super(HalJsonPoiRepresentation, self).as_dict()
        base['_links'] = {}
        base['_links']['self'] = {
                'href': url_for(self.endpoint, ident=self.poi.id)
        }
        if self.poi.parent:
            base['_links']['parent'] = {
                'href': url_for(self.endpoint, ident=self.poi.parent)
            }
        if len(self.poi.children) > 0:
            children = []
            for child in self.poi.children:
                children.append({'href': url_for(self.endpoint, ident=child)})
            base['_links']['child'] = children

        transport_service = TransportService.from_context()
        if transport_service.get_provider(self.poi):
            base['_links']['curie'] = {
                'name': 'hl',
                'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
                'templated': True,
            }
            base['_links']['hl:rti'] = {
                'href': url_for('places.rti', ident=self.poi.id),
                'title': 'Real-time information'
            }
        return base


class JsonPoisRepresentation(object):

    def __init__(self, search, results, start, count, size):
        """Represents a list of search result as JSON
        :param search: search query
        :param results: list of search results
        :param start: int as the first result of the page
        :param count: int as the size of the page
        :param size: int as total size of results
        """
        self.search = search
        self.results = results
        self.start = start
        self.count = count
        self.size = size

    def as_dict(self, representation=JsonPoiRepresentation):
        """JSON representation of a list of POIs
        :param representation:
        :return dict with the representation as JSON
        """
        repr = {'query': self.search }
        res = []
        for r in self.results:
            res.append(representation(r).as_dict())
        repr['results'] = res
        return repr


class HalJsonPoisRepresentation(JsonPoisRepresentation):

    def __init__(self, search, results, start, count, size, endpoint):
        super(HalJsonPoisRepresentation, self).__init__(search, results, start, count, size)
        self.endpoint = endpoint

    def as_dict(self):
        response = {
            'query': self.search,
            'size': self.size,
        }
        res = []
        for r in self.results:
            res.append(HalJsonPoiRepresentation(r, 'places.poidetail').as_dict())
        response['_embedded'] = {'results': res }
        response['_links'] = {}
        response['_links']['self'] = {
            'href': url_for(self.endpoint, q=self.search)
        }
        response['_links']['curie'] = {
            'name': 'hl',
            'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
            'templated': True,
        }
        response['_links']['hl:last'] = {
            'href': url_for(self.endpoint, q=self.search, start=self.size-self.count, count=self.count)
        }
        response['_links']['hl:first'] = {
            'href': url_for(self.endpoint, q=self.search, count=self.count)
        }
        if self.size > self.start+self.count:
            response['links']['hl:next'] = {
                'href': url_for(self.endpoint, q=self.search, start=self.start+self.count, count=self.count)
            }
        if self.start > 0 and self.size > self.start+self.count:
            response['links']['hl:prev'] = {
                'href': url_for(self.endpoint, q=self.search, start=self.start-self.count, count=self.count)
            }

        return response
