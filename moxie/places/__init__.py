from flask import Blueprint
from flask.helpers import url_for, make_response

from moxie.transport.views import RTI
from moxie.core.representations import HALRepresentation
from .views import Search, PoiDetail, Types


def create_blueprint(blueprint_name):
    places_blueprint = Blueprint(blueprint_name, __name__)

    places_blueprint.add_url_rule('/', view_func=get_routes)

    places_blueprint.add_url_rule('/search',
            view_func=Search.as_view('search'))

    places_blueprint.add_url_rule('/types',
            view_func=Types.as_view('types'))

    places_blueprint.add_url_rule('/<path:ident>',
            view_func=PoiDetail.as_view('poidetail'))

    places_blueprint.add_url_rule('/<path:ident>/rti',
            view_func=RTI.as_view('rti'))

    return places_blueprint


def get_routes():
    representation = HALRepresentation({})
    representation.add_link('search', url_for('places.search'))
    representation.add_link('types', url_for('places.types'))
    representation.add_link('detail', '/places/{id}', templated=True)   # TODO cannot use url_for because templating
    representation.add_link('rti', '/places/{id}/rti', templated=True)
    response = make_response(representation.as_json(), 200)
    response.headers['Content-Type'] = "application/json"
    return response