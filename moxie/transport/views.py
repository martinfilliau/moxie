from flask import json
from moxie.core.views import ServiceView
from moxie.core.kv import kv_store
from .services import TransportService


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    CACHE_KEY_FORMAT = '{0}_naptan_{1}'
    CACHE_EXPIRE = 10   # seconds for cache to expire

    def handle_request(self, ident):
        cache = kv_store.get(self.CACHE_KEY_FORMAT.format(__name__, ident))
        if cache:
            return json.loads(cache)
        else:
            transport_service = TransportService.from_context()
            services, messages = transport_service.get_rti(ident)
            response = {
                'services': services,
                'messages': messages
            }
            kv_store.setex(self.CACHE_KEY_FORMAT.format(__name__, ident),
                    self.CACHE_EXPIRE, json.dumps(response))
            return response
