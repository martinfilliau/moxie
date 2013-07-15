import logging
import requests
from lxml import etree
from requests.exceptions import RequestException
from datetime import datetime

from moxie.core.cache import cache
from moxie.core.service import ProviderException
from . import TransportRTIProvider


logger = logging.getLogger(__name__)

CACHE_KEY = "ox-p-r"
CACHE_KEY_UPDATE = CACHE_KEY + "_updated"


class OxfordParkAndRideProvider(TransportRTIProvider):
    """Provider for Oxfordshire Park and Ride website
    """

    _CARPARKS = {
        'Pear Tree Park & Ride OX2 8JD': "osm:4333225",
        'Redbridge Park & Ride OX1 4XG': "osm:2809915",
        'Seacourt Park & Ride OX2 0HP': "osm:34425625",
        'Thornhill Park & Ride OX3 8DP': "osm:24719725",
        'Water Eaton Park & Ride OX2 8HA': "osm:4329908",
    }

    provides = {'p-r': "Park and Rides Live Information"}

    def __init__(self, url="http://voyager.oxfordshire.gov.uk/Carpark.aspx", timeout=4):
        self.url = url
        self.timeout = timeout

    def handles(self, doc, rti_type=None):
        for ident in doc.identifiers:
            if ident in self._CARPARKS.values():
                return True
        return False

    def invoke(self, doc, rti_type=None):
        for ident in doc.identifiers:
            if ident in self._CARPARKS.values():
                data = self.get_data()
                services = data.get(ident)
                messages = []
                title = self.provides.get(rti_type)
                return services, messages, rti_type, title
        return None

    def get_all(self):
        """Get data from all park and rides
        """
        return {'park_and_rides':[dict(v, identifier=k) for k, v in self.get_data().items()] }

    def import_data(self):
        try:
            response = requests.get(self.url, timeout=self.timeout, config={'danger_mode': True})
        except RequestException as re:
            logger.warning('Error in request to Park & Ride info', exc_info=True,
                           extra={
                               'data': {
                                   'url': self.url}
                           })
            raise ProviderException
        else:
            data = self.parse_html(response.text)
            cache.set(CACHE_KEY, data)
            cache.set(CACHE_KEY_UPDATE, datetime.now().isoformat())

    def get_data(self):
        """
        Requests the URL and parses the page
        :return dictionary of park and rides availability information
        """
        data = cache.get(CACHE_KEY)
        if data:
            return data
        else:
            raise ProviderException

    def parse_html(self, html):
        """Parses the HTML of the page
        :param html: HTML content as a string
        :return dictionary of park and rides with availability information
        """
        carparks = {}

        try:
            xml = etree.fromstring(html, parser=etree.HTMLParser())
            tbody = xml.find(".//div[@class='cloud-amber']/table/tbody")

            for tr in tbody:
                name = tr[1].text.strip()
                identifier = self._CARPARKS.get(name, None)

                if not identifier:
                    break

                if tr[6].text == 'Faulty':
                    spaces = 0
                    unavailable = True
                else:
                    try:
                        spaces = int(tr[3].text)
                        unavailable = False
                    except ValueError:
                        spaces = 0
                        unavailable = True

                carparks[identifier] = {
                    'name': name,
                    'spaces': spaces,
                    'capacity': int(tr[4].text),
                    'percentage': int(100 * (1 - float(spaces) / float(tr[4].text))),
                    'unavailable': unavailable,
                    }
        except Exception as e:
            logger.exception("Couldn't parse the park and rides page", exc_info=True)

        return carparks


if __name__ == '__main__':
    provider = OxfordParkAndRideProvider()
    carparks = provider.get_data()
    print carparks