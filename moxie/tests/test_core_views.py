import unittest
from mock import patch
import flask
from datetime import timedelta, datetime

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


class TestExpiringView(TestServiceView):
    expires = timedelta(days=1, minutes=23)


class TestFixedExpiringView(TestServiceView):
    expires = datetime(year=2010, month=10, day=10, hour=23, minute=59, second=59)


class TestMultiInheritance(TestServiceView, TestSecondServiceView):
    pass


class ServiceViewTestCase(unittest.TestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.add_url_rule('/foo', view_func=TestServiceView.as_view('foo'))
        self.app.add_url_rule('/expires', view_func=TestExpiringView.as_view('expires'))
        self.app.add_url_rule('/fixed', view_func=TestFixedExpiringView.as_view('fixed'))

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

    def test_expires_timedelta(self):
        with self.app.test_client() as c:
            with patch('moxie.core.views.datetime') as now_mock:
                now_mock.utcnow.return_value = datetime(2010, 10, 10, 10, 10, 10)
                rv = c.get('/expires', headers=[('Accept', 'foo/bar')])
                self.assertEqual(rv.status_code, 200)
                now = datetime(2010, 10, 10, 10, 10, 10)
                now += TestExpiringView.expires
                expected = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
                self.assertEqual(rv.headers.get('Expires'), expected)
                self.assertEqual(rv.headers.get('Cache-Control'), 'max-age={seconds}'
                                    .format(seconds=int(TestExpiringView.expires.total_seconds())))

    def test_expires_datetime(self):
        with self.app.test_client() as c:
            with patch('moxie.core.views.datetime') as now_mock:
                now_mock.utcnow.return_value = datetime(2010, 10, 10, 23, 59, 00)
                rv = c.get('/fixed', headers=[('Accept', 'foo/bar')])
                self.assertEqual(rv.status_code, 200)
                expected = datetime(2010, 10, 10, 23, 59, 59).strftime("%a, %d %b %Y %H:%M:%S GMT")
                self.assertEqual(rv.headers.get('Expires'), expected)
                self.assertEqual(rv.headers.get('Cache-Control'), 'max-age=59')

    def test_no_expires(self):
        with self.app.test_client() as c:
            rv = c.get('/foo', headers=[('Accept', 'application/json')])
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv.content_type, 'application/json')
            self.assertIsNone(rv.headers.get('Expires', None))
            self.assertIsNone(rv.headers.get('Cache-Control', None))