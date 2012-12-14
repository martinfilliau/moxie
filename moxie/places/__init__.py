from flask import Blueprint

from moxie.transport.views import RTI
from .views import Search, PoiDetail


def create_blueprint(blueprint_name):
    places_blueprint = Blueprint(blueprint_name, __name__)

    # URL Rules
    places_blueprint.add_url_rule('/search',
            view_func=Search.as_view('search'))

    places_blueprint.add_url_rule('/detail/<path:ident>',
            view_func=PoiDetail.as_view('poidetail'))

    places_blueprint.add_url_rule('/detail/<path:ident>/rti',
            view_func=RTI.as_view('rti'))

    return places_blueprint
