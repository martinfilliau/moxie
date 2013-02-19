from werkzeug.exceptions import default_exceptions, HTTPException
from flask import make_response, request
from flask.exceptions import JSONHTTPException


def exception_handler(exception):
    """Exception handler
    From http://flask.pocoo.org/snippets/83/
    """
    return abort((exception.code
            if isinstance(exception, HTTPException)
            else 500),
            body=str(exception))

def abort(status_code, body=None, headers={}):
    """Content negociate the error response.
    From http://flask.pocoo.org/snippets/97/
    """

    if 'text/html' in request.headers.get("Accept", ""):
        error_cls = HTTPException
    else:
        error_cls = JSONHTTPException

    class_name = error_cls.__name__
    bases = [error_cls]
    attributes = {'code': status_code}

    if status_code in default_exceptions:
        # Mixin the Werkzeug exception
        bases.insert(0, default_exceptions[status_code])

    error_cls = type(class_name, tuple(bases), attributes)
    return make_response(error_cls(body), status_code, headers)


class ApplicationException(Exception):

    http_code = 500
    message = "An error has occured"

class ServiceUnavailable(ApplicationException):

    http_code = 503
    message = "Service not available"