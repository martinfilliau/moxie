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

    def __init__(self, areas, indexer, precedence, identifier_key='identifiers'):
        self.areas = areas
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        self.prev_tag = None
        self.element_data = None
        self.capture_data = False
        self.stop_points = dict()
        self.stop_areas = dict()
        self.tag_handlers = dict()
        self.namespaced = None
        self.debug_print = False
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
        self.prev_tag = tag
        if tag in ['StopArea', 'StopPoint']:
            self.tag_counts = defaultdict(int)
            self.element_data = defaultdict(str)
            self.capture_data = True

    def end(self, tag):
        ns, tag = self.split_namespace(tag)
        if self.capture_data and not self.skip_element:
            if tag in self.tag_handlers:
                th = self.tag_handlers[tag]
                th(self.element_data)
                self.element_data = None
                self.capture_data = False
                self.debug_print = False

    def data(self, data):
        if self.capture_data and not self.skip_element:
            if self.prev_tag in ['Latitude', 'Longitude']:
                self.tag_counts[self.prev_tag] += 1
                self.element_data[self.prev_tag] += data
                try:
                    float(self.element_data[self.prev_tag])
                except Exception as e:
                    print self.tag_counts
                    self.debug_print = True
            else:
                self.element_data[self.prev_tag] += data
            self.element_data[self.prev_tag] = self.element_data[self.prev_tag].strip()

    @tag_handler('StopArea')
    def add_stop_area(self, sa):
        area_code = sa['StopAreaCode'][:3]
        if area_code in self.areas:
            data = dict([('raw_naptan_%s' % k, v) for k, v in sa.items()])
            data[self.identifier_key] = ["atco:%s" % sa['StopAreaCode']]
            lon, lat = sa.pop('Longitude'), sa.pop('Latitude')
            data['location'] = "%s,%s" % (lon, lat)
            data['name'] = sa['CommonName']
            data['id'] = str(uuid.uuid1())
            self.stop_areas[sa['StopAreaCode']] = data

    @tag_handler('StopPoint')
    def add_stop(self, sp):
        """If within our set of areas then store to be indexed"""
        area_code = sp['AtcoCode'][:3]
        if area_code in self.areas:
            data = dict([('raw_naptan_%s' % k, v) for k, v in sp.items()])
            data[self.identifier_key] = ["atco:%s" % sp['AtcoCode']]
            lon, lat = sp.pop('Longitude'), sp.pop('Latitude')
            data['location'] = "%s,%s" % (lon, lat)
            data['name'] = sp['CommonName']
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
            if 'raw_naptan_StopAreaRef' in sp:
                try:
                    parent_area = stop_areas[sp['raw_naptan_StopAreaRef']]
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


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('naptanfile', type=argparse.FileType('r'))
    ns = args.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('collection1')

    buffer_size = 8192
    naptan = ns.naptanfile
    parser = etree.XMLParser(target=NaptanXMLHandler(['340'], solr, 10))
    buffered_data = naptan.read(buffer_size)
    while buffered_data:
        parser.feed(buffered_data)
        buffered_data = naptan.read(buffer_size)
    stop_points, stop_areas = parser.close()
    for stop_area_code, data in stop_areas.items():
        search_results = solr.search_for_ids(
            'identifiers', data['identifiers'])
        doc = prepare_document(data, search_results.json, 10)
        doc = [doc]
        solr.index(doc)
    for atco_code, sp in stop_points.items():
        search_results = solr.search_for_ids(
            'identifiers', sp['identifiers'])
        doc = prepare_document(sp, search_results.json, 10)
        doc = [doc]
        solr.index(doc)

if __name__ == '__main__':
    main()
