import importlib
import logging

from flask import _app_ctx_stack, make_response

logger = logging.getLogger(__name__)

        
def check_services():
    ctx = _app_ctx_stack.top
    services = ctx.app.config.get('HEALTHCHECKS', [])
    ok, result = run_healthchecks(services)
    if ok:
        response_code = 200
    else:
        response_code = 500
    response = make_response('\n'.join(result), response_code)
    response.headers['Content-Type'] = "text/plain"
    return response


def run_healthchecks(services):
    """Run healthchecks by calling the method healthcheck() on every service.
    :param services: list of services to check
    :return True if everything is OK else False, string describing healthcheks"""
    if not services:
        return False, ["No healthchecks configured!"]
    ok = True
    result = []
    for service, parameters in services.iteritems():
        module_name, _, klass_name = service.rpartition('.')
        module = importlib.import_module(module_name)
        klass = getattr(module, klass_name)
        try:
            success, text = klass(**parameters).healthcheck()
        except Exception as e:
            success = False
            text = e
        if not success:
            ok = False
        result.append('* {service} [{parameters}]: {text}'.format(service=service,
            parameters=str(parameters), text=text))
    return ok, result