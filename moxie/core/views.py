from flask.views import View
from flask import request, jsonify
from werkzeug.exceptions import NotAcceptable
from collections import defaultdict


def accepts(*accept_values):
    """Given a list of mime-types this view should route responses
    through depending upon the request Accept headers.
    """
    def wrapper(f):
        mimetypes = getattr(f, 'mimetypes', [])
        mimetypes.extend(accept_values)
        mimetypes = setattr(f, 'mimetypes', mimetypes)
        return f
    return wrapper


class ServiceMetaclass(type):
    """Metaclass which picks up any Service Responses and registers them.
    Service Responses:
        Methods which are decorated with @accepts this sets a .mimetypes
        attribute on the method listing any mimetypes which the method supports
    Note: We also register service_responses from our base classes.
    """
    def __new__(cls, name, bases, attrs):
        service_responses = dict()
        for b in bases:  # Bases first so they get (correctly?) overriden
            service_responses.update(getattr(b, 'service_responses', dict()))
        for attr in attrs.values():
            mimetypes = getattr(attr, 'mimetypes', [])
            for mt in mimetypes:
                service_responses[mt] = attr
        attrs['service_responses'] = service_responses
        return type.__new__(cls, name, bases, attrs)


class ServiceView(View):

    __metaclass__ = ServiceMetaclass
    default_response = NotAcceptable

    def dispatch_request(self):
        """Finds the best_match service_response from those registered
        If no good service_response can be found we generally want to
        return a NotAcceptable 406.
        """
        best_match = request.accept_mimetypes.best_match(
                self.service_responses.keys())
        if best_match:
            service_response = self.service_responses[best_match]
            response = self.handle_request()
            return service_response(self, response)
        else:
            return self.default_response()

    def handle_request(self):
        """This function should be implemented by all views to build
        a common response object. Usually in the form of a Python
        dictionary object. This response is then formatted and returned
        by a method depending upon the request headers Accept mimetypes.
        """
        return dict()

    @accepts('application/json')
    def as_json(self, response):
        return jsonify(response)
