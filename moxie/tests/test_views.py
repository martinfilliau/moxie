import unittest
import flask

from moxie.core.views import register_mimetype, ServiceView


class RegisterMimeTypeTestCase(unittest.TestCase):

    def test_register_mimetype(self):
        @register_mimetype('foo/bar')
        def test_func():
            return 'Hello World!'
        self.assertEqual(test_func.mimetypes, ['foo/bar'])

    def test_registering_multiple_mimetypes(self):
        @register_mimetype('foo/bar')
        @register_mimetype('text/html')
        @register_mimetype('bar/baz')
        def test_func():
            return 'Hello World!'
        self.assertEqual(test_func.mimetypes,
                ['bar/baz', 'text/html', 'foo/bar'])


class TestServiceView(ServiceView):
    @register_mimetype('foo/bar')
    def basic_response(self):
        return 'Hello World!', 200

    @register_mimetype('foo/json')
    def json_response(self):
        return flask.jsonify({'Hello': 'World'})


class ServiceViewTestCase(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.add_url_rule('/foo', view_func=TestServiceView.as_view('foo'))

    def test_service_response(self):
        sv = TestServiceView()
        self.assertEqual(sv.service_responses['foo/bar'], sv.basic_response)

    def test_not_acceptable_request(self):
        with self.app.test_client() as c:
            rv = c.get('/foo', headers=[('Accept', 'fail/ure')])
            self.assertEqual(rv.status_code, 406)

    def test_working_response(self):
        with self.app.test_client() as c:
            rv = c.get('/foo', headers=[('Accept', 'foo/bar')])
            self.assertEqual(rv.status_code, 200)

    def test_working_response_json(self):
        with self.app.test_client() as c:
            rv = c.get('/foo', headers=[('Accept', 'foo/json')])
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv.content_type, 'application/json')
