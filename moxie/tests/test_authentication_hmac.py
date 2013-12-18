import unittest

from moxie import create_app
from moxie.core.views import accepts
from moxie.authentication import HMACView


class DummyUser(object):
    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.name = 'Dave'


class TestAuthenticatedView(HMACView):

    def handle_request(self):
        one_user = DummyUser('mysupersecretkey')
        if self.check_auth(one_user.secret_key):
            return {'name': one_user.name}

    @accepts('foo/bar')
    def basic_response(self, response):
        return 'Hello %s!' % response['name'], 200


class HMACAuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.user = DummyUser('mysupersecretkey')
        self.app = create_app()
        self.app.add_url_rule('/test', 'test', TestAuthenticatedView.as_view('test'))

    def test_successful_hmac(self):
        headers = [
            ('Accept', 'foo/bar'),
            ('Date', 'Wednesday'),
            ('X-HMAC-Nonce', 'foobarbaz'),
            ('Authorization', '668db85d1dff6718d778454fc8c1d368a906f675'),
        ]
        with self.app.test_client() as c:
            rv = c.get('/test', headers=headers)
            self.assertEqual(rv.status_code, 200)

    def test_hmac_signature_mismatch(self):
        headers = [
            ('Accept', 'foo/bar'),
            ('Date', 'Wednesday'),
            ('X-HMAC-Nonce', 'foobarbaz'),
            ('Authorization', 'wrong-wrong'),
        ]
        with self.app.test_client() as c:
            rv = c.get('/test', headers=headers)
            self.assertEqual(rv.status_code, 401)

    def test_missing_header(self):
        headers = [
            ('Accept', 'foo/bar'),
            ('Date', 'Wednesday'),
            ('Authorization', 'wrong-wrong'),
        ]
        with self.app.test_client() as c:
            rv = c.get('/test', headers=headers)
            self.assertEqual(rv.status_code, 401)
            self.assertIn("missing header", rv.headers['WWW-Authenticate'])
