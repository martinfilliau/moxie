import unittest

from flask import Blueprint
from moxie import create_app
from moxie.core.service import Service, NoConfiguredService


class TestProvider(Service):
    pass


class ArgService(Service):
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        services = {'foobar': {'TestProvider': {}},
                'barfoo': {'TestProvider': {}},
                'blueblue': {'ArgService': {'mox': 'ie'}},
                }
        self.app.config['SERVICES'] = services
        bp = Blueprint('foobar', 'foobar')
        self.app.register_blueprint(bp)

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
            self.assertEqual(argserv.kwargs, {'mox': 'ie'})

    def test_service_blueprint_context(self):
        with self.app.blueprint_context('foobar'):
            TestProvider.from_context()

    def test_service_blueprint_context_not_configured(self):
        with self.app.blueprint_context('foobar'):
            with self.assertRaises(NoConfiguredService):
                ArgService.from_context()
