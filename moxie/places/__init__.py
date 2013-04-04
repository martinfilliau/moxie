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
    path = 'places'     # TODO should be passed as argument?
    representation = HALRepresentation({})
    representation.add_curie('hl', 'http://moxie.readthedocs.org/en/latest/http_api/places.html#{rel}')
    representation.add_link('self', '/{bp}'.format(bp=path))
    representation.add_link('hl:search', '/{bp}/search?q={{q}}'.format(bp=path),
                            templated=True, title='Search')
    representation.add_link('hl:types', url_for('{bp}.types'.format(bp=path)), title='List of types')
    representation.add_link('hl:detail', '/{bp}/{{id}}'.format(bp=path),
                            templated=True, title='POI detail')
    representation.add_link('hl:rti', '/{bp}/{{id}}/rti'.format(bp=path),
                            templated=True, title='POI Real-Time Information')
    response = make_response(representation.as_json(), 200)
    response.headers['Content-Type'] = "application/json"
    return response