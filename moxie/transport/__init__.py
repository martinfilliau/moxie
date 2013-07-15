from flask import Blueprint, request
from flask.helpers import make_response

from moxie.core.representations import HALRepresentation
from moxie.transport.views import ParkAndRides

TRANSPORT_CURIE = 'http://moxie.readthedocs.org/en/latest/http_api/transport.html#{rel}'


def create_blueprint(blueprint_name, conf):
    transport_blueprint = Blueprint(blueprint_name, __name__, **conf)

    transport_blueprint.add_url_rule('/', view_func=get_routes)

    transport_blueprint.add_url_rule('/park-and-rides',
            view_func=ParkAndRides.as_view('p-r'))

    return transport_blueprint


def get_routes():
    path = request.path
    representation = HALRepresentation({})
    representation.add_curie('hl', TRANSPORT_CURIE)
    representation.add_link('self', '{bp}'.format(bp=path))
    representation.add_link('hl:p-r', '{bp}park-and-rides'.format(bp=path),
                            title='Park and Rides Real-Time Information')
    response = make_response(representation.as_json(), 200)
    response.headers['Content-Type'] = "application/json"
    return response
