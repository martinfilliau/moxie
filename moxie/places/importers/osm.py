import logging
import uuid

from xml.sax import handler, make_parser
from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class OSMHandler(handler.ContentHandler):

    def __init__(self, indexer, precedence, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key

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
        if element_type in ['way', 'node'] and any([x in self.tags for x in ['amenity', 'naptan:AtcoCode']]):
            result = dict([('raw_osm_%s' % k, v) for k, v in self.tags.items()])
            result['raw_osm_type'] = element_type
            result['raw_osm_version'] = self.attrs['version']
            result[self.identifier_key] = ['osm:%s' % self.id]
            atco = self.tags.get('naptan:AtcoCode', None)
            if atco:
                result[self.identifier_key].append('atco:%s' % atco)
            # Some ameneties do not have names, this is correct behaviour.
            # For example, post boxes and car parks.
            result['name'] = self.tags.get('name', self.tags.get('operator', None))
            if result['name']:
                result['location'] = "%s,%s" % location
                search_results = self.indexer.search_for_ids(
                        self.identifier_key, result[self.identifier_key])
                result = prepare_document(result, search_results.json, self.precedence)
                result = [result]
                self.indexer.index(result)

    def endDocument(self):
        pass

def main():
    import argparse
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
