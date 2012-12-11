import unittest
import mock

from flask import Blueprint

from moxie import create_app
from moxie.places.representations import HalJsonPoiRepresentation
from moxie.places.domain import POI
from moxie.core.service import Service


class MockTransportServiceNeverProvide(Service):
    def get_provider(self, poi):
        return False


class MockTransportServiceAlwaysProvide(Service):
    def get_provider(self, poi):
        return True


class PlacesRepresentationsTestCase(unittest.TestCase):

    def setUp(self):
        self.test_poi = POI(id=42, name='Test POI', lat=4.2, lon=2.4, type='boat')
        self.app = create_app()
        services = {'foobar': {'MockTransportServiceNeverProvide': {},
                'MockTransportServiceAlwaysProvide': {}}}
        self.app.config['SERVICES'] = services
        bp = Blueprint('foobar', 'foobar')
        self.app.register_blueprint(bp)

    def test_as_dict_no_transport_service(self):
        with self.app.blueprint_context('foobar'):
            poi = HalJsonPoiRepresentation(self.test_poi, 'places.poidetail')
            poi = poi.as_dict()
            self.assertFalse('hl:rti' in poi['_links'])

    def test_as_dict_with_transport_service(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceNeverProvide):
            with self.app.blueprint_context('foobar'):
                poi = HalJsonPoiRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertFalse('hl:rti' in poi['_links'])

    def test_as_dict_with_transport_service_provided(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceAlwaysProvide):
            with self.app.blueprint_context('foobar'):
                poi = HalJsonPoiRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertTrue('hl:rti' in poi['_links'])
