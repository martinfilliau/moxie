import logging

from xml.sax import handler, make_parser

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class NaptanXMLHandler(handler.ContentHandler):

    def __init__(self, areas, indexer, precedence, identifier_key='identifiers'):
        self.areas = areas
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        self.prev_tag = None
        self.data = None
        self.capture_data = False
        self.results = []

    def startElement(self, name, attrs):
        self.prev_tag = name
        if name == 'StopPoint':
            self.data = dict()
            self.capture_data = True

    def endElement(self, name):
        if name == 'StopPoint':
            self.add_stop(self.data)
            self.data = None
            self.capture_data = False

    def characters(self, content):
        if self.capture_data:
            self.data[self.prev_tag] = content

    def add_stop(self, data):
        """If within our set of areas then store to be indexed"""
        area_code = data['AtcoCode'][:3]
        if area_code in self.areas:
            self.results.append(data)

    def endDocument(self):
        for result in self.results:
            data = dict([('raw_naptan_%s' % k, v) for k, v in result.items()])
            data[self.identifier_key] = ["atco:%s" % result['AtcoCode']]
            data['location'] = "%s,%s" % (result.pop('Longitude'), result.pop('Latitude'))
            data['name'] = result['CommonName']
            search_results = self.indexer.search_for_ids(
                self.identifier_key, data[self.identifier_key])
            doc = prepare_document(data, search_results.json, self.precedence)
            doc = [doc]
            self.indexer.index(doc)

def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('naptanfile', type=argparse.FileType('r'))
    ns = args.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('collection1')

    parser = make_parser(['xml.sax.xmlreader.IncrementalParser'])
    parser.setContentHandler(NaptanXMLHandler(['340'], solr, 10))
    # Parse in 8k chunks
    naptan = ns.naptanfile
    buffer = naptan.read(8192)
    # bunzip = bz2.BZ2Decompressor()
    while buffer:
        parser.feed(buffer)
        buffer = naptan.read(8192)
    parser.close()

if __name__ == '__main__':
    main()