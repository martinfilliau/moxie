from flask import url_for
from moxie.places.domain import POI


class PoiRepresentation(object):

    def __init__(self, poi):
        self.poi = poi

    def as_dict(self):
        return {
            'id': self.poi.id,
            'name': self.poi.name,
            'lat': self.poi.lat,
            'lon': self.poi.lon,
            'type': self.poi.type,
        }

    def __repr__(self):
        return self.as_dict()


class HalPoiRepresentation(PoiRepresentation):

    def as_dict(self):
        base = super(HalPoiRepresentation, self).as_dict()
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

        return base