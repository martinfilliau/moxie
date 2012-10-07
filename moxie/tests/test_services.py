import unittest

from moxie.core.provider import Provider
from moxie.core.service import Service, NoProviderFound

class ProvidesAll(Provider):
    def handles(self, doc):
        return True
    def invoke(self, doc):
        return doc


class ProvidesNone(Provider):
    def handles(self, doc):
        return False
    def invoke(self, doc):
        return doc


class TestProvider(Service):
    def annotate_provider(self, doc):
        if self.provider_exists(doc):
            doc['provider_exists'] = True
            return doc
        return doc


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.any_service = TestProvider(providers=[ProvidesAll()])
        self.no_service = TestProvider(providers=[ProvidesNone()])
        self.doc = {'foo': 'bar'}

    def test_provider_exists(self):
        self.assertTrue(self.any_service.provider_exists(self.doc))

    def test_no_provider_exists(self):
        self.assertFalse(self.no_service.provider_exists(self.doc))

    def test_annotated_doc(self):
        doc = self.any_service.annotate_provider(self.doc)
        self.assertTrue(doc['provider_exists'])

    def test_unannotated_doc(self):
        doc = self.no_service.annotate_provider(self.doc)
        with self.assertRaises(KeyError):
            doc['provider_exists']

    def test_invoked_provider_success(self):
        self.assertEqual(self.any_service.invoke_provider(self.doc), self.doc)

    def test_invoked_provider_fail(self):
        with self.assertRaises(NoProviderFound):
            self.no_service.invoke_provider(self.doc)
