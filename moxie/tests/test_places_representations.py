import unittest
import mock

from flask import Blueprint

from moxie import create_app
from moxie.transport.providers import TransportRTIProvider
from moxie.places.representations import HALPOIRepresentation, POIRepresentation
from moxie.places.domain import POI
from moxie.places.solr import doc_to_poi
from moxie.core.service import Service, NoSuitableProviderFound, ProviderService


class MockTransportServiceNeverProvide(Service):
    def get_provider(self, poi):
        raise NoSuitableProviderFound()


class MockTransportRTIProvider(TransportRTIProvider):
    provides = {'some-fake-rti': 'Fake RTI'}


class MockTransportRTIProviderHandlesAll(TransportRTIProvider):
    provides = {'all-rti-1': 'All RTI 1'}

    def handles(self, *args, **kwargs):
        return True


class MockTransportRTIProviderHandlesAllTwo(MockTransportRTIProviderHandlesAll):
    provides = {'all-rti-2': 'All RTI 2'}


class MockTransportServiceAlwaysProvide(Service):

    def get_provider(self, poi):
        return MockTransportRTIProvider()


class MockTransportMultiRTIProvider(TransportRTIProvider):
    provides = {'rti1': 'RTI One', 'rti2': 'RTI Two', 'rti3': 'RTI Three'}


class MockTransportServiceAlwaysProvideMulti(Service):

    def get_provider(self, poi):
        return MockTransportMultiRTIProvider()


class MockTransportServiceMultipleProviders(ProviderService):
    pass


class PlacesRepresentationsTestCase(unittest.TestCase):

    def setUp(self):
        self.test_poi = POI(id=42, name='Test POI', lat=4.2, lon=2.4, type='boat')
        self.app = create_app()
        services = {'foobar': {'MockTransportServiceNeverProvide': {},
                'MockTransportServiceAlwaysProvide': {},
                'MockTransportServiceAlwaysProvideMulti': {},
                'MockTransportServiceMultipleProviders': {'providers': {
                    'moxie.tests.test_places_representations.MockTransportRTIProviderHandlesAll': {},
                    'moxie.tests.test_places_representations.MockTransportRTIProviderHandlesAllTwo': {}}},
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

    def test_as_dict_with_many_providers_no_rti(self):
        with mock.patch('moxie.places.representations.TransportService', new=MockTransportServiceMultipleProviders):
            with self.app.blueprint_context('foobar'):
                poi = HALPOIRepresentation(self.test_poi, 'places.poidetail')
                poi = poi.as_dict()
                self.assertFalse(any([link.startswith('rti') for link in poi['_links']]))

    def test_poi_no_meta(self):
        poi = POI('my:id', 'Name', '/type')
        self.assertFalse(getattr(poi, 'fields', False))

        doc = {'id': 'my:id', 'name': 'Name', 'type': '/type'}
        poi = doc_to_poi(doc)
        self.assertIsNone(getattr(poi, 'fields', None))

    def test_doc_poi_meta(self):
        doc = {'id': 'my:id', 'name': 'Name', 'type': '/type', 'my_meta_test': 'test', 'my_meta_test_one': 'two'}
        poi = doc_to_poi(doc, fields_key='my_meta_')
        self.assertEqual(poi.fields['test'], 'test')
        self.assertEqual(poi.fields['test_one'], 'two')

        doc = {'id': 'my:id', 'name': 'Name', 'type': '/type', '_test': 'test', '_test_one': 'two'}
        poi = doc_to_poi(doc, fields_key='_')
        self.assertEqual(poi.fields['test'], 'test')
        self.assertEqual(poi.fields['test_one'], 'two')

        representation = POIRepresentation(poi)
        self.assertEqual(representation.as_dict()['test'], 'test')