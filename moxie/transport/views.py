from datetime import timedelta

from moxie.core.cache import cache
from moxie.core.views import ServiceView
from .services import TransportService


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    TIMEOUT = 10    # seconds

    expires = timedelta(seconds=TIMEOUT)

    @cache.cached(timeout=TIMEOUT)
    def handle_request(self, ident):
        transport_service = TransportService.from_context()
        services, messages = transport_service.get_rti(ident)
        response = {
            'services': services,
            'messages': messages
        }
        return response