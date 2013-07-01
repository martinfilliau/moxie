import unittest
import mock

from flask import Blueprint

from moxie import create_app
from moxie.transport.providers import TransportRTIProvider
from moxie.places.representations import HALPOIRepresentation
from moxie.places.domain import POI
from moxie.core.service import Service


class MockTransportServiceNeverProvide(Service):
    def get_provider(self, poi):
        return False


class MockTransportRTIProvider(TransportRTIProvider):
    provides = {'some-fake-rti': 'Fake RTI'}


class MockTransportServiceAlwaysProvide(Service):

    def get_provider(self, poi):
        return MockTransportRTIProvider()


class MockTransportMultiRTIProvider(TransportRTIProvider):
    provides = {'rti1': 'RTI One', 'rti2': 'RTI Two', 'rti3': 'RTI Three'}


class MockTransportServiceAlwaysProvideMulti(Service):

    def get_provider(self, poi):
        return MockTransportMultiRTIProvider()


class PlacesRepresentationsTestCase(unittest.TestCase):

    def setUp(self):
        self.test_poi = POI(id=42, name='Test POI', lat=4.2, lon=2.4, type='boat')
        self.app = create_app()
        services = {'foobar': {'MockTransportServiceNeverProvide': {},
                'MockTransportServiceAlwaysProvide': {},
                'MockTransportServiceAlwaysProvideMulti': {},
                }}
        self.app.config['SERVICES'] = services
        bp = Blueprint('foobar', 'foobar')
        self.app.register_blueprint(bp)

    def test_as_dict_no_transport_service(self):
        with self.app.blueprint_context('foobar'):
            poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
            poi = poi.as_dict()
            self.assertFalse('hl:rti' in poi['_links'])

    def test_as_dict_with_transport_service(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceNeverProvide):
            with self.app.blueprint_context('foobar'):
                poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                # Test we don't have any links starting with 'rti:'
                self.assertFalse(any([link.startswith('rti') for link in poi['_links']]))

    def test_as_dict_with_transport_service_provided(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceAlwaysProvide):
            with self.app.blueprint_context('foobar'):
                poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertTrue('rti:some-fake-rti' in poi['_links'])

    def test_as_dict_with_transport_service_provided_multiple_rti(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceAlwaysProvideMulti):
            with self.app.blueprint_context('foobar'):
                poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertTrue('rti:rti1' in poi['_links'])
                self.assertTrue('rti:rti2' in poi['_links'])
                self.assertTrue('rti:rti3' in poi['_links'])

    def test_as_dict_with_transport_service_rti_titles(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceAlwaysProvide):
            with self.app.blueprint_context('foobar'):
                poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertTrue(poi['_links']['rti:some-fake-rti']['title'] == 'Fake RTI')
