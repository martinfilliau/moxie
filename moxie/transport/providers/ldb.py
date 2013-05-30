import logging
import suds

from suds.sax.element import Element


logger = logging.getLogger(__name__)


class LiveDepartureBoardPlacesProvider():
    _WSDL_URL = "https://realtime.nationalrail.co.uk/ldbws/wsdl.aspx"
    _ATTRIBUTION = {'title': ("Powered by National Rail Enquiries"),
                  'url': "http://www.nationalrail.co.uk"}

    def __init__(self, token, max_services=15):
        self._max_services = max_services
        soapheaders = Element('AccessToken').insert(
                Element('TokenValue').setText(token))
        try:
            self.ldb = suds.client.Client(self._WSDL_URL,
                    soapheaders=soapheaders)
        except:
            logger.warning("Could not instantiate suds client for live departure board.",
                    exc_info=True, extra={'wsdl_url': self._WSDL_URL})

    def get_departure_board(self, crs):
        db = self.ldb.service.GetDepartureBoard(self._max_services, crs)
        return self.transform_suds(db)

    def get_arrival_board(self, crs):
        db = self.ldb.service.GetArrivalBoard(self._max_services, crs)
        return self.transform_suds(db)

    def transform_suds(self, o):
        if isinstance(o, suds.sudsobject.Object):
            return dict((k, self.transform_suds(v)) for k, v in o)
        elif isinstance(o, list):
            return map(self.transform_suds, o)
        else:
            return o

    def delayed(self, eta, sta, etd, std):
        """
        Try and figure out if a service is delayed based on free text values
        for estimated/scheduled times of arrival/depature
        """
        if eta in ('Delayed', 'Cancelled') or etd in ('Delayed', 'Cancelled'):
            # Easy case
            return True
        else:
            # More complex case, have to parse time stamps
            try:
                # Compare scheduled and expected arrival times
                schedh, schedm = sta.split(':')
                exph, expm = eta.rstrip('*').split(':')
            except ValueError:
                pass
            else:
                # Minutes since midnight, as we can't compare time objects
                sched_msm = int(schedh) * 60 + int(schedm)
                exp_msm = int(exph) * 60 + int(expm)
                if exp_msm < sched_msm:
                    # Deal with wraparound at midnight
                    sched_msm += 1440
                if exp_msm - sched_msm >= 5:
                    # 5 minute delay
                    return True
            try:
                # Compare scheduled and expected departure times
                schedh, schedm = std.split(':')
                exph, expm = etd.rstrip('*').split(':')
            except ValueError:
                pass
            else:
                # Minutes since midnight, as we can't compare time objects
                sched_msm = int(schedh) * 60 + int(schedm)
                exp_msm = int(exph) * 60 + int(expm)
                if exp_msm < sched_msm:
                    # Deal with wraparound at midnight
                    sched_msm += 1440
                if exp_msm - sched_msm >= 5:
                    # 5 minute delay
                    return True
            return False
