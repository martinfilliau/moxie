from flask import Blueprint

from .views import Search, PoiDetail, RTI


def create_blueprint(blueprint_name):
    places_blueprint = Blueprint(blueprint_name, __name__)

    # URL Rules
    places_blueprint.add_url_rule('/search',
            view_func=Search.as_view('search'))

    places_blueprint.add_url_rule('/<path:ident>',
            view_func=PoiDetail.as_view('poidetail'))

    places_blueprint.add_url_rule('/<path:ident>/rti',
            view_func=RTI.as_view('rti'))

    return places_blueprint
