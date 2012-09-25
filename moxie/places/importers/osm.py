# -*- coding: utf-8 -*-
import logging

from xml.sax import handler
from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


SHOPS = { 'supermarket': '/amenities/shop/supermarket',
          'bicycle': '/amenities/shop/bicycle',
          'convenience': '/amenities/shop/convenience',
          'hairdresser': '/amenities/shop/hairdresser',
          'book': '/amenities/shop/book',
          }

AMENITIES = { 'atm': '/amenities/atm',
              'bank': '/amenities/bank',            # TODO atm=yes?
              'bar': '/amenities/food-drink/bar',
              'bicycle_parking': '/transport/bicycle-parking',
              'cafe': '/amenities/food-drink/cafe',  # TODO food=yes?
              'cinema': '/leisure/cinema',
              'dentist': '/amenities/health/dentist',
              'doctors': '/amenities/health/doctor',
              'fast_food': '/amenities/food-drink/fast-food',
              'hospital': '/amenities/health/hospital',
              'library': '/amenities/public-library', # TODO is it?
              'parking': '/transport/car-park',
              'pharmacy': '/amenities/health/pharmacy',
              'post_box': '/amenities/post-box',
              'post_office': '/amenities/post-office',
              'pub': '/amenities/food-drink/pub',    # TODO food=yes?
              'recycling': '/amenities/recycling-facility',
              'restaurant': '/amenities/food-drink/restaurant',
              'swimming_pool': '/leisure/swimming-pool',
              'taxi': '/transport/taxi-rank',
              'theatre': '/leisure/theatre',
              'waste_basket': '/amenities/recycling-facility',
              }

class OSMHandler(handler.ContentHandler):

    def __init__(self, indexer, precedence, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        # k/v from OSM that we want to import in our "tags"
        self.indexed_tags = ['cuisine', 'brand', 'brewery', 'operator']
        # We only import element that have one of these key
        self.element_tags = ['amenity', 'shop', 'naptan:AtcoCode']

    def startDocument(self):
        self.tags = {}
        self.valid_node = True
        self.create_count, self.modify_count = 0, 0
        self.delete_count, self.unchanged_count = 0, 0
        self.ignore_count = 0
        self.node_locations = {}

    def startElement(self, name, attrs):
        if name == 'node':
            lon, lat = float(attrs['lon']), float(attrs['lat'])
            id = attrs['id']
            self.node_location = lon, lat
            self.attrs = attrs
            self.id = id
            self.tags = {}
            self.node_locations[id] = lon, lat
        elif name == 'tag':
            self.tags[attrs['k']] = attrs['v']
        elif name == 'way':
            self.nodes = []
            self.tags = {}
            self.attrs = attrs
            self.id = attrs['id']
        elif name == 'nd':
            self.nodes.append(attrs['ref'])

    def endElement(self, element_type):
        if element_type == 'node':
            location = self.node_location
        elif element_type == 'way':
            min_, max_ = (float('inf'), float('inf')), (float('-inf'), float('-inf'))
            for lon, lat in [self.node_locations[n] for n in self.nodes]:
                min_ = min(min_[0], lon), min(min_[1], lat)
                max_ = max(max_[0], lon), max(max_[1], lat)
            location = (min_[0] + max_[0]) / 2, (min_[1] + max_[1]) / 2
        try:
            if self.tags.get('life_cycle', 'in_use') != 'in_use' or self.tags.get('disused') in ('1', 'yes', 'true'):
                return

            if element_type in ['way', 'node'] and any([x in self.tags for x in self.element_tags]):
                result = dict([('raw_osm_%s' % k, v) for k, v in self.tags.items()])
                result['raw_osm_type'] = element_type
                result['raw_osm_version'] = self.attrs['version']

                result[self.identifier_key] = ['osm:%s' % self.id]
                atco = self.tags.get('naptan:AtcoCode', None)
                if atco:
                    result[self.identifier_key].append('atco:%s' % atco)

                result['tags'] = []
                for it in self.indexed_tags:
                    doc_tags = [t.replace('_', ' ').strip() for t in self.tags.get(it, '').split(';')]
                    if doc_tags and doc_tags != ['']:
                        result['tags'].extend(doc_tags)

                # Filter elements depending on amenity / shop tags
                if 'amenity' in self.tags:
                    if self.tags['amenity'] in AMENITIES:
                        result['type'] = AMENITIES[self.tags['amenity']]
                    else:
                        return
                elif 'shop' in self.tags:
                    if self.tags['shop'] in SHOPS:
                        result['type'] = SHOPS[self.tags['shop']]
                    else:
                        return
                else:
                    return

                name = self.tags.get('name', self.tags.get('operator', None))
                if name is None:
                    name = u"↝ %f, %f" % location
                result['name'] = name

                address = "{0} {1} {2} {3}".format(self.tags.get("addr:housename", ""), self.tags.get("addr:housenumber", ""),
                        self.tags.get("addr:street", ""), self.tags.get("addr:postcode", ""))
                result['address'] = " ".join(address.split())

                # TODO handle formatting of phone numbers(?)
                # TODO handle multiple phone numbers(?) (seems to be separated by a "/" in OSM.
                if 'phone' in self.tags:
                    result['phone'] = self.tags['phone']

                if 'url' in self.tags:
                    result['website'] = self.tags['url']

                if 'website' in self.tags:
                    result['website'] = self.tags['website']

                if 'opening_hours' in self.tags:
                    result['opening_hours'] = self.tags['opening_hours']

                if 'collection_times' in self.tags:
                    result['collection_times'] = self.tags['collection_times']

                result['location'] = "%s,%s" % location
                search_results = self.indexer.search_for_ids(
                        self.identifier_key, result[self.identifier_key])
                result = prepare_document(result, search_results.json, self.precedence)
                result = [result]
                self.indexer.index(result)
        except Exception as e:
            logger.warning("Couldn't index a POI: " + e, exc_info=True)

    def endDocument(self):
        self.indexer.commit()


def main():
    import argparse
    from xml.sax import make_parser
    parser = argparse.ArgumentParser()
    parser.add_argument('osmfile', type=argparse.FileType('r'))
    ns = parser.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('collection1')
    handler = OSMHandler(solr, 5)

    parser = make_parser(['xml.sax.xmlreader.IncrementalParser'])
    parser.setContentHandler(handler)
    # Parse in 8k chunks
    osm = ns.osmfile
    buffer = osm.read(8192)
    # bunzip = bz2.BZ2Decompressor()
    while buffer:
        parser.feed(buffer)
        buffer = osm.read(8192)
    parser.close()

if __name__ == '__main__':
    main()
