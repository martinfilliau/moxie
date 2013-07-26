import logging
import re
import unicodedata
from lxml import etree

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)

rx = re.compile(' +')

POLICIES = {
    '1': 'All',
    '2': 'Some',
    '3': 'None'
}


def text(l, n):
    e = l.find(n)
    if e is not None and e.text is not None:
        return string_cleanup(e.text)


def list(l, n):
    e = l.findall(n)
    if e is not None:
        return [string_cleanup(s.text) for s in e if s is not None]


def policies(l, n):
    e = l.findall(n)
    pol = {}
    if e is not None:
        for policy in e:
            #pol[policy.get('for')] = {'access': POLICIES[policy.find('access').text],
            #                          'borrowing': POLICIES[policy.find('borrowing').text],
            #                          'notes': string_cleanup(policy.find('notes').text)}
            pol[policy.get('for')] = "Admissions: {access}. Borrowings: {borrowing}. Notes: {notes}".format(
                access=POLICIES[policy.find('access').text],
                borrowing=POLICIES[policy.find('borrowing').text],
                notes=string_cleanup(policy.find('notes').text))
    return pol


def string_cleanup(s):
    if s:
        if isinstance(s, unicode):
            s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
        return rx.sub(' ', s).strip()
    else:
        return None


class OxLibraryDataImporter(object):

    def __init__(self, indexer, precedence, file, identifier_key='identifiers',
                 lib_data_identifier='librarydata',
                 prefix_index_key='meta_library_'):
        self.indexer = indexer
        self.precedence = precedence
        self.file = file
        self.identifier_key = identifier_key
        self.lib_data_identifier = lib_data_identifier
        self.prefix_index_key = prefix_index_key

    def run(self):
        self.parse_libs()
        if self.indexer:
            self.index()

    def parse_libs(self):
        xml = etree.parse(self.file)
        libraries = xml.xpath('.//library')
        self.libs = [{'id': text(l, 'id'),
                      'opening_hours_termtime': text(l, 'hours/termtime'),
                      'opening_hours_vacation': text(l, 'hours/vacation'),
                      'opening_hours_closed': text(l, 'hours/closed'),
                      'subjects': list(l, 'subjects/subject'),
                      'policies': policies(l, 'policies/policy')
                     } for l in libraries]

    def index(self):
        not_found = 0
        imported = 0
        for lib in self.libs:
            ident = "{key}:{value}".format(key=self.lib_data_identifier,
                                           value=lib['id'])
            search_results = self.indexer.search_for_ids(self.identifier_key,
                                                         [ident])
            if search_results.results:
                doc = search_results.results[0]
                doc[self.prefix_index_key+'opening_hours_termtime'] = lib['opening_hours_termtime']
                doc[self.prefix_index_key+'opening_hours_vacation'] = lib['opening_hours_vacation']
                doc[self.prefix_index_key+'opening_hours_closed'] = lib['opening_hours_closed']
                doc[self.prefix_index_key+'subject'] = lib['subjects']
                if 'academic' in lib['policies']:
                    doc[self.prefix_index_key+'policy_academic'] = lib['policies']['academic']
                if 'other' in lib['policies']:
                    doc[self.prefix_index_key+'policy_other'] = lib['policies']['other']
                if 'postgraduate' in lib['policies']:
                    doc[self.prefix_index_key+'policy_postgraduate'] = lib['policies']['postgraduate']
                if 'undergraduate' in lib['policies']:
                    doc[self.prefix_index_key+'policy_undergraduate'] = lib['policies']['undergraduate']
                doc['type'] = doc['type'][0]    # cannot be a list atm
                result = prepare_document(doc, search_results, self.precedence)
                self.indexer.index([result])
                imported += 1
            else:
                logger.info('No results for {ident}'.format(ident=ident))
                not_found += 1
        logger.info('{imported} imported, {not_found} not found'.format(imported=imported,
                                                                        not_found=not_found))


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