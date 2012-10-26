from flask.views import View
from flask import request, jsonify, make_response, current_app
from werkzeug.exceptions import NotAcceptable
from werkzeug.wrappers import BaseResponse


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

    default_allow_headers = ''
    default_cors_max_age = 21600

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(ServiceView, cls).as_view(*args, **kwargs)
        view.provide_automatic_options = False
        return view

    def _handle_options(self):
        options_resp = current_app.make_default_options_response()
        h = options_resp.headers
        if request.headers['origin'] in current_app.conf['DEFAULT_ALLOW_ORIGINS']:
            h['Access-Control-Allow-Origin'] = request.headers['origin']
        h['Access-Control-Allow-Methods'] = h['allow']
        h['Access-Control-Max-Age'] = str(self.default_cors_max_age)
        h['Access-Control-Allow-Headers'] = self.default_allow_headers
        return options_resp

    def dispatch_request(self, *args, **kwargs):
        """Finds the best_match service_response from those registered
        If no good service_response can be found we generally want to
        return a NotAcceptable 406.
        """
        if request.method == 'OPTIONS':
            return self._handle_options()
        best_match = request.accept_mimetypes.best_match(
                self.service_responses.keys())
        if best_match:
            service_response = self.service_responses[best_match]
            response = self.handle_request(*args, **kwargs)
            response = make_response(service_response(self, response))
            if request.headers['origin'] in current_app.conf['DEFAULT_ALLOW_ORIGINS']:
                response.headers['Access-Control-Allow-Origin'] = request.headers['origin']
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response
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
        if issubclass(type(response),
                (BaseResponse, current_app.response_class)):
            return response
        else:
            return jsonify(response)
