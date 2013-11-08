import unittest

from moxie import create_app
from moxie.core.views import accepts
from moxie.authentication import HMACView


class DummyUser(object):
    def __init__(self, secret_key):
        self.secret_key = secret_key


class TestAuthenticatedView(HMACView):

    def handle_request(self):
        print self._check_auth(DummyUser('mysupersecretkey'))
        return {'name': 'Dave'}

    @accepts('foo/bar')
    def basic_response(self, response):
        return 'Hello %s!' % response['name'], 200


class HMACAuthenticationTestCase(unittest.TestCase):
    def setUp(self):
        self.user = DummyUser('mysupersecretkey')
        self.app = create_app()
        self.app.add_url_rule('/test', 'test', TestAuthenticatedView.as_view('test'))

    def test_successful_hmac(self):
        with self.app.test_client() as c:
            rv = c.get('/foo', headers=[('Accept', 'foo/bar')])
            print rv
