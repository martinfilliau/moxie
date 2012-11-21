import unittest

from flask import Blueprint, request
from moxie.core.app import Moxie, BlueprintNotRegistered


class MoxieAppTestCase(unittest.TestCase):

    def setUp(self):
        self.test_app = Moxie('test', '/')
        self.foo_blueprint = Blueprint('foobar', 'foobar')
        self.test_app.register_blueprint(self.foo_blueprint)

    def test_blueprint_not_registered(self):
        with self.assertRaises(BlueprintNotRegistered):
            with self.test_app.blueprint_context('barfoo'):
                pass

    def test_request_context(self):
        with self.test_app.blueprint_context('foobar'):
            self.assertTrue(request)

    def test_request_context_teardown(self):
        with self.test_app.blueprint_context('foobar'):
            self.assertTrue(request)
        self.assertFalse(request)

    def test_blueprint_request(self):
        with self.test_app.blueprint_context('foobar'):
            self.assertEqual(request.blueprint, 'foobar')
