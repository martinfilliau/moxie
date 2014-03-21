import logging
import rdflib
import json
from rdflib import RDF
from rdflib.namespace import DC, SKOS, FOAF, DCTERMS

from moxie.places.importers.rdf_namespaces import Geo, Geometry, OxPoints, VCard, Org, OpenVocab
from moxie.places.importers.helpers import prepare_document

logger = logging.getLogger(__name__)

MAPPED_TYPES = [
    (OxPoints.University, '/university'),
    (OxPoints.College, '/university/college'),
    (OxPoints.Department, '/university/department'),
    (OxPoints.Faculty, '/university/department'),
    (OxPoints.Unit, '/university/department'),
    (OxPoints.Library, '/university/library'),
    (OxPoints.SubLibrary, '/university/sub-library'),
    (OxPoints.Division, '/university/division'),
    (OxPoints.Museum, '/leisure/museum'),
    (OxPoints.CarPark, '/transport/car-park/university'),
    (OxPoints.Room, '/university/room'),
    (OxPoints.Hall, '/university/hall'),
    (OxPoints.Building, '/university/building'),
    (OxPoints.Space, '/university/space'),
    (OxPoints.Site, '/university/site')
]

# properties which maps "easily" to our structure
MAPPED_PROPERTIES = [
    ('website', FOAF.homepage),
    ('short_name', OxPoints.shortLabel),
]

OXPOINTS_IDENTIFIERS = {
    OxPoints.hasOUCSCode: 'oucs',
    OxPoints.hasOLISCode: 'olis',
    OxPoints.hasOLISAlephCode: 'olis-aleph',
    OxPoints.hasOSMIdentifier: 'osm',
    OxPoints.hasFinanceCode: 'finance',
    OxPoints.hasOBNCode: 'obn',
    OxPoints.hasLibraryDataId: 'librarydata'
}

