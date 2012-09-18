import json
import re

from moxie.places.importers.helpers import prepare_document


class OxpointsImporter(object):

    IDENTIFIERS = {
        'oxp_hasOUCSCode': 'oucs',
        'oxp_hasOLISCode': 'olis',
        'oxp_hasOLISAlephCode': 'olis-aleph',
        'oxp_hasOSMIdentifier': 'osm',
        'oxp_hasFinanceCode': 'finance',
        'oxp_hasOBNCode': 'obn',
    }

    def __init__(self, indexer, precedence, oxpoints_file, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        self.oxpoints_file = oxpoints_file

    def import_data(self):
        data = json.load(self.oxpoints_file)
        for datum in data:
            name = datum.get('oxp_fullyQualifiedTitle', datum.get('dc_title', ''))
            if not name:
                continue
            oxpoints_id = datum['uri'].rsplit('/')[-1]
            if datum.get('type', '') == 'http://xmlns.com/foaf/0.1/Image' or oxpoints_id.endswith('.jpg'):
                continue
            doc = dict()
            doc['name'] = name

            oxpoints_type = datum.get('type', '').rsplit('#')[-1]
            doc['tags'] = [oxpoints_type]

            ids = list()
            ids.append('oxpoints:{0}'.format(oxpoints_id))

            for oxp_property, identifier in self.IDENTIFIERS.items():
                if oxp_property in datum:
                    value = datum.pop(oxp_property)
                    if identifier == "osm":
                        value = value.split('/')[1]
                    if type(value) is list:
                        for val in value:
                            ids.append('{0}:{1}'.format(identifier, val.replace(' ', '-').replace('/', '-')))
                    else:
                        ids.append('{0}:{1}'.format(identifier, value.replace(' ', '-').replace('/', '-')))

            doc['identifiers'] = ids

            if 'geo_lat' in datum and 'geo_long' in datum:
                doc['location'] = "%s,%s" % (datum.pop('geo_long'), datum.pop('geo_lat'))
            else:
                continue
            doc.update([('raw_oxpoints_{0}'.format(k), v) for k, v in datum.items()])
            for k, v in doc.items():
                if type(v) not in [str, unicode] and k != self.identifier_key:
                    doc.pop(k)

            search_results = self.indexer.search_for_ids(
                    self.identifier_key, doc[self.identifier_key])
            result = prepare_document(doc, search_results.json, self.precedence)
            result = [result]
            self.indexer.index(result)
        self.indexer.commit()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('oxpointsfile', type=argparse.FileType('r'))
    ns = parser.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('collection1')
    importer = OxpointsImporter(solr, 10, ns.oxpointsfile)
    importer.import_data()


if __name__ == '__main__':
    main()
