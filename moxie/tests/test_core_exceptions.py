import unittest
import flask
import json

from moxie.core.views import ServiceView, accepts
from moxie.core.exceptions import NotFound


class TestServiceView(ServiceView):

    @accepts('application/json')
    def basic_response(self, response):
        raise NotFound()


class TestExceptionServiceView(ServiceView):

    @accepts('application/json')
    def basic_response(self, response):
        return response

    def handle_request(self):
        raise NotFound()


class AbortContentNegotiation(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.add_url_rule('/test', view_func=TestServiceView.as_view('test'))
        self.app.add_url_rule('/test2', view_func=TestExceptionServiceView.as_view('test2'))

    def test_accept_json(self):
        with self.app.test_client() as c:
            rv = c.get('/test', headers=[('Accept', 'application/json')])
            self.assertEqual(rv.status_code, 404)
            self.assertEqual(rv.content_type, 'application/json')
            data = json.loads(rv.data)
            self.assertIn('description', data)

    def test_exception_accept_json(self):
        with self.app.test_client() as c:
            rv = c.get('/test2', headers=[('Accept', 'application/json')])
            self.assertEqual(rv.status_code, 404)
            self.assertEqual(rv.content_type, 'application/json')
            data = json.loads(rv.data)
            self.assertIn('description', data)