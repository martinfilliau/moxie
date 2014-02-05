import json
import logging
import rdflib
from rdflib import RDF
from rdflib.term import URIRef
from rdflib.namespace import DC, SKOS


from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class OxPoints(object):

    _BASE = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'
    SITE = URIRef(_BASE+'Site')
    COLLEGE = URIRef(_BASE+'College')
    DEPARTMENT = URIRef(_BASE+'Department')
    PRIMARY_PLACE = URIRef(_BASE+'primaryPlace')
    IDENTIFIERS = {
        _BASE+'hasOUCSCode': 'oucs',
        _BASE+'hasOLISCode': 'olis',
        _BASE+'hasOLISAlephCode': 'olis-aleph',
        _BASE+'hasOSMIdentifier': 'osm',
        _BASE+'hasFinanceCode': 'finance',
        _BASE+'hasOBNCode': 'obn',
        _BASE+'hasLibraryDataId': 'librarydata'
    }


class Org(object):

    _BASE = 'http://www.w3.org/ns/org#'
    HAS_PRIMARY_SITE = URIRef(_BASE+"hasPrimarySite")


class Geo(object):

    _BASE = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
    LAT = URIRef(_BASE+'lat')
    LONG = URIRef(_BASE+'long')


class Geometry(object):

    _BASE = 'http://data.ordnancesurvey.co.uk/ontology/geometry/'
    AS_WKT = URIRef(_BASE+'asWKT')
    EXTENT = URIRef(_BASE+'extent')


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
        documents.extend(self.process_type(OxPoints.COLLEGE))
        documents.extend(self.process_type(OxPoints.DEPARTMENT))
        print documents
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

    def process_type(self, type):
        objects = []
        for subject in self.graph.subjects(RDF.type, type):
            doc = {}
            doc['name'] = self.graph.value(subject, DC['title']).toPython()
            oxpoints_id = subject.toPython().rsplit('/')[-1]
            oxpoints_id = 'oxpoints:%s' % oxpoints_id
            doc['id'] = oxpoints_id

            ids = set()
            ids.add(oxpoints_id)
            ids.update(self._get_identifiers_for_subject(subject))

            site = self.graph.value(subject, OxPoints.PRIMARY_PLACE)
            if site:
                ids.update(self._get_identifiers_for_subject(site))
                if (site, Geo.LAT, None) in self.graph and (site, Geo.LONG, None) in self.graph:
                    doc['lat'] = self.graph.value(site, Geo.LAT).toPython()
                    doc['long'] = self.graph.value(site, Geo.LONG).toPython()
                site_shape = self.graph.value(site, Geometry.EXTENT)
                if site_shape:
                    doc['shape'] = self.graph.value(site_shape, Geometry.AS_WKT).toPython()

            doc['identifiers'] = ids

            alternative_names = set()
            alternative_names.update(self._get_values_for_property(subject, SKOS['altLabel']))
            alternative_names.update(self._get_values_for_property(subject, SKOS['hiddenLabel']))
            if alternative_names:
                doc['alternative_names'] = alternative_names

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

        oxpoints_id = datum['uri'].rsplit('/')[-1]
        oxpoints_type = datum['type'].rsplit('#')[-1]
        name = datum.get('dc_title', datum.get('oxp_fullyQualifiedTitle', ''))

        # Do not index items without name or not in the list of types defined
        if not oxpoints_type in self.OXPOINTS_TYPES or not name:
            return

        doc = dict()
        doc['name'] = name
        doc['id'] = 'oxpoints:{0}'.format(oxpoints_id)
        doc['type'] = self.OXPOINTS_TYPES[oxpoints_type]

        if 'geo_lat' in datum and 'geo_long' in datum:
            doc['location'] = "%s,%s" % (datum.pop('geo_lat'), datum.pop('geo_long'))

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

        # Adding alternative names (alt, hidden) to the full-text search
        alternative_names = set()
        if 'skos_altLabel' in datum:
            alternative_names.update(datum.get('skos_altLabel'))
        if 'skos_hiddenLabel' in datum:
            alternative_names.update(datum.get('skos_hiddenLabel'))
        if alternative_names:
            doc['alternative_names'] = list(alternative_names)

        """
        Address properties:
        "vCard_postal-code":"OX2 6JF",
        "vCard_locality":"Oxford",
        "vCard_extended-address":"St Antony's College",
        "vCard_street-address":"62 Woodstock Road"},
        """
        address = "{0} {1}".format(datum.get("vCard_street-address", ""), datum.get("vCard_postal-code", ""))
        doc['address'] = " ".join(address.split())

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

        if 'foaf_homepage' in datum:
            doc['website'] = datum['foaf_homepage']

        # Add all other k/v to the doc, and then remove everythign but strings...
        # ... useless
        #doc.update([('raw_oxpoints_{0}'.format(k), v) for k, v in datum.items()])
        #for k, v in doc.items():
        #    if type(v) not in [str, unicode] and k != self.identifier_key:
        #        doc.pop(k)

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
