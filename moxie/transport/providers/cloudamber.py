import logging
import requests

from lxml import etree
from itertools import chain
from . import TransportRTIProvider
from requests.exceptions import RequestException
from moxie.core.exceptions import ServiceUnavailable
from moxie.core.metrics import statsd

logger = logging.getLogger(__name__)


class CloudAmberBusRtiProvider(TransportRTIProvider):
    """
    Parses an HTML page from a CloudAmber instance
    """

    provides = {'bus': "Live bus departure times"}

    def __init__(self, url, timeout=2):
        """
        Init
        :param url: URL of CloudAmber instance
        :param timeout: (optional) timeout when trying to reach URL
        """
        self.url = url
        self.timeout = timeout

    def handles(self, doc, rti_type=None):
        if rti_type and rti_type not in self.provides:
            return False
        for ident in doc.identifiers:
            if ident.startswith('naptan'):
                return True
        return False

    def invoke(self, doc, rti_type):
        for ident in doc.identifiers:
            if ident.startswith('naptan'):
                _, naptan_code = ident.split(':')
                services, messages = self.get_rti(naptan_code)
                title = self.provides.get(rti_type)
                return services, messages, rti_type, title

    def get_url(self, naptan_code):
        """
        Format a URL with a naptan code and URL of the instance
        @param naptan_code: Naptan code to append to the URL
        @return: formatted URL
        """
        return "{0}/Naptan.aspx?t=departure&sa={1}&dc=&ac=96&vc=&x=0&y=0&format=xhtml".format(self.url, naptan_code)

    def get_rti(self, naptan_code):
        """
        Get a dict containing RTI
        @param naptan_code: SMS code to search for
        @return: dictionary of services
        """
        try:
            with statsd.timer('transport.providers.cloudamber.rti_request'):
                response = requests.get(self.get_url(naptan_code),
                                        timeout=self.timeout)
                response.raise_for_status()
        except RequestException:
            logger.warning('Error in request to Cloudamber', exc_info=True,
                         extra={
                             'data': {
                                 'url': self.url,
                                 'naptan': naptan_code}
                         })
            raise ServiceUnavailable()
        else:
            with statsd.timer('transport.providers.cloudamber.parse_html'):
                return self.parse_html(response.text)

    def parse_html(self, content):
        """
        Parse HTML content from a CloudAmber page
        @param content: HTML content
        @return: list of services, messages
        """
        services = []
        messages = []
        try:
            xml = etree.fromstring(content, parser=etree.HTMLParser())
            # we need the second table
            cells = xml.findall('.//div[@class="cloud-amber"]')[0].findall('.//table')[1].findall('tbody/tr/td')

            # retrieved all cells, splitting every CELLS_PER_ROW to get rows
            CELLS_PER_ROW = 5
            rows = [cells[i:i+CELLS_PER_ROW] for i in range(0, len(cells), CELLS_PER_ROW)]

            parsed_services = {}

            for row in rows:
                service, destination, proximity = [row[i].text.encode('utf8').replace('\xc2\xa0', '')
                                                   for i in range(3)]
                if proximity.lower() == 'due':
                    diff = 0
                else:
                    diff = int(proximity.split(' ')[0])

                if not service in services:
                    # first departure of this service
                    parsed_services[service] = (destination, (proximity, diff), [])
                else:
                    # following departure of this service
                    parsed_services[service][2].append((proximity, diff))

            services = [(s[0], s[1][0], s[1][1], s[1][2]) for s in parsed_services.items()]
            services.sort(key=lambda x: (' '*(5-len(x[0]) + (1 if x[0][-1].isalpha() else 0)) + x[0]))
            services.sort(key=lambda x: x[2][1])

            services = [{'service': s[0],
                         'destination': s[1],
                         'next': s[2][0],
                         'following': [f[0] for f in s[3]],
                         } for s in services]

            # messages that can be displayed (bus stop)
            cells = xml.findall('.//table')[0].findall('tr/td')

            try:
                messages = cells[3]
                parts = ([messages.text] +
                         list(chain(*([c.text, etree.tostring(c), c.tail] for c in messages.getchildren()))) +
                         [messages.tail])
                messages = ''.join([p for p in parts if p])
                messages = [messages]
            except IndexError:
                pass
                # no message

        except Exception:
            logger.info('Unable to parse HTML', exc_info=True, extra={
                'data': {
                    'html_content': content,
                    },
                })

        return services, messages
