# -*- coding: utf-8 -*-
import logging

from xml.sax import handler
from moxie.places.importers.helpers import prepare_document, format_uk_telephone

logger = logging.getLogger(__name__)


DEFAULT_SHOP = '/amenities/shop'

SHOPS = {'supermarket': '/amenities/supermarket',
         'department_store': '/amenities/supermarket',      # TODO supermarket? or just shop?
         'bicycle': '/amenities/shop/bicycle',
         'convenience': '/amenities/supermarket/convenience',
         #'hairdresser': '/amenities/shop/hairdresser',    Disabled due to poor quality of data (TRELLO#144).
         'book': '/amenities/shop/book',
         'mall': DEFAULT_SHOP,
         'deli': DEFAULT_SHOP,
         'doityourself': DEFAULT_SHOP,
         'newsagent': DEFAULT_SHOP
         }

AMENITIES = {'atm': '/amenities/atm',
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
             'post_box': '/amenities/post/post-box',
             'post_office': '/amenities/post/post-office',
             'pub': '/amenities/food-drink/pub',    # TODO food=yes?
             'punt_hire': '/leisure/punt',
             'recycling': '/amenities/recycling-facility',
             'restaurant': '/amenities/food-drink/restaurant',
             'swimming_pool': '/leisure/swimming-pool',
             'taxi': '/transport/taxi-rank',
             'theatre': '/leisure/theatre',
             'waste_basket': '/amenities/recycling-facility',
             }

PARK_AND_RIDE = '/transport/car-park/park-and-ride'


class OSMHandler(handler.ContentHandler):

    def __init__(self, indexer, precedence, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        # k/v from OSM that we want to import in our "tags"
        self.indexed_tags = ['cuisine', 'brand', 'brewery', 'operator']
        # We only import element that have one of these key
        self.element_tags = ['amenity', 'shop', 'naptan:AtcoCode']
        self.pois = []

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
            self.node_location = lat, lon
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
            if self.tags.get('life_cycle', 'in_use') != 'in_use':
                return

            for key in self.tags.iterkeys():
                if 'disused' in key:
                    # e.g. disused:amenity=restaurant
                    # http://wiki.openstreetmap.org/wiki/Key:disused
                    return

            if element_type in ['way', 'node'] and any([x in self.tags for x in self.element_tags]):
                result = {}
                osm_id = 'osm:%s' % self.id
                atco_id = self.tags.get('naptan:AtcoCode', None)
                result[self.identifier_key] = [osm_id]
                # if it has an ATCO ID, we set the ATCO ID as the main ID for this document
                # instead of the OSM ID
                if atco_id:
                    result['id'] = atco_id
                    result[self.identifier_key].append('atco:%s' % atco_id)
                else:
                    result['id'] = osm_id

                result['tags'] = []
                for it in self.indexed_tags:
                    doc_tags = [t.replace('_', ' ').strip() for t in self.tags.get(it, '').split(';')]
                    if doc_tags and doc_tags != ['']:
                        result['tags'].extend(doc_tags)

                # Filter elements depending on amenity / shop tags
                if 'amenity' in self.tags:
                    if self.tags['amenity'] in AMENITIES:
                        # special case for Park and Rides where amenity=parking and park_ride=bus/yes/... except no
                        # TODO we should be able to handle this kind of case in a better way
                        if self.tags['amenity'] == "parking" and self.tags.get('park_ride', 'no') != 'no':
                            result['type'] = PARK_AND_RIDE
                        else:
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

                # if the element doesn't have a name, it will be an empty string
                result['name'] = self.tags.get('name', self.tags.get('operator', ''))
                result['name_sort'] = result['name']

                address = "{0} {1} {2} {3}".format(self.tags.get("addr:housename", ""), self.tags.get("addr:housenumber", ""),
                        self.tags.get("addr:street", ""), self.tags.get("addr:postcode", ""))
                result['address'] = " ".join(address.split())

                if 'phone' in self.tags:
                    result['phone'] = format_uk_telephone(self.tags['phone'])

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
                self.pois.append(prepare_document(result, search_results, self.precedence))
        except Exception as e:
            logger.warning("Couldn't index a POI.", exc_info=True)

    def endDocument(self):
        self.indexer.index(self.pois)
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
    while buffer:
        parser.feed(buffer)
        buffer = osm.read(8192)
    parser.close()

if __name__ == '__main__':
    main()
