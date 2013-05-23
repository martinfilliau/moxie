import unittest
import flask

from moxie.core.views import accepts, ServiceView


class AcceptsMimeTypeTestCase(unittest.TestCase):

    def test_accepts(self):
        @accepts('foo/bar')
        def test_func():
            return 'Hello World!'
        self.assertEqual(test_func.mimetypes, ['foo/bar'])

    def test_registering_multiple_mimetypes(self):
        @accepts('foo/bar', 'text/html', 'bar/baz')
        def test_func():
            return 'Hello World!'
        self.assertEqual(set(test_func.mimetypes),
                set(['bar/baz', 'text/html', 'foo/bar']))


class TestServiceView(ServiceView):

    def handle_request(self):
        return {'name': 'Dave'}

    @accepts('foo/bar')
    def basic_response(self, response):
        return 'Hello %s!' % response['name'], 200


class TestSecondServiceView(ServiceView):

    def handle_request(self):
        return {'name': 'Fred'}

    @accepts('foo/bar')
    def basic_response(self, response):
        return 'Hello %s!' % response['name'], 200


class TestInheritedServiceView(TestServiceView):
    @accepts('foo/bar')
    def foobar(self, response):
        return "foobar!"


class TestMultiInheritance(TestServiceView, TestSecondServiceView):
    pass


class ServiceViewTestCase(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.add_url_rule('/foo', view_func=TestServiceView.as_view('foo'))

    def test_service_response(self):
        sv = TestServiceView()
        #  im_func gets to the actual function of the unbound method
        self.assertEqual(sv.service_responses['foo/bar'], sv.basic_response.im_func)

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
            rv = c.get('/foo', headers=[('Accept', 'application/json')])
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv.content_type, 'application/json')

    def test_inherited_service_response_override(self):
        sv = TestInheritedServiceView()
        self.assertNotEqual(sv.service_responses['foo/bar'], sv.basic_response.im_func)
        self.assertEqual(sv.service_responses['foo/bar'], sv.foobar.im_func)

    def test_multi_inheritance_service_response(self):
        """This test tells us in the case of a multi-inheritance service view the bases
        will be evaluated left to right. In this case the TestSecondServiceView overrides
        the previously registered response for 'foo/bar' on TestServiceView.
        """
        sv = TestMultiInheritance()
        self.assertEqual(sv.service_responses['foo/bar'], TestSecondServiceView.basic_response.im_func)
        self.assertNotEqual(sv.service_responses['foo/bar'], TestServiceView.basic_response.im_func)
