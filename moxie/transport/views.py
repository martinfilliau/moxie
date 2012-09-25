from flask import request
from moxie.core.views import ServiceView

from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider

class BusRti(ServiceView):
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        naptan_code = request.args.get('id')
        cabrp = CloudAmberBusRtiProvider("")    # TODO current_app.CONFIGURATION
        services, messages = cabrp.get_rti(naptan_code)
        response = dict()
        response["services"] = services
        response["messages"] = messages
        return response