import json
import re
import logging

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class OxpointsImporter(object):

    IDENTIFIERS = {
        'oxp_hasOUCSCode': 'oucs',
        'oxp_hasOLISCode': 'olis',
        'oxp_hasOLISAlephCode': 'olis-aleph',
        'oxp_hasOSMIdentifier': 'osm',
        'oxp_hasFinanceCode': 'finance',
        'oxp_hasOBNCode': 'obn',
    }

    # Alignment between OxPoints types we want to store and our hierarchy of types
    OXPOINTS_TYPES = {
        'College': '/university/college',
        'Department': '/university/department',
        'Carpark': '/transport/car-park/university',
        'Room': '/university/room',
        'Library': '/university/library',
        'SubLibrary': '/university/library/sub-library',
        'Museum': '/leisure/museum',
        'Building': '/university/building',
        'Unit': '/university/unit',
        'Faculty': '/university/faculty',
        'Division': '/university/division',
        'University': '/university',
        'Space': '/university/space',
        'Site': '/university/site',
        'Hall': '/university/hall',
    }

    def __init__(self, indexer, precedence, oxpoints_file, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        self.oxpoints_file = oxpoints_file

    def import_data(self):
        data = json.load(self.oxpoints_file)
        for datum in data:
            try:
                self.process_datum(datum)
            except Exception as e:
                logger.warning("Couldn't process an item: " + e, exc_info=True)
        self.indexer.commit()

    def process_datum(self, datum):
        """
        Process a single OxPoint
        @param datum: dict with item
        """

        oxpoints_id = datum['uri'].rsplit('/')[-1]
        oxpoints_type = datum['type'].rsplit('#')[-1]
        name = datum.get('oxp_fullyQualifiedTitle', datum.get('dc_title', ''))

        if not oxpoints_type in self.OXPOINTS_TYPES:
            return

        if not name:
            return

        doc = dict()
        doc['name'] = name
        doc['id'] = 'oxpoints:{0}'.format(oxpoints_id)
        doc['type'] = self.OXPOINTS_TYPES.get(oxpoints_type, '/other')

        if 'geo_lat' in datum and 'geo_long' in datum:
            doc['location'] = "%s,%s" % (datum.pop('geo_long'), datum.pop('geo_lat'))
        else:
            return

        ids = list()
        ids.append(doc['id'])

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

        """
        Address properties:
        "vCard_postal-code":"OX2 6JF",
        "vCard_locality":"Oxford",
        "vCard_extended-address":"St Antony's College",
        "vCard_street-address":"62 Woodstock Road"},
        """
        address = "{0} {1}".format(datum.get("vCard_street-address", ""), datum.get("vCard_postal-code", ""))
        doc['address'] = " ".join(address.split())

        if 'foaf_homepage' in datum:
            doc['website'] = datum['foaf_homepage']

        doc.update([('raw_oxpoints_{0}'.format(k), v) for k, v in datum.items()])

        for k, v in doc.items():
            if type(v) not in [str, unicode] and k != self.identifier_key:
                doc.pop(k)

        search_results = self.indexer.search_for_ids(
            self.identifier_key, doc[self.identifier_key])
        result = prepare_document(doc, search_results.json, self.precedence)
        result = [result]
        self.indexer.index(result)


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
