from flask import Blueprint

from moxie.transport.views import RTI
from .views import Search, PoiDetail, Types


def create_blueprint(blueprint_name):
    places_blueprint = Blueprint(blueprint_name, __name__)

    places_blueprint.add_url_rule('/search',
            view_func=Search.as_view('search'))

    places_blueprint.add_url_rule('/types',
            view_func=Types.as_view('types'))

    places_blueprint.add_url_rule('/<path:ident>',
            view_func=PoiDetail.as_view('poidetail'))

    places_blueprint.add_url_rule('/<path:ident>/rti',
            view_func=RTI.as_view('rti'))

    return places_blueprint
