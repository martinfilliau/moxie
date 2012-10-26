from flask import Blueprint

from .views import Authorized, Authorize, VerifyCallback


def create_blueprint(blueprint_name):
    oauth_blueprint = Blueprint(blueprint_name, __name__)

    # URL Rules
    oauth_blueprint.add_url_rule('/authorized',
            view_func=Authorized.as_view('authorized'))

    oauth_blueprint.add_url_rule('/authorize',
            view_func=Authorize.as_view('authorize'))

    oauth_blueprint.add_url_rule('/verify',
            view_func=VerifyCallback.as_view('verify'))

    return oauth_blueprint
