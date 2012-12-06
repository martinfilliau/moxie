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

    def __repr__(self):
        return self.as_dict()


class HalJsonPoiRepresentation(JsonPoiRepresentation):

    def as_dict(self):
        base = super(HalJsonPoiRepresentation, self).as_dict()
        base['_links'] = {}
        base['_links']['self'] = {
                'href': url_for('places.poidetail', ident=self.poi.id)
        }
        if self.poi.parent:
            base['_links']['parent'] = {
                'href': url_for('places.poidetail', ident=self.poi.parent)
            }
        if len(self.poi.children) > 0:
            children = []
            for child in self.poi.children:
                children.append({'href': url_for('places.poidetail', ident=child)})
            base['_links']['child'] = children

        transport_service = TransportService.from_context()
        if transport_service.get_provider(self.poi):
            base['_links']['rti'] = {
                'href': url_for('places.rti', ident=self.poi.id)
            }
        return base

    def __repr__(self):
        return self.as_dict()