class OxpointsImporter(object):

    def __init__(self, indexer, precedence, oxpoints_file, shapes_file, static_files_dir, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        graph = rdflib.Graph()
        graph.parse(file=oxpoints_file, format="application/rdf+xml")
        graph.parse(file=shapes_file, format="application/rdf+xml")
        self.graph = graph
        self.merged_things = []     # list of building/sites merged into departments
        if not static_files_dir:
            logger.warning('STATIC_FILES_IMPORT_DIRECTORY not set, images will not be imported')
        self.static_files_dir = static_files_dir

    def import_data(self):
        documents = []
        for oxpoints_type, mapped_type in MAPPED_TYPES:
            documents.extend(self.process_type(oxpoints_type, mapped_type))
        self.indexer.index(documents)
        self.indexer.commit()

    def process_type(self, rdf_type, defined_type):
        """Browse the graph for a certain type and process found subjects
        :param rdf_type: RDF type to find
        :param defined_type: type defining subjects found
        :return list of documents
        """
        objects = []
        for subject in self.graph.subjects(RDF.type, rdf_type):
            try:
                doc = self.process_subject(subject, defined_type)
                if doc:
                    search_results = self.indexer.search_for_ids(self.identifier_key, doc[self.identifier_key])
                    result = prepare_document(doc, search_results, self.precedence)
                    objects.append(result)
            except Exception:
                logger.warning('Could not process subject', exc_info=True,
                               extra={'data': {'subject': subject.toPython()}})
        return objects

    def process_subject(self, subject, mapped_type):
        """Prepare a document from a Subject by browsing the RDF graph
        :param subject: subject URIRef
        :return dict
        """
        title = self.graph.value(subject, DC.title)
        if not title:
            return None
        else:
            title = title.toPython()

        if subject in self.merged_things:
            logger.info('Ignoring %s -- merged with Thing already' % subject.toPython())
            return None

        doc = {}
        doc['name'] = title
        doc['id'] = self._get_formatted_oxpoints_id(subject)
        doc['type'] = mapped_type

        sort_label = self.graph.value(subject, OpenVocab.SORT_LABEL)
        if sort_label:
            doc['name_sort'] = sort_label.toPython()
        else:
            doc['name_sort'] = title

        ids = set()
        ids.add(doc['id'])
        ids.update(self._get_identifiers_for_subject(subject))

        parent_of = set()
        child_of = set()

        main_site = self.graph.value(subject, OxPoints.primaryPlace)
        main_site_id = None

        # attempt to merge a Thing and its Site if it has one
        if main_site:
            site_title = self.graph.value(main_site, DC.title)
            if site_title:
                site_title = site_title.toPython()

                # if the main_site has the same name that the Thing, then merge
                # them and do not import the Site by itself
                if site_title == title:
                    main_site_id = self._get_formatted_oxpoints_id(main_site)
                    ids.add(main_site_id)
                    ids.update(self._get_identifiers_for_subject(main_site))
                    self.merged_things.append(main_site)

            if not main_site_id:
                # Thing and its main site haven't been merged
                # adding a relation between the site and the thing
                parent_of.add(self._get_formatted_oxpoints_id(main_site))

            location = self._get_location(main_site)
            if location:
                doc['location'] = location
            shape = self._get_shape(main_site)
            if shape:
                doc['shape'] = shape
        else:
            # else attempt to get a location from the actual thing
            shape = self._get_shape(subject)
            if shape:
                doc['shape'] = shape
            location = self._get_location(subject)
            if location:
                doc['location'] = location
            else:
                # if not, try to find location from the parent element
                parent = self.graph.value(subject, DCTERMS.isPartOf)
                if parent:
                    location = self._get_location(parent)
                    if location:
                        doc['location'] = location

        doc[self.identifier_key] = list(ids)

        alternative_names = self._get_alternative_names(subject)
        if alternative_names:
            doc['alternative_names'] = alternative_names

        address_node = self.graph.value(subject, VCard.adr)
        if address_node:
            address = self._get_address_for_subject(address_node)
            if address:
                doc['address'] = address

        social_accounts = self._get_values_for_property(subject, FOAF.account)
        if social_accounts:
            for account in social_accounts:
                if 'facebook.com' in account:
                    doc['_social_facebook'] = account
                elif 'twitter.com' in account:
                    doc['_social_twitter'] = account

        # defined properties that matches our structure
        for prop, rdf_prop in MAPPED_PROPERTIES:
            val = self.graph.value(subject, rdf_prop)
            if val is not None:
                doc[prop] = val.toPython()

        images = []
        images.extend(self._get_images(subject, FOAF.depiction))
        images.extend(self._get_images(subject, FOAF.logo))
        doc['images'] = images

        parent_of.update(self._find_inverse_relations(subject, Org.subOrganizationOf))
        parent_of.update(self._find_relations(subject, Org.hasSite))
        parent_of.update(self._find_inverse_relations(subject, DCTERMS.isPartOf))
        parent_of.discard(main_site_id)
        if parent_of:
            doc['parent_of'] = list(parent_of)

        child_of.update(self._find_relations(subject, Org.subOrganizationOf))
        child_of.update(self._find_inverse_relations(subject, Org.hasSite))
        child_of.update(self._find_relations(subject, DCTERMS.isPartOf))
        if child_of:
            doc['child_of'] = list(child_of)

        return doc

    def _get_identifiers_for_subject(self, subject):
        """Find all identifiers for a given subject and
        return them as a list of identifier_type:identifier_value
        :param subject: subject (URI) to inspect
        :return list of identifiers
        """
        ids = []
        for oxp_property, identifier in OXPOINTS_IDENTIFIERS.items():
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
            relations.append(self._get_formatted_oxpoints_id(o))
        return relations

    def _find_inverse_relations(self, subject, rel_type):
        """Find inverse relations between a given subject and predicate
        :param subject: subject
        :param rel_type: relation URiRef
        :return list of string containing formatted OxPoints identifiers
        """
        relations = []
        for s, p, o in self.graph.triples((None, rel_type, subject)):
            relations.append(self._get_formatted_oxpoints_id(s))
        return relations

    def _get_address_for_subject(self, subject):
        """Format an address from a given subject
        :param subject: URIRef of a subject having VCard properties
        :return formatted string containing address or None
        """
        street_address = self.graph.value(subject, VCard['street-address'])
        postal_code = self.graph.value(subject, VCard['postal-code'])

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

    def _get_formatted_oxpoints_id(self, uri_ref, separator=':'):
        """Split an URI to get the OxPoints ID
        :param uri_ref: URIRef object
        :return string representing oxpoints ID
        """
        return 'oxpoints{separator}{ident}'.format(separator=separator,
                                                   ident=uri_ref.toPython().rsplit('/')[-1])

    def _get_location(self, subject):
        if (subject, Geo.lat, None) in self.graph and (subject, Geo.long, None) in self.graph:
            return "%s,%s" % (self.graph.value(subject, Geo.lat).toPython(),
                              self.graph.value(subject, Geo.long).toPython())
        else:
            return None

    def _get_shape(self, subject):
        shape = self.graph.value(subject, Geometry.extent)
        if shape:
            return self.graph.value(shape, Geometry.asWKT).toPython()
        else:
            return None

    def _get_alternative_names(self, subject):
        alternative_names = set()
        alternative_names.update(self._get_values_for_property(subject, SKOS.altLabel))
        alternative_names.update(self._get_values_for_property(subject, SKOS.hiddenLabel))
        return list(alternative_names)

    def _get_files(self, subject, rdf_prop):
        """Get files for given subject and predicate
        Will download the file and store it
        :param subject: subject
        :param rdf_prop: predicate
        :return list of json strings containing source URL and new location
        """
        # TODO can't import it in the file for some reasons??
        from moxie.places.tasks import download_file

        files = []
        for val in self.graph.objects(subject, rdf_prop):
            url = val.toPython()
            file_name = url.split('/')[-1]
            oxpoints_path = self._get_formatted_oxpoints_id(subject, separator='/')
            download_location = '{base}{oxpoints_id}/original/{file_name}'.format(base=self.static_files_dir,
                                                                                  oxpoints_id=oxpoints_path,
                                                                                  file_name=file_name)

            download_file.delay(val.toPython(), download_location)
            image_description = {'location': download_location,
                                 'file_name': file_name,
                                 'source_url': url}
            files.append(json.dumps(image_description))
        return files


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
