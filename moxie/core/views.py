from flask.views import View
from flask import request
from werkzeug.exceptions import NotAcceptable
from collections import defaultdict


def register_mimetype(mimetype):
    def wrapper(f):
        mimetypes = getattr(f, 'mimetypes', [])
        mimetypes.append(mimetype)
        mimetypes = setattr(f, 'mimetypes', mimetypes)
        mimetypes
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
        for mt in request.accept_mimetypes.values():
            if mt in self.service_responses:
                return self.service_responses[mt]()
        return self.default_response()

    @register_mimetype('text/html')
    def as_html(self):
        raise NotImplementedError()

    @register_mimetype('application/json')
    def as_json(self):
        raise NotImplementedError()
