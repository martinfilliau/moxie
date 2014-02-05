import json
import logging
import rdflib
from rdflib import RDF
from rdflib.namespace import DC, SKOS, FOAF

from moxie.places.importers.rdf_namespaces import Geo, Geometry, OxPoints, Vcard
from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class OxpointsImporter(object):


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
        'Unit': '/university/department',
        'Faculty': '/university/department',
        'Division': '/university/division',
        'University': '/university',
        'Space': '/university/space',
        'Site': '/university/site',
        'Hall': '/university/hall',
    }

    def __init__(self, indexer, precedence, oxpoints_file, shapes_file, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        graph = rdflib.Graph()
        graph.parse(file=oxpoints_file, format="application/rdf+xml")
        graph.parse(file=shapes_file, format="application/rdf+xml")
        self.graph = graph

    def import_data(self):
        documents = []
        documents.extend(self.process_type(OxPoints.COLLEGE, '/university/college'))
        documents.extend(self.process_type(OxPoints.DEPARTMENT, '/university/department'))
        self.indexer.index(documents)
        self.indexer.commit()

        return

        data = json.load(self.oxpoints_file)
        documents = []
        for datum in data:
            try:
                doc = self.process_datum(datum)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.warning("Couldn't process an item.", exc_info=True)

        self.indexer.index(documents)
        self.indexer.commit()

    def process_type(self, rdf_type, defined_type):
        objects = []
        for subject in self.graph.subjects(RDF.type, rdf_type):
            doc = {}
            doc['name'] = self.graph.value(subject, DC['title']).toPython()
            oxpoints_id = subject.toPython().rsplit('/')[-1]
            oxpoints_id = 'oxpoints:%s' % oxpoints_id
            doc['id'] = oxpoints_id
            doc['type'] = defined_type
            doc['meta_precedence'] = self.precedence     # TODO should use prepare_document

            ids = set()
            ids.add(oxpoints_id)
            ids.update(self._get_identifiers_for_subject(subject))

            site = self.graph.value(subject, OxPoints.PRIMARY_PLACE)
            if site:
                ids.update(self._get_identifiers_for_subject(site))
                if (site, Geo.LAT, None) in self.graph and (site, Geo.LONG, None) in self.graph:
                    doc['location'] = "%s,%s" % (self.graph.value(site, Geo.LAT).toPython(),
                                                 self.graph.value(site, Geo.LONG).toPython())
                site_shape = self.graph.value(site, Geometry.EXTENT)
                if site_shape:
                    doc['shape'] = self.graph.value(site_shape, Geometry.AS_WKT).toPython()

            doc['identifiers'] = list(ids)

            alternative_names = set()
            alternative_names.update(self._get_values_for_property(subject, SKOS['altLabel']))
            alternative_names.update(self._get_values_for_property(subject, SKOS['hiddenLabel']))
            if alternative_names:
                doc['alternative_names'] = list(alternative_names)

            address_node = self.graph.value(subject, Vcard.ADR)
            if address_node:
                address = self._get_address_for_subject(address_node)
                if address:
                    doc['address'] = address

            homepage = self.graph.value(subject, FOAF['homepage'])
            if homepage:
                doc['website'] = homepage.toPython()

            objects.append(doc)
        return objects

    def _get_identifiers_for_subject(self, subject):
        """Find all identifiers for a given subject and
        return them as a list of identifier_type:identifier_value
        :param subject: subject (URI) to inspect
        :return list of identifiers
        """
        ids = []
        for oxp_property, identifier in OxPoints.IDENTIFIERS.items():
            for obj in self.graph.objects(subject, oxp_property):
                val = obj
                if identifier == 'osm':
                    val = val.split('/')[1]
                ids.append('{0}:{1}'.format(identifier, val.replace(' ', '-').replace('/', '-')))
        return ids

    def _get_address_for_subject(self, subject):
        street_address = self.graph.value(subject, Vcard.STREET_ADDRESS)
        postal_code = self.graph.value(subject, Vcard.POSTAL_CODE)

        if street_address or postal_code:
            address = "{0} {1}".format(street_address or '', postal_code or '')
            return " ".join(address.split())
        else:
            return None

    def _get_values_for_property(self, subject, prop):
        """Find all the values for a given subject and property
        :param subject: subject to inspect
        :param prop: property to find
        :return list of values for given property or empty list
        """
        values = []
        for obj in self.graph.objects(subject, prop):
            values.append(obj.toPython())
        return values

    def process_datum(self, datum):
        """
        Process a single OxPoint
        @param datum: dict with item
        """

        doc = dict()

        doc['parent_of'] = []
        doc['child_of'] = []

        if 'dct_isPartOf' in datum:
            parent_id = datum['dct_isPartOf']['uri'].rsplit('/')[-1]
            doc['child_of'].append('oxpoints:{0}'.format(parent_id))

        if 'oxp_occupies' in datum:
            for occupy in datum['oxp_occupies']:
                doc['child_of'].append('oxpoints:{0}'.format(occupy['uri'].rsplit('/')[-1]))

        if 'passiveProperties' in datum:
            if 'dct_isPartOf' in datum['passiveProperties']:
                for child in datum['passiveProperties']['dct_isPartOf']:
                    doc['parent_of'].append('oxpoints:{0}'.format(child['uri'].rsplit('/')[-1]))

        search_results = self.indexer.search_for_ids(
            self.identifier_key, doc[self.identifier_key])
        result = prepare_document(doc, search_results, self.precedence)
        return result


def main():
    #logging.basicConfig(level=logging.DEBUG)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('oxpointsfile', type=argparse.FileType('r'))
    ns = parser.parse_args()
    from moxie.core.search.solr import SolrSearch
    solr = SolrSearch('places', 'http://new-mox.vm:8080/solr/')
    importer = OxpointsImporter(solr, 10, ns.oxpointsfile)
    importer.import_data()


if __name__ == '__main__':
    main()
