import logging
import re
from lxml import etree

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)

rx = re.compile('\W+')


def f(l, n):
    e = l.find(n)
    if e is not None and e.text is not None:
        return rx.sub(' ', e.text).strip()


class OxLibraryDataImporter(object):

    def __init__(self, indexer, precedence, file):
        self.indexer = indexer
        self.precedence = precedence
        self.file = file

    def run(self):
        xml = etree.parse(self.file)
        libraries = xml.xpath('.//library')
        self.libs = [{'name': f(l, 'name'),
         'id': f(l, 'id'),
         'opening_hours_term_time': f(l, 'hours/termtime'),
         'opening_hours_vacation': f(l, 'hours/vacation'),
         'opening_hours_closed': f(l, 'hours/closed')} for l in libraries]


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('file', type=argparse.FileType('r'))
    ns = args.parse_args()
    importer = OxLibraryDataImporter(None, 10, ns.file)
    importer.run()
    import pprint
    pprint.pprint(importer.libs)


if __name__ == '__main__':
    main()