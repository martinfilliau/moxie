import unittest

from moxie import create_app
from moxie.core.provider import Provider
from moxie.core.service import Service, NoConfiguredService


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
        if self.get_provider(doc):
            doc['provider_exists'] = True
            return doc
        return doc


class ArgService(Service):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.any_service = TestProvider(providers=[ProvidesAll()])
        self.no_service = TestProvider(providers=[ProvidesNone()])
        self.doc = {'foo': 'bar'}
        self.app = create_app()
        services = {'foobar': {'TestProvider': ([], {})},
                'barfoo': {'TestProvider': ([], {})},
                'blueblue': {'ArgService': ([1, 2, 3], {'mox': 'ie'})},
                }
        self.app.config['SERVICES'] = services

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

    def test_service_config_missing(self):
        with self.app.app_context():
            with self.assertRaises(NoConfiguredService):
                TestProvider.from_context(blueprint_name='blueblue')

    def test_service_app_context_cache(self):
        with self.app.app_context():
            tp = TestProvider.from_context(blueprint_name='foobar')
            tp2 = TestProvider.from_context(blueprint_name='foobar')
            self.assertEqual(tp, tp2)

    def test_service_app_context_cache_different_blueprint(self):
        with self.app.app_context():
            tp = TestProvider.from_context(blueprint_name='foobar')
            tp2 = TestProvider.from_context(blueprint_name='barfoo')
            self.assertNotEqual(tp, tp2)

    def test_service_configured_args(self):
        with self.app.app_context():
            argserv = ArgService.from_context(blueprint_name='blueblue')
            self.assertEqual(argserv.args, (1, 2, 3))
            self.assertEqual(argserv.kwargs, {'mox': 'ie'})
