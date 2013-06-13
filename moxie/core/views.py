from datetime import datetime, timedelta
import datetime as dt   # dt is used here to make the tests pass (datetime is mocked)

from flask.views import View
from flask import request, jsonify, make_response, current_app, abort
from werkzeug.exceptions import NotAcceptable
from werkzeug.wrappers import BaseResponse
from werkzeug.http import http_date

from moxie.core.exceptions import ApplicationException, BadRequest, exception_handler


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
    methods = ['GET', 'OPTIONS']

    cors_allow_headers = ''
    cors_allow_credentials = False
    cors_max_age = 21600

    # Set to a timedelta or datetime to control HTTP caching headers
    expires = None

    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(ServiceView, cls).as_view(*args, **kwargs)
        view.provide_automatic_options = False
        return view

    def _handle_options(self):
        options_resp = current_app.make_default_options_response()
        return self._cors_headers(options_resp, preflight=True)

    def _cors_headers(self, response, preflight=False, origin=None):
        """Applies the appropriate CORS headers for a given Response"""
        if not origin and request:  # Origin must exist in a valid CORS request
            origin = request.headers.get('origin')
        h = {}
        allow_origins = current_app.config.get('DEFAULT_ALLOW_ORIGINS', [])
        if not self.cors_allow_credentials:
            h['Access-Control-Allow-Origin'] = '*'
        elif current_app.debug or origin in allow_origins:
            h['Access-Control-Allow-Origin'] = origin
        else:
            abort(400)
        if preflight:
            h['Access-Control-Allow-Methods'] = response.headers['allow']
            h['Access-Control-Max-Age'] = str(self.cors_max_age)
            if self.cors_allow_headers:
                h['Access-Control-Allow-Headers'] = self.cors_allow_headers
        if self.cors_allow_credentials:
            h['Access-Control-Allow-Credentials'] = 'true'
        response.headers.extend(h)
        return response

    def _expires_headers(self, response):
        """Applies Expires and Cache-Control headers
        :param response: response to extend
        :return: response
        """
        h = {}
        if self.expires:
            if isinstance(self.expires, timedelta):
                now = datetime.utcnow()
                now += self.expires
                h['Expires'] = http_date(now)
                h['Cache-Control'] = 'max-age={seconds}'.format(seconds=self.expires.seconds)
            elif isinstance(self.expires, dt.datetime):
                difference = self.expires - datetime.utcnow()
                h['Expires'] = http_date(self.expires)
                h['Cache-Control'] = 'max-age={seconds}'.format(seconds=difference.seconds)
            response.headers.extend(h)
        return response

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
            try:
                response = self.handle_request(*args, **kwargs)
                response = make_response(service_response(self, response))
                response = self._expires_headers(response)
            except ApplicationException as ae:
                response = exception_handler(ae)
            except:
                if current_app.debug:
                    raise
                response = exception_handler(ApplicationException())
            response = self._cors_headers(response)
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
