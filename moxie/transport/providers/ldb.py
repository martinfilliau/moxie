import logging
import suds

from contextlib import contextmanager
from suds.sax.element import Element
from . import TransportRTIProvider


logger = logging.getLogger(__name__)


@contextmanager
def override_loglevel(level):
    """Silence pesky logs"""
    previous_level = logger.getEffectiveLevel()
    root_previous_level = logger.root.getEffectiveLevel()
    logger.setLevel(level)
    logger.root.setLevel(level)
    yield
    logger.setLevel(previous_level)
    logger.root.setLevel(root_previous_level)


class LiveDepartureBoardPlacesProvider(TransportRTIProvider):
    _WSDL_URL = "https://realtime.nationalrail.co.uk/ldbws/wsdl.aspx"
    _ATTRIBUTION = {'title': ("Powered by National Rail Enquiries"),
                  'url': "http://www.nationalrail.co.uk"}

    provides = {'rail-departures': "Departures",
            'rail-arrivals': "Arrivals"}

    def __init__(self, token, max_services=15):
        self._token = token
        self._max_services = max_services
        self._ldb_service = None

    def handles(self, doc, rti_type=None):
        if rti_type and rti_type not in self.provides:
            return False
        for ident in doc.identifiers:
            if ident.startswith('crs'):
                return True
        return False

    def get_ldb_service(self):
        """Tries to cache the SOAP Client so we don't keep recreating
        it and loading in the WSDL each time.
        """
        if not self._ldb_service:
            try:
                soapheaders = Element('AccessToken').insert(
                        Element('TokenValue').setText(self._token))
                self._ldb_service = suds.client.Client(self._WSDL_URL,
                        soapheaders=soapheaders)
            except:
                logger.warning("Could not instantiate suds client for live departure board.",
                        exc_info=True, extra={'wsdl_url': self._WSDL_URL})
        return self._ldb_service

    def invoke(self, doc, rti_type):
        for ident in doc.identifiers:
            if ident.startswith('crs'):
                _, crs_code = ident.split(':')
                if rti_type == 'rail-departures':
                    services, messages = self.get_departure_board(crs_code)
                elif rti_type == 'rail-arrivals':
                    services, messages = self.get_arrival_board(crs_code)
                title = self.provides.get(rti_type)
                return services, messages, rti_type, title

    def get_departure_board(self, crs):
        with override_loglevel('WARNING'):
            ldb_service = self.get_ldb_service()
            db = ldb_service.service.GetDepartureBoard(self._max_services, crs)
        db = self.transform_suds(db)
        if 'nrccMessages' in db:
            messages = db['nrccMessages']['message']
        else:
            messages = []
        return db['trainServices']['service'], messages

    def get_arrival_board(self, crs):
        with override_loglevel('WARNING'):
            ldb_service = self.get_ldb_service()
            db = ldb_service.service.GetArrivalBoard(self._max_services, crs)
        db = self.transform_suds(db)
        if 'nrccMessages' in db:
            messages = db['nrccMessages']['message']
        else:
            messages = []
        return db['trainServices']['service'], messages

    def transform_suds(self, o):
        if isinstance(o, suds.sudsobject.Object):
            return dict((k, self.transform_suds(v)) for k, v in o)
        elif isinstance(o, list):
            return map(self.transform_suds, o)
        else:
            return o
