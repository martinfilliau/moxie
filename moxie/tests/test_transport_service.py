import unittest

from moxie.transport.providers import TransportRTIProvider
from moxie.transport.services import TransportService


class ProvidesAll(TransportRTIProvider):
    def handles(self, doc):
        return True

    def invoke(self, doc):
        return doc


class ProvidesNone(TransportRTIProvider):
    def handles(self, doc):
        return False

    def invoke(self, doc):
        return doc


class TestProvider(TransportService):
    def annotate_provider(self, doc):
        if self.get_provider(doc):
            doc['provider_exists'] = True
            return doc
        return doc


class TransportServiceTest(unittest.TestCase):

    def setUp(self):
        provides_all_conf = {'moxie.tests.test_transport_service.ProvidesAll': {}}
        provides_none_conf = {'moxie.tests.test_transport_service.ProvidesNone': {}}
        self.any_service = TestProvider(providers=provides_all_conf)
        self.no_service = TestProvider(providers=provides_none_conf)
        self.doc = {'foo': 'bar'}

    def test_get_provider(self):
        self.assertTrue(self.any_service.get_provider(self.doc))

    def test_none_get_provider(self):
        self.assertEqual(None, self.no_service.get_provider(self.doc))

    def test_annotated_doc(self):
        doc = self.any_service.annotate_provider(self.doc)
        self.assertTrue(doc['provider_exists'])

    def test_unannotated_doc(self):
        doc = self.no_service.annotate_provider(self.doc)
        with self.assertRaises(KeyError):
            doc['provider_exists']

    def test_invoked_provider_success(self):
        provider = self.any_service.get_provider(self.doc)
        self.assertEqual(provider(self.doc), self.doc)
