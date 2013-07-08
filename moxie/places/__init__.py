from flask import Blueprint, request
from flask.helpers import make_response

from moxie.transport.views import RTI, ParkAndRides
from moxie.core.representations import HALRepresentation
from .views import Search, PoiDetail, Types

PLACES_CURIE = 'http://moxie.readthedocs.org/en/latest/http_api/places.html#{rel}'


def create_blueprint(blueprint_name, conf):
    places_blueprint = Blueprint(blueprint_name, __name__, **conf)

    places_blueprint.add_url_rule('/', view_func=get_routes)

    places_blueprint.add_url_rule('/search',
            view_func=Search.as_view('search'))

    places_blueprint.add_url_rule('/types',
            view_func=Types.as_view('types'))

    places_blueprint.add_url_rule('/<path:ident>',
            view_func=PoiDetail.as_view('poidetail'))

    places_blueprint.add_url_rule('/<path:ident>/rti/<path:rtitype>',
            view_func=RTI.as_view('rti'))

    places_blueprint.add_url_rule('/transport/park-and-rides',
            view_func=ParkAndRides.as_view('p-r'))      # TODO should be in the Transport blueprint

    return places_blueprint


def get_routes():
    path = request.path
    representation = HALRepresentation({})
    representation.add_curie('hl', PLACES_CURIE)
    representation.add_link('self', '{bp}'.format(bp=path))
    representation.add_link('hl:search', '{bp}search?q={{q}}'.format(bp=path),
                            templated=True, title='Search')
    representation.add_link('hl:types', '{bp}types'.format(bp=path),
            title='List of types')
    representation.add_link('hl:detail', '{bp}{{id}}'.format(bp=path),
                            templated=True, title='POI detail')
    representation.add_link('hl:rti',
            '{bp}{{id}}/rti/{{type}}'.format(bp=path), templated=True,
            title='Real-Time Information for a given POI')
    representation.add_link('hl:p-r', '/transport/park-and-ride',
            title='Park and Rides Real-Time information')   # TODO do not hard-code path
    response = make_response(representation.as_json(), 200)
    response.headers['Content-Type'] = "application/json"
    return response
