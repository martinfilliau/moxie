import logging

from flask import request, redirect

from moxie.core.views import ServiceView
from .services import OAuth1Service

logger = logging.getLogger(__name__)


class Authorize(ServiceView):
    """Returns a 302 to the OAuth server to begin the OAuth workflow"""
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        callback_uri = request.values.get('callback_uri', None)
        if callback_uri:
            callback_uri = unicode(callback_uri)
        redirection_url = oauth.authorization_url(callback_uri=callback_uri)
        return redirect(redirection_url)


class Authorized(ServiceView):
    methods = ['GET', 'OPTIONS']

    cors_allow_credentials = True

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        if oauth.authorized:
            return {'authorized': True}
        else:
            return {'authorized': False}


class VerifyCallback(ServiceView):
    methods = ['POST', 'GET', 'OPTIONS']

    cors_allow_credentials = True

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        verifier = request.args['oauth_verifier']
        oauth.verify(verifier)
        logger.debug("Verifier {verifier} auth status: {auth_status}"
            .format(verifier=verifier, auth_status=oauth.authorized))
        if oauth.authorized:
            return {'authorized': True}
        else:
            return {'authorized': False}
