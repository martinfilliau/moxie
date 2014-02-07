import logging
import rdflib
from rdflib import RDF
from rdflib.namespace import DC, SKOS, FOAF, DCTERMS

from moxie.places.importers.rdf_namespaces import Geo, Geometry, OxPoints, Vcard, Org
from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)


class OxpointsImporter(object):

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
        documents.extend(self.process_type(OxPoints.FACULTY, '/university/department'))
        documents.extend(self.process_type(OxPoints.UNIT, '/university/department'))
        documents.extend(self.process_type(OxPoints.LIBRARY, '/university/library'))
        documents.extend(self.process_type(OxPoints.SUB_LIBRARY, '/university/sub-library'))
        documents.extend(self.process_type(OxPoints.DIVISION, '/university/division'))
        documents.extend(self.process_type(OxPoints.MUSEUM, '/leisure/museum'))
        documents.extend(self.process_type(OxPoints.CAR_PARK, '/transport/car-park/university'))
        self.indexer.index(documents)
        self.indexer.commit()

    def process_type(self, rdf_type, defined_type):
        objects = []
        for subject in self.graph.subjects(RDF.type, rdf_type):
            doc = {}
            doc['name'] = self.graph.value(subject, DC['title']).toPython()
            doc['id'] = 'oxpoints:%s' % self._get_oxpoints_id(subject)
            doc['type'] = defined_type

            ids = set()
            ids.add(doc['id'])
            ids.update(self._get_identifiers_for_subject(subject))

            site = self.graph.value(subject, OxPoints.PRIMARY_PLACE)
            # attempt to merge a Thing and its Site if it has one
            if site:
                ids.add('oxpoints:%s' % self._get_oxpoints_id(site))
                ids.update(self._get_identifiers_for_subject(site))
                location = self._get_location(site)
                if location:
                    doc['location'] = location
                site_shape = self.graph.value(site, Geometry.EXTENT)
                if site_shape:
                    doc['shape'] = self.graph.value(site_shape, Geometry.AS_WKT).toPython()
            else:
                # else attempt to get a location from the actual thing
                location = self._get_location(subject)
                if location:
                    doc['location'] = location
                else:
                    # if not, try to find location from the parent element
                    parent = self.graph.value(subject, DCTERMS['isPartOf'])
                    if parent:
                        location = self._get_location(parent)
                        if location:
                            doc['location'] = location

            doc[self.identifier_key] = list(ids)

            alternative_names = self._get_alternative_names(subject)
            if alternative_names:
                doc['alternative_names'] = alternative_names

            address_node = self.graph.value(subject, Vcard.ADR)
            if address_node:
                address = self._get_address_for_subject(address_node)
                if address:
                    doc['address'] = address

            homepage = self.graph.value(subject, FOAF['homepage'])
            if homepage:
                doc['website'] = homepage.toPython()

            social_accounts = self._get_values_for_property(subject, FOAF['account'])
            if social_accounts:
                for account in social_accounts:
                    if 'facebook.com' in account:
                        doc['_social_facebook'] = account
                    elif 'twitter.com' in account:
                        doc['_social_twitter'] = account

            logo = self.graph.value(subject, FOAF['logo'])
            if logo:
                doc['_picture_logo'] = logo.toPython()

            depiction = self.graph.value(subject, FOAF['depiction'])
            if depiction:
                doc['_picture_depiction'] = depiction.toPython()

            parent_of = self._find_inverse_relations(subject, Org.SUB_ORGANIZATION_OF)
            if parent_of:
                doc['parent_of'] = parent_of

            child_of = self._find_relations(subject, Org.SUB_ORGANIZATION_OF)
            if child_of:
                doc['child_of'] = child_of

            search_results = self.indexer.search_for_ids(self.identifier_key, doc[self.identifier_key])
            result = prepare_document(doc, search_results, self.precedence)

            objects.append(result)
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

    def _find_relations(self, subject, rel_type):
        """Find relations between a given subject and predicate
        :param subject: subject
        :param rel_type: relation URiRef
        :return list of string containing formatted OxPoints identifiers
        """
        relations = []
        for s, p, o in self.graph.triples((subject, rel_type, None)):
            relations.append('oxpoints:%s' % self._get_oxpoints_id(o))
        return relations

    def _find_inverse_relations(self, subject, rel_type):
        """Find inverse relations between a given subject and predicate
        :param subject: subject
        :param rel_type: relation URiRef
        :return list of string containing formatted OxPoints identifiers
        """
        relations = []
        for s, p, o in self.graph.triples((None, rel_type, subject)):
            relations.append('oxpoints:%s' % self._get_oxpoints_id(s))
        return relations

    def _get_address_for_subject(self, subject):
        """Format an address from a given subject
        :param subject: URIRef of a subject having VCard properties
        :return formatted string containing address or None
        """
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

    def _get_oxpoints_id(self, uri_ref):
        """Split an URI to get the OxPoints ID
        :param uri_ref: URIRef object
        :return string representing oxpoints ID
        """
        return uri_ref.toPython().rsplit('/')[-1]

    def _get_location(self, subject):
        if (subject, Geo.LAT, None) in self.graph and (subject, Geo.LONG, None) in self.graph:
            return "%s,%s" % (self.graph.value(subject, Geo.LAT).toPython(),
                              self.graph.value(subject, Geo.LONG).toPython())
        else:
            return None

    def _get_alternative_names(self, subject):
        alternative_names = set()
        alternative_names.update(self._get_values_for_property(subject, SKOS['altLabel']))
        alternative_names.update(self._get_values_for_property(subject, SKOS['hiddenLabel']))
        return list(alternative_names)


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
