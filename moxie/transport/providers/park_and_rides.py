import logging
import requests
from lxml import etree
from requests.exceptions import RequestException


logger = logging.getLogger(__name__)


class OxfordParkAndRideProvider(object):
    """Provider for Oxfordshire Park and Ride website
    """

    _CARPARKS = {
        'Pear Tree Park & Ride OX2 8JD': "osm:4333225",
        'Redbridge Park & Ride OX1 4XG': "osm:2809915",
        'Seacourt Park & Ride OX2 0HP': "osm:34425625",
        'Thornhill Park & Ride OX3 8DP': "osm:24719725",
        'Water Eaton Park & Ride OX2 8HA': "osm:4329908",
    }
    _CARPARK_IDS = _CARPARKS.values()

    provides = {'p-r': "Park and Rides Live Information"}

    def __init__(self, url="http://voyager.oxfordshire.gov.uk/Carpark.aspx", timeout="4"):
        self.url = url
        self.timeout = timeout

    def handles(self, doc, rti_type=None):
        for ident in doc.identifiers:
            if ident in self._CARPARK_IDS:
                return True
        return False

    def invoke(self, doc, rti_type=None):
        pass

    def get_data(self):
        """
        Requests the URL and parses the page
        :return dictionary of park and rides availability information
        """
        try:
            response = requests.get(self.url, timeout=self.timeout, config={'danger_mode': True})
        except RequestException as re:
            logger.warning('Error in request to Park & Ride info', exc_info=True,
                           extra={
                               'data': {
                                   'url': self.url}
                           })
        else:
            return self.parse_html(response.text)

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

                carparks[name] = {
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