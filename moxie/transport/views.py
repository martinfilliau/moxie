import json

from flask import request, current_app

from moxie.core.views import ServiceView
from moxie.core.kv import kv_store
from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider

class BusRti(ServiceView):
    methods = ['GET', 'OPTIONS']

    CACHE_KEY_FORMAT = '{0}_naptan_{1}'
    CACHE_EXPIRE = 10   # seconds for cache to expire

    def handle_request(self):
        naptan_code = request.args.get('id')

        cache = kv_store.get(self.CACHE_KEY_FORMAT.format(__name__, naptan_code))
        if cache:
            return json.loads(cache)
        else:
            provider = CloudAmberBusRtiProvider(current_app.config['BUS_RTI_URL'])
            services, messages = provider.get_rti(naptan_code)
            response = {
                'services': services,
                'messages': messages
            }
            kv_store.setex(self.CACHE_KEY_FORMAT.format(__name__, naptan_code),
                    self.CACHE_EXPIRE, json.dumps(response))
            return response
