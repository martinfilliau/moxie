import logging
import re
from lxml import etree

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)

rx = re.compile('\W+')


def text(l, n):
    e = l.find(n)
    if e is not None and e.text is not None:
        return string_cleanup(e.text)


def list(l, n):
    e = l.findall(n)
    if e is not None:
        return [string_cleanup(s.text) for s in e if s is not None]


def string_cleanup(str):
    return rx.sub(' ', str).strip()


class OxLibraryDataImporter(object):

    def __init__(self, indexer, precedence, file):
        self.indexer = indexer
        self.precedence = precedence
        self.file = file

    def run(self):
        xml = etree.parse(self.file)
        libraries = xml.xpath('.//library')
        self.libs = [{'name': text(l, 'name'),
                      'id': text(l, 'id'),
                      'opening_hours_term_time': text(l, 'hours/termtime'),
                      'opening_hours_vacation': text(l, 'hours/vacation'),
                      'opening_hours_closed': text(l, 'hours/closed'),
                      'subjects': list(l, 'subjects/subject')
                     } for l in libraries]


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