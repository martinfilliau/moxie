import logging
import json

from flask import _app_ctx_stack, make_response

logger = logging.getLogger(__name__)


def get_blueprints():
    """Return a list of blueprints in HAL JSON
    """
    ctx = _app_ctx_stack.top
    services = ctx.app.blueprints.keys()
    links = {}
    for service in services:
        links[service] = {'self': {'href': '/{blueprint}'.format(blueprint=service)}}
    content = json.dumps({'_links': links})
    response = make_response(content, 200)
    response.headers['Content-Type'] = "application/json"
    return response