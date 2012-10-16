import logging

from xml.sax import ContentHandler, make_parser
from collections import defaultdict

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)

NAPTAN_MAPPING = {
    'TXR': '/transport/taxi-rank',
    'BCT': '/transport/bus-stop',
    'AIR': '/transport/airport',
}


#if self.meta['stop-type'] in ('AIR', 'FTD', 'RSE', 'TMU', 'BCE'):
#    title = ugettext('Entrance to %s') % common_name
#elif self.meta['stop-type'] in ('FBT',):
#    title = ugettext('Berth at %s') % common_name
#elif self.meta['stop-type'] in ('RPL','PLT'):
## referring to rail and metro stations


def tag_handler(tag):
    def wrapper(f):
        tags = getattr(f, 'tags', [])
        tags.append(tag)
        tags = setattr(f, 'tags', tags)
        return f
    return wrapper


class NaptanXMLHandler(ContentHandler):

    def __init__(self, areas, identifier_key):
        self.areas = areas
        self.identifier_key = identifier_key
        self.tag_stack = []
        self.element_data = None
        self.capture_data = False
        self.flexible_zone = False
        self.stop_points = dict()
        self.stop_areas = dict()
        self.tag_handlers = dict()
        self.namespaced = None
        for attr in dir(self):
            attr = getattr(self, attr)
            tags = getattr(attr, 'tags', [])
            for tag in tags:
                self.tag_handlers[tag] = attr

    def startElement(self, tag, attrib):
        self.skip_element = False
        if attrib.get('Status', 'active') != 'active':
            self.skip_element = True
            return
        self.tag_stack.append(tag)
        if tag in ['StopArea', 'StopPoint']:
            self.element_data = defaultdict(str)
            self.tag_stack = []
            self.capture_data = True

    def endElement(self, tag):
        if self.capture_data and not self.skip_element:
            if tag in self.tag_handlers:
                th = self.tag_handlers[tag]
                th(self.element_data)
                self.element_data = None
                self.capture_data = False
                self.flexible_zone = False
            else:
                self.tag_stack.pop()

    def characters(self, data):
        if self.capture_data and not self.skip_element:
            tag = '_'.join(self.tag_stack)
            self.element_data[tag] += data
            self.element_data[tag] = self.element_data[tag].strip()

    @tag_handler('StopArea')
    def add_stop_area(self, sa):
        sa.default_factory = None
        area_code = sa['StopAreaCode'][:3]
        if area_code in self.areas:
            data = dict([('raw_naptan_%s' % k, v) for k, v in sa.items()])
            data['id'] = "stoparea:%s" % sa['StopAreaCode']
            data[self.identifier_key] = [data['id']]
            lon, lat = (sa.pop('Location_Translation_Longitude'),
                    sa.pop('Location_Translation_Latitude'))
            data['location'] = "%s,%s" % (lon, lat)
            data['name'] = sa['Name']
            data['type'] = "/transport/bus-stop-area"
            self.stop_areas[sa['StopAreaCode']] = data

    @tag_handler('StopPoint')
    def add_stop(self, sp):
        """Set the location to our agreed format of lon,lat and pick a
        friendly name. We also apply a busstop tag """
        sp.default_factory = None
        area_code = sp['AtcoCode'][:3]
        if area_code in self.areas:
            data = dict([('raw_naptan_%s' % k, v) for k, v in sp.items()])
            data['id'] = "atco:%s" % sp['AtcoCode']
            identifiers = []
            identifiers.append(data['id'])
            if 'NaptanCode' in sp:
                naptan_id = ''.join(map(self.naptan_dial, sp['NaptanCode']))
                identifiers.append("naptan:%s" % naptan_id)
            data[self.identifier_key] = identifiers

            # TODO: should add a test for this
            if 'StopClassification_StopType' in sp and sp['StopClassification_StopType'] in NAPTAN_MAPPING:
                data['type'] = NAPTAN_MAPPING[sp['StopClassification_StopType']]
            else:
                return

            lon, lat = (sp.pop('Place_Location_Translation_Longitude'),
                    sp.pop('Place_Location_Translation_Latitude'))
            data['location'] = "%s,%s" % (lon, lat)

            if 'Descriptor_Indicator' in sp:
                indicator = self.get_indicator_name(str(sp['Descriptor_Indicator']))
                data['name'] = "%s %s" % (indicator, sp['Descriptor_CommonName'])
            else:
                data['name'] = sp['Descriptor_CommonName']
            self.stop_points[sp['AtcoCode']] = data

    def annotate_stop_area_ancestry(self, stop_areas):
        for stop_area_code, area in stop_areas.items():
            if 'raw_naptan_ParentStopAreaRef' in area:
                try:
                    parent = stop_areas[area['raw_naptan_ParentStopAreaRef']]
                except KeyError:
                    continue
                if 'child_of' in area:
                    area['child_of'].append(parent['id'])
                else:
                    area['child_of'] = [parent['id']]
                if 'parent_of' in parent:
                    parent['parent_of'].append(area['id'])
                else:
                    parent['parent_of'] = [area['id']]
        return stop_areas

    def annotate_stop_point_ancestry(self, stop_points, stop_areas):
        for atco_code, sp in stop_points.items():
            if 'raw_naptan_StopAreas_StopAreaRef' in sp:
                try:
                    parent_area = stop_areas[sp['raw_naptan_StopAreas_StopAreaRef']]
                except KeyError:
                    continue
                if 'child_of' in sp:
                    sp['child_of'].append(parent_area['id'])
                else:
                    sp['child_of'] = [parent_area['id']]
                if 'parent_of' in parent_area:
                    parent_area['parent_of'].append(sp['id'])
                else:
                    parent_area['parent_of'] = [sp['id']]
        return stop_points, stop_areas

    def endDocument(self):
        areas = self.annotate_stop_area_ancestry(self.stop_areas)
        self.stop_points, self.stop_areas = self.annotate_stop_point_ancestry(self.stop_points, areas)

    @staticmethod
    def get_indicator_name(indicator):
        """
        Get a "friendly" name for the indicator
        @param indicator: indicator's name in Naptan format
        @return: "friendly" name
        """
        parts = []
        for part in indicator.split():
            # TODO plan i18n for this
            parts.append({
                'op': 'Opposite',
                'opp': 'Opposite',
                'opposite': 'Opposite',
                'adj': 'Adjacent',
                'outside': 'Outside',
                'o/s': 'Outside',
                'nr': 'Near',
                'inside': 'Inside',
                'stp': 'Stop',
            }.get(part.lower(), part))
        indicator = ' '.join(parts)
        return indicator

    @staticmethod
    def naptan_dial(c):
        """
        Convert a alphabetical NaPTAN code in the database to the numerical code
        used on bus stops
        """
        if c.isdigit():
            return c
        return unicode(min(9, (ord(c)-91)//3))


class NaPTANImporter(object):
    def __init__(self, indexer, precedence, naptan_file, areas,
            identifier_key='identifiers', buffer_size=8192,
            handler=NaptanXMLHandler):
        self.indexer = indexer
        self.precedence = precedence
        self.naptan_file = naptan_file
        self.areas = areas
        self.identifier_key = identifier_key
        self.buffer_size = buffer_size
        self.handler = handler(self.areas, self.identifier_key)

    def run(self):
        parser = make_parser(['xml.sax.IncrementalParser'])
        parser.setContentHandler(self.handler)
        buffered_data = self.naptan_file.read(self.buffer_size)
        while buffered_data:
            parser.feed(buffered_data)
            buffered_data = self.naptan_file.read(self.buffer_size)
        parser.close()
        for stop_area_code, data in self.handler.stop_areas.items():
            search_results = self.indexer.search_for_ids(
                self.identifier_key, data[self.identifier_key])
            doc = prepare_document(data, search_results.json, self.precedence)
            doc = [doc]
            self.indexer.index(doc)
        for atco_code, sp in self.handler.stop_points.items():
            search_results = self.indexer.search_for_ids(
                self.identifier_key, sp[self.identifier_key])
            doc = prepare_document(sp, search_results.json, self.precedence)
            doc = [doc]
            self.indexer.index(doc)
        self.indexer.commit()


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('naptanfile', type=argparse.FileType('r'))
    ns = args.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('collection1')
    naptan_importer = NaPTANImporter(solr, 10, ns.naptanfile, ['340'], 'identifiers')
    naptan_importer.run()


if __name__ == '__main__':
    main()
