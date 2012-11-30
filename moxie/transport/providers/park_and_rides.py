import logging
import requests
from lxml import etree


logger = logging.getLogger(__name__)


class OxfordParkAndRideProvider(object):
    """Provider for Oxfordshire Park and Ride website
    """

    _VOYAGER_URL = "http://voyager.oxfordshire.gov.uk/Carpark.aspx"

    def get_data(self):
        """
        Requests the URL and parses the page
        :return dictionary of park and rides availability information
        """
        response = requests.get(self._VOYAGER_URL, timeout=4)
        if response.ok:
            return self.parse_html(response.text)
        else:
            logger.warning("Could reach {url}".format(url=self._VOYAGER_URL), extra=
                {'response_code': response.status_code})

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