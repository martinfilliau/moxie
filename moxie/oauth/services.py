import urlparse
import requests
import logging

from moxie.core.service import Service
from requests_oauthlib import OAuth1
from flask import request, session


logger = logging.getLogger(__name__)


class OAuthCredential(object):
    """Descriptor for caching our OAuth credentials in a user session.
    Only if one is available. Caches on the :py:class:`OAuth1Service`
    object in an attribute named by :py:attr:`OAuthCredential.credential_store`
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
        elif request and self.key in session:
            creds = session[self.key]
            store[self.key] = creds
            return creds
        else:
            return None, None

    def __set__(self, instance, value):
        store = self.get_credential_store(instance)
        store[self.key] = value
        logger.debug("Setting {key}: {value}".format(key=self.key, value=value))
        if request:
            session[self.key] = value
            logger.debug(session)


def __delete__(self, instance):
        store = self.get_credential_store(instance)
        if self.key in store:
            del store[self.key]
        if request and self.key in session:
            del session[self.key]


class OAuth1Service(Service):
    """Enables using 3-legged authentication with OAuth v1 the Moxie client
    handles making actual redirections and user interactions.

    .. note:: OAuth1 terminology varies, between the original spec and the
       formal `RFC`_ the terminology is far from consistent.
       We have tried to follow the `RFC`_ where possible however, we use
       ``requests.auth`` which uses differing terminology.

    .. _RFC: http://tools.ietf.org/html/rfc5849#page-5

    :param oauth_endpoint: URL of the form http://service.foo/oauth/
    :param client_identifier: Client token identifier.
    :param client_secret: Shared secret paired with the above identifier.
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
    def authorized(self):
        """Returns ``True`` if resource owner credentials are available."""
        resource_owner_key, resource_owner_secret = self.access_credentials
        if resource_owner_key and resource_owner_secret:
            return True
        else:
            return False

    def refresh_temporary_credentials(self, callback_uri=None):
        """Requests new temporary credentials from the OAuth server.

        :param callback_uri: the request is (optionally) signed with this
               URL and the user should be redirected back here upon
               completing the OAuth workflow.
        """
        url = urlparse.urljoin(self.oauth_endpoint, self.request_token_path)
        temp_oa = OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret, callback_uri=callback_uri)
        response = requests.get(url, auth=temp_oa)
        qs = urlparse.parse_qs(response.text)
        self.temporary_credentials = (unicode(qs['oauth_token'][0]),
                unicode(qs['oauth_token_secret'][0]))
        return self.temporary_credentials

    def authorization_url(self, token_param='oauth_token', callback_uri=None):
        """Convenience method to both generate a new temporary credential and
        return a URL where a user can continue the OAuth workflow
        authentication. Always generates new temporary credentials.
        """
        token, _ = self.refresh_temporary_credentials(callback_uri)
        url = urlparse.urljoin(self.oauth_endpoint, self.authorize_path)
        params = {token_param: token}
        request = requests.Request(url=url, params=params)
        return request.full_url

    def verify(self, verifier):
        """Sends a signed request to the OAuth server trading in your temporary
        credentials for *access credentials* these can be used to sign requests
        for the users protected resources.

        :param verifier: Verification code passed from the OAuth server through
               the users OAuth workflow. Can be either passed in a redirect or
               the user could be instructed to copy it over.
        """
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
        logger.debug(qs)
        self.access_credentials = (unicode(qs['oauth_token'][0]),
                unicode(qs['oauth_token_secret'][0]))
        return self.access_credentials

    @property
    def signer(self):
        """Returns a :py:class:`OAuth1` object which can be used to sign
        http requests bound for protected resources::

            oa = OAuth1Service('http://private.foo/oauth', 'private', 'key')
            requests.get('http://private.foo/private_resource', auth=oa.signer)
        """
        resource_owner_key, resource_owner_secret = self.access_credentials
        return OAuth1(client_key=self.client_identifier,
                client_secret=self.client_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret)
