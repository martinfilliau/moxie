from flask import jsonify


def exception_handler(ex):
    """Prepare an exception as a JSON response
    :param ex: exception
    :return: response
    """
    response = jsonify(ex.to_dict())
    response.status_code = ex.status_code
    response.headers.extend(ex.headers)
    return response


class ApplicationException(Exception):

    status_code = 500
    message = "An error has occured"

    def __init__(self, message=None, status_code=None, payload=None,
                 headers=None):
        Exception.__init__(self)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['description'] = self.message
        return rv


class ServiceUnavailable(ApplicationException):

    status_code = 503
    message = "Service not available"


class BadRequest(ApplicationException):

    status_code = 400


class NotFound(ApplicationException):

    status_code = 404
    message = "Not found"
