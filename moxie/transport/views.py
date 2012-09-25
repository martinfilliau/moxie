from flask import request, current_app
from moxie.core.views import ServiceView


class BusRti(ServiceView):
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        response = dict()
        return response