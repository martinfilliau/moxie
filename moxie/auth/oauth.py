import urlparse
import requests
import logging

from moxie.core.service import Service
from requests.auth import OAuth1
from flask import session


logger = logging.getLogger(__name__)


class OAuthCredential(object):
    """Descriptor for caching our OAuth credentials in a user session.
    Only if one is available. Caches to the :py:class:`OAuth1Service`
    object in an attribute named :py:attr:`OAuthCredential.credential_store`.
    """
    credential_store = '_credentials'

    def __init__(self, key):
        self.key = 'oauth_%s' % key

    def get_credential_store(self, instance):
        if not hasattr(instance, self.credential_store):
            setattr(instance, self.credential_store, dict())
        return getattr(instance, self.credential_store)

    def __get__(self, instance, owner):
        store = self.get_credential_store(instance)
        if self.key in store:
            return store[self.key]
        elif session and self.key in session:
            creds = session[self.key]
            store[self.key] = creds
            return creds
        else:
            return None, None

    def __set__(self, instance, value):
        store = self.get_credential_store(instance)
        store[self.key] = value
        if session:
            session[self.key] = value

    def __delete__(self, instance):
        store = self.get_credential_store(instance)
        if self.key in store:
            del store[self.key]
        if session and self.key in session:
            del session[self.key]


class OAuth1Service(Service):
    """Enables using 3-legged authentication with OAuth v1 the Moxie client
    handles making actual redirections and user interactions.

    :param oauth_endpoint: URL of the form http://service.foo/oauth/
    """

    temporary_credentials = OAuthCredential('temporary')
    access_credentials = OAuthCredential('access')

    def __init__(self, oauth_endpoint, client_identifier, client_secret,
            request_token_path='request_token',
            access_token_path='access_token',
            authorize_path='authorize'):
        self.oauth_endpoint = oauth_endpoint
        self.client_identifier = unicode(client_identifier)
        self.client_secret = unicode(client_secret)

        # The 3 endpoints used
        self.request_token_path = request_token_path
        self.access_token_path = access_token_path
        self.authorize_path = authorize_path

    @property
    def authenticated(self):
        resource_owner_key, resource_owner_secret = self.access_credentials
        if resource_owner_key and resource_owner_secret:
            return True
        else:
            return False

    def refresh_temporary_credentials(self):
        url = urlparse.urljoin(self.oauth_endpoint, self.request_token_path)
        temp_oa = OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret)
        response = requests.get(url, auth=temp_oa)
        qs = urlparse.parse_qs(response.text)
        self.temporary_credentials = (unicode(qs['oauth_token'][0]),
                unicode(qs['oauth_token_secret'][0]))
        return self.temporary_credentials

    @property
    def authorization_url(self, token_param='oauth_token'):
        temporary_identifier, _ = self.temporary_credentials
        if not temporary_identifier:
            temporary_identifier, _ = self.refresh_temporary_credentials()
        url = urlparse.urljoin(self.oauth_endpoint, self.authorize_path)
        params = {token_param: temporary_identifier}
        request = requests.Request(url=url, params=params)
        return request.full_url

    def verify(self, verifier):
        verifier = unicode(verifier)
        url = urlparse.urljoin(self.oauth_endpoint, self.access_token_path)
        resource_owner_key, resource_owner_secret = self.temporary_credentials
        access_oa = OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier)
        response = requests.get(url=url, auth=access_oa)
        qs = urlparse.parse_qs(response.text)
        self.access_credentials = (unicode(qs['oauth_token'][0]),
                unicode(qs['oauth_token_secret'][0]))
        return self.access_credentials

    @property
    def signer(self):
        """Returns a :py:class:`OAuth1` object which can be used to sign
        http requests bound for protected resources:

            oa = OAuth1Service('http://private.foo/oauth', 'private', 'key')
            requests.get('http://private.foo/private_resource', auth=oa.signer)
        """
        resource_owner_key, resource_owner_secret = self.access_credentials
        return OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret)
