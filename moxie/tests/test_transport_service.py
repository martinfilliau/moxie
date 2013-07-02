import unittest

from moxie.transport.providers import TransportRTIProvider
from moxie.transport.services import TransportService
from moxie.core.service import NoSuitableProviderFound, MultipleProvidersFound


class ProvidesAll(TransportRTIProvider):
    def handles(self, doc):
        return True

    def invoke(self, *args):
        return args


class ProvidesAllTwo(ProvidesAll):
    pass


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
        provides_all_twice_conf = {'moxie.tests.test_transport_service.ProvidesAll': {},
                'moxie.tests.test_transport_service.ProvidesAllTwo': {}}
        self.any_service = TestProvider(providers=provides_all_conf)
        self.no_service = TestProvider(providers=provides_none_conf)
        self.many_providers = TestProvider(providers=provides_all_twice_conf)
        self.doc = {'foo': 'bar'}

    def test_get_provider(self):
        self.assertTrue(self.any_service.get_provider(self.doc))

    def test_none_get_provider(self):
        with self.assertRaises(NoSuitableProviderFound):
            self.no_service.get_provider(self.doc)

    def test_multiple_providers(self):
        with self.assertRaises(MultipleProvidersFound):
            self.many_providers.get_provider(self.doc)

    def test_annotated_doc(self):
        doc = self.any_service.annotate_provider(self.doc)
        self.assertTrue(doc['provider_exists'])

    def test_invoked_provider_success(self):
        provider = self.any_service.get_provider(self.doc)
        self.assertEqual(provider(self.doc)[0], self.doc)

    def test_invoked_provider_args_proxy(self):
        provider = self.any_service.get_provider(self.doc)
        args = (self.doc, 1, 2, 3, {1: True})
        self.assertEqual(provider(*args), args)
