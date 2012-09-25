from flask import request, current_app

from moxie.core.views import ServiceView
from moxie.core.kv import kv_store
from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider

class BusRti(ServiceView):
    methods = ['GET', 'OPTIONS']

    def handle_request(self):
        naptan_code = request.args.get('id')
        cabrp = CloudAmberBusRtiProvider(current_app.config['BUS_RTI_URL'])
        services, messages = cabrp.get_rti(naptan_code)
        response = dict()
        response["services"] = services
        response["messages"] = messages
        return response