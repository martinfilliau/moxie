import logging

from flask import _app_ctx_stack, make_response

from moxie.core.representations import HALRepresentation

logger = logging.getLogger(__name__)


def get_blueprints():
    """Return a list of blueprints in HAL JSON
    """
    ctx = _app_ctx_stack.top
    services = ctx.app.blueprints.keys()
    representation = HALRepresentation({})
    for service in services:
        representation.add_link(service, '/{blueprint}'.format(blueprint=service))
    response = make_response(representation.as_json(), 200)
    response.headers['Content-Type'] = "application/json"
    return response