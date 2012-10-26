from flask import request, abort, redirect

from moxie.core.views import ServiceView
from .services import OAuth1Service


class Authorize(ServiceView):
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        return redirect(oauth.authorization_url)


class Authorized(ServiceView):
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        if oauth.authorized:
            return {'authorized': True}
        else:
            abort(403)


class VerifyCallback(ServiceView):
    methods = ['POST', 'GET', 'OPTIONS']

    def handle_request(self):
        oauth = OAuth1Service.from_context()
        verifier = request.args['oauth_verifier']
        oauth.verify(verifier)
        if oauth.authorized:
            return {'authorized': True}
        else:
            abort(403)
