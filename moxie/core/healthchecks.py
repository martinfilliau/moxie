import importlib
import logging

from flask import _app_ctx_stack, make_response

logger = logging.getLogger(__name__)


class Healthchecks(object):
    
    def __init__(self):
        pass
        
def check_services():
    ctx = _app_ctx_stack.top
    services = ctx.app.config.get('HEALTHCHECKS', [])
    result = []
    response_code = 200
    for service, parameters in services.iteritems():
        module_name, _, klass_name = service.rpartition('.')
        module = importlib.import_module(module_name)
        klass = getattr(module, klass_name)
        try:
            ok, text = klass(**parameters).healthcheck()
        except Exception as e:
            ok = False
            text = e
        if not ok:
            response_code = 500
        result.append('* {service} [{parameters}]: {text}'.format(service=service,
            parameters=str(parameters), text=text))
    response = make_response('\n'.join(result), response_code)
    response.headers['Content-Type'] = "text/plain"
    return response
