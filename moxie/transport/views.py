import logging

from datetime import timedelta

from moxie.core.exceptions import BadRequest, ServiceUnavailable, NotFound
from moxie.core.cache import cache
from moxie.core.views import ServiceView
from moxie.core.service import NoSuitableProviderFound, MultipleProvidersFound, ProviderException
from moxie.transport.services import TransportService


logger = logging.getLogger(__name__)


class RTI(ServiceView):
    methods = ['GET', 'OPTIONS']

    TIMEOUT = 10    # seconds

    expires = timedelta(seconds=TIMEOUT)

    @cache.cached(timeout=TIMEOUT)
    def handle_request(self, ident, rtitype):
        transport_service = TransportService.from_context()
        try:
            rti_data = transport_service.get_rti(ident, rtitype)
        except NoSuitableProviderFound:
            msg = "NoSuitableProviderFound for: %s (%s)" % (ident, rtitype)
            logger.warn(msg, exc_info=True)
            raise BadRequest(msg)
        except MultipleProvidersFound:
            msg = "MultipleProvidersFound for: %s (%s)" % (ident, rtitype)
            logger.critical(msg, exc_info=True)
            raise BadRequest(msg)
        except NotFound:
            raise NotFound("POI {ident} not found".format(ident=ident))
        else:
            services, messages, rtitype, title = rti_data
            response = {
                'services': services,
                'messages': messages,
                'type': rtitype,
                'title': title,
            }
            return response


class ParkAndRides(ServiceView):

    TIMEOUT = 30    # seconds

    expires = timedelta(seconds=TIMEOUT)

    def handle_request(self):
        transport_service = TransportService.from_context()
        try:
            return transport_service.get_park_and_ride()
        except ProviderException:
            logger.critical("Unable to reach P-R provider", exc_info=True)
            raise ServiceUnavailable(message="Unable to reach provider")