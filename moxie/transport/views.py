from flask import json

from moxie.core.cache import cache
from moxie.core.views import ServiceView
from .services import TransportService


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    @cache.cached(timeout=10)
    def handle_request(self, ident):
        transport_service = TransportService.from_context()
        services, messages = transport_service.get_rti(ident)
        response = {
            'services': services,
            'messages': messages
        }
        return response