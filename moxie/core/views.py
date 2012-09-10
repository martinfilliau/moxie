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


class ServiceView(View):

    default_response = NotAcceptable

    def __init__(self, *args, **kwargs):
        self.service_responses = defaultdict(list)
        for attr in dir(self):
            attr = getattr(self, attr)
            mimetypes = getattr(attr, 'mimetypes', [])
            for mt in mimetypes:
                self.service_responses[mt] = attr
        super(ServiceView, self).__init__(*args, **kwargs)

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
            return service_response(response)
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
