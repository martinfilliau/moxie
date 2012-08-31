import logging
import uuid

from lxml import etree
from collections import defaultdict

from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


def tag_handler(tag):
    def wrapper(f):
        tags = getattr(f, 'tags', [])
        tags.append(tag)
        tags = setattr(f, 'tags', tags)
        return f
    return wrapper


class NaptanXMLHandler(object):

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

    def split_namespace(self, tag):
        if self.namespaced is None:
            if '}' in tag:
                self.namespaced = True
            else:
                self.namespaced = False
        if self.namespaced:
            namespace, tag = tag.split('}')
            return namespace[1:], tag
        else:
            return None, tag

    def start(self, tag, attrib):
        ns, tag = self.split_namespace(tag)
        self.skip_element = False
        if attrib.get('Status', 'active') != 'active':
            self.skip_element = True
            return
        self.tag_stack.append(tag)
        if tag in ['StopArea', 'StopPoint']:
            self.element_data = defaultdict(str)
            self.tag_stack = []
            self.capture_data = True

    def end(self, tag):
        ns, tag = self.split_namespace(tag)
        if self.capture_data and not self.skip_element:
            if tag in self.tag_handlers:
                th = self.tag_handlers[tag]
                th(self.element_data)
                self.element_data = None
                self.capture_data = False
                self.flexible_zone = False
            else:
                self.tag_stack.pop()

    def data(self, data):
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
            data[self.identifier_key] = ["stoparea:%s" % sa['StopAreaCode']]
            lon, lat = (sa.pop('Location_Translation_Longitude'),
                    sa.pop('Location_Translation_Latitude'))
            data['location'] = "%s,%s" % (lon, lat)
            data['name'] = sa['Name']
            data['tags'] = ['bus stop area']
            data['id'] = str(uuid.uuid1())
            self.stop_areas[sa['StopAreaCode']] = data

    @tag_handler('StopPoint')
    def add_stop(self, sp):
        """Set the location to our agreed format of lon,lat and pick a
        friendly name. We also apply a busstop tag """
        sp.default_factory = None
        area_code = sp['AtcoCode'][:3]
        if area_code in self.areas:
            data = dict([('raw_naptan_%s' % k, v) for k, v in sp.items()])
            data[self.identifier_key] = ["atco:%s" % sp['AtcoCode']]
            lon, lat = (sp.pop('Place_Location_Translation_Longitude'),
                    sp.pop('Place_Location_Translation_Latitude'))
            data['location'] = "%s,%s" % (lon, lat)
            if 'Descriptor_Indicator' in sp:
                data['name'] = "%s - %s" % (sp['Descriptor_CommonName'], sp['Descriptor_Indicator'])
            else:
                data['name'] = sp['Descriptor_CommonName']
            data['tags'] = ['bus stop']
            data['id'] = str(uuid.uuid1())
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

    def close(self):
        areas = self.annotate_stop_area_ancestry(self.stop_areas)
        stop_points, stop_areas = self.annotate_stop_point_ancestry(self.stop_points, areas)
        return stop_points, stop_areas


class NaPTANImporter(object):
    def __init__(self, indexer, precedence, naptan_file, areas,
            identifier_key='identifiers', buffer_size=8192,
            xml_parser=NaptanXMLHandler):
        self.indexer = indexer
        self.precedence = precedence
        self.naptan_file = naptan_file
        self.areas = areas
        self.identifier_key = identifier_key
        self.buffer_size = buffer_size
        self.xml_parser = xml_parser(self.areas, self.identifier_key)

    def run(self):
        parser = etree.XMLParser(target=self.xml_parser)
        buffered_data = self.naptan_file.read(self.buffer_size)
        while buffered_data:
            parser.feed(buffered_data)
            buffered_data = self.naptan_file.read(self.buffer_size)
        stop_points, stop_areas = parser.close()
        for stop_area_code, data in stop_areas.items():
            search_results = self.indexer.search_for_ids(
                'identifiers', data['identifiers'])
            doc = prepare_document(data, search_results.json, 10)
            doc = [doc]
            self.indexer.index(doc)
        for atco_code, sp in stop_points.items():
            search_results = self.indexer.search_for_ids(
                'identifiers', sp['identifiers'])
            doc = prepare_document(sp, search_results.json, 10)
            doc = [doc]
            self.indexer.index(doc)


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
