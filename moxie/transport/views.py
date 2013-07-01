from datetime import timedelta

from moxie.core.exceptions import BadRequest
from moxie.core.cache import cache
from moxie.core.views import ServiceView
from .services import TransportService, RTITypeNotSupported


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    TIMEOUT = 10    # seconds

    expires = timedelta(seconds=TIMEOUT)

    @cache.cached(timeout=TIMEOUT)
    def handle_request(self, ident, rtitype):
        transport_service = TransportService.from_context()
        try:
            rti_data = transport_service.get_rti(ident, rtitype)
        except RTITypeNotSupported:
            raise BadRequest("POI: %s doesn't support the RTI requested: %s"
                    % (ident, rtitype))
        else:
            services, messages, rtitype, title = rti_data
            response = {
                'services': services,
                'messages': messages,
                'type': rtitype,
                'title': title,
            }
            return response
