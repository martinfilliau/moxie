import unittest, json

from moxie.core.app import Moxie
from moxie.core.views import ServiceView


class TestCORSWithCredentials(ServiceView):

    cors_allow_headers = 'X-DAVE'
    cors_allow_credentials = True
    cors_max_age = 20
    methods = ['GET', 'OPTIONS', 'PUT']

    def handle_request(self):
        return {'name': 'Dave'}


class TestCORSWithoutCredentials(TestCORSWithCredentials):
    cors_allow_credentials = False


class CORSViewsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = Moxie(__name__)
        self.app.config['DEFAULT_ALLOW_ORIGINS'] = ['foo.domain']
        self.app.add_url_rule('/creds', view_func=TestCORSWithCredentials.as_view('creds'))
        self.app.add_url_rule('/nocreds', view_func=TestCORSWithoutCredentials.as_view('nocreds'))

    def test_credential_true(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.headers['Access-Control-Allow-Credentials'], 'true')

    def test_credential_allow_methods(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(set([m.strip() for m in rv.headers['Access-Control-Allow-Methods'].split(',')]), set(['PUT', 'GET', 'OPTIONS', 'HEAD']))

    def test_credential_allow_headers(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.headers['Access-Control-Allow-Headers'], "X-DAVE")

    def test_credential_max_age(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.headers['Access-Control-Max-Age'], "20")

    def test_credential_echo_origin(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.headers['Access-Control-Allow-Origin'], 'foo.domain')

    def test_credential_bad_origin(self):
        with self.app.test_client() as c:
            rv = c.open('/creds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foobar.domain')])
            self.assertEqual(rv.status_code, 400)

    def test_without_creds_wildcard(self):
        with self.app.test_client() as c:
            rv = c.get('/nocreds', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.headers['Access-Control-Allow-Origin'], '*')

    def test_preflight_content(self):
        with self.app.test_client() as c:
            rv = c.open('/nocreds', method='OPTIONS', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            self.assertEqual(rv.data, '')

    def test_actual_content(self):
        with self.app.test_client() as c:
            rv = c.get('/nocreds', headers=[('Accept', 'application/json'), ('Origin', 'foo.domain')])
            data = json.loads(rv.data)
            self.assertEqual(data['name'], 'Dave')
