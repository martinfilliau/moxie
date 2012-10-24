import urlparse
import requests
import logging

from moxie.core.service import Service
from requests.auth import OAuth1
from flask import session


logger = logging.getLogger(__name__)


class OAuthCredentials(object):
    def __init__(self, client=None, temporary=None, access=None):
        self._credentials = {
                'client': client,
                'temporary': temporary,
                'access': access
                }

    def __get__(self, instance, owner):
        print instance
        print owner
        session_key = "oath_%s" % instance
        if instance not in self._credentials.keys():
            raise AttributeError()
        credentials = self._credentials[instance]
        if credentials:
            return credentials
        elif session and session_key in session:
            return session[session_key]
        else:
            return None




class OAuth1Service(Service):
    """Enables using 3-legged authentication with OAuth v1 the Moxie client
    handles making actual redirections and user interactions.

    :param oauth_endpoint: URL of the form http://service.foo/oauth/
    """

    def __init__(self, oauth_endpoint, client_identifier, client_secret,
            request_token_path='request_token', access_token_path='access_token',
            authorize_path='authorize'):
        self.oauth_endpoint = oauth_endpoint
        self.client_identifier = unicode(client_identifier)
        self.client_secret = unicode(client_secret)

        # The 3 endpoints used
        self.request_token_path = request_token_path
        self.access_token_path = access_token_path
        self.authorize_path = authorize_path

        self.temporary_token_identifier = None
        self.temporary_token_secret = None
        self.access_token_identifier = None
        self.access_token_secret = None

    def refresh_temporary_credentials(self):
        url = urlparse.urljoin(self.oauth_endpoint, self.request_token_path)
        temp_oa = OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret)
        response = requests.get(url, auth=temp_oa)
        qs = urlparse.parse_qs(response.text)
        self.temporary_token_identifier = unicode(qs['oauth_token'][0])
        self.temporary_token_secret = unicode(qs['oauth_token_secret'][0])
        return self.temporary_token_identifier, self.temporary_token_secret

    @property
    def authorization_url(self, token_param='oauth_token'):
        if not self.temporary_token_identifier:
            self.refresh_temporary_credentials()
        url = urlparse.urljoin(self.oauth_endpoint, self.authorize_path)
        params = {token_param: self.temporary_token_identifier}
        request = requests.Request(url=url, params=params)
        return request.full_url

    def refresh_access_credentials(self, verifier):
        verifier = unicode(verifier)
        url = urlparse.urljoin(self.oauth_endpoint, self.access_token_path)
        access_oa = OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret,
                resource_owner_key=self.temporary_token_identifier,
                resource_owner_secret=self.temporary_token_secret,
                verifier=verifier)
        response = requests.get(url=url, auth=access_oa)
        qs = urlparse.parse_qs(response.text)
        self.access_token_identifier = unicode(qs['oauth_token'][0])
        self.access_token_secret = unicode(qs['oauth_token_secret'][0])
        return self.access_token_identifier, self.access_token_secret

    @property
    def signer(self):
        return OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret,
                resource_owner_key=self.access_token_identifier,
                resource_owner_secret=self.access_token_secret)
