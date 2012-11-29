from flask import request, redirect

from moxie.core.views import ServiceView
from .services import OAuth1Service


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
        if oauth.authorized:
            return {'authorized': True}
        else:
            return {'authorized': False}
