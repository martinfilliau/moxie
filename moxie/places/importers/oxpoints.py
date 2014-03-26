import logging

import rdflib
from rdflib import RDF
from rdflib.namespace import DC, SKOS, FOAF, DCTERMS, RDFS

from moxie.places.importers.rdf_namespaces import (Geo, Geometry, OxPoints, VCard,
                                                   Org, OpenVocab, LinkingYou, Accessibility,
                                                   AdHocDataOx, EntranceOpeningType, ParkingType,
                                                   Rooms, Levelness)
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
    ('_picture_logo', FOAF.logo),
    ('_picture_depiction', FOAF.depiction),
    ('_accessibility_access_guide_url', LinkingYou['space-accessibility']),
    ('_accessibility_has_hearing_system', Accessibility.hasHearingSystem),
    ('_accessibility_has_quiet_space', Accessibility.hasQuietSpace),
    ('_accessibility_has_cafe_refreshments', Accessibility.hasCafeRefreshments),
    ('_accessibility_has_adapted_furniture', Accessibility.hasAdaptedFurniture),
    ('_accessibility_has_computer_access', Accessibility.hasComputerAccess),
    ('_accessibility_has_lifts_to_all_floors', Accessibility.liftsToAllFloors),
    ('_accessibility_number_of_accessible_toilets', Accessibility.numberOfAccessibleToilets),
    ('_accessibility_number_of_floors', Accessibility.numberOfFloors),
    ('_accessibility_opening_hours_closed', AdHocDataOx.openingHoursClosed),
    ('_accessibility_opening_hours_term_time', AdHocDataOx.openingHoursTermTime),
    ('_accessibility_opening_hours_vacation', AdHocDataOx.openingHoursVacation),
    ('_accessibility_floorplan', Accessibility.floorplan),
    ('_accessibility_building_image', AdHocDataOx.accessGuideImage),
]

ENTRANCE_OPENING_TYPES = {
    EntranceOpeningType.ManualDoor: 'Manual door',
    EntranceOpeningType.PoweredDoor: 'Powered door',
    EntranceOpeningType.AutomaticDoor: 'Automatic door',
}

ENTRANCE_LEVEL_TYPES = {
    Levelness.Level: 'Level',
    Levelness.NotLevel: 'Not level',
    Levelness.PlatformLift: 'Platform lift',
    Levelness.StairLift: 'Stair lift'
}

PARKING_TYPES = {
    ParkingType.BlueBadge: 'Blue Badge',
    ParkingType.PayAndDisplay: 'Pay and Display'
}

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

    def __init__(self, indexer, precedence, oxpoints_file, shapes_file, accessibility_file, identifier_key='identifiers'):
        self.indexer = indexer
        self.precedence = precedence
        self.identifier_key = identifier_key
        graph = rdflib.Graph()
        RDF_MEDIA_TYPE = 'text/turtle'  # default RDF serialization
        graph.parse(oxpoints_file, format=RDF_MEDIA_TYPE)
        graph.parse(shapes_file, format=RDF_MEDIA_TYPE)
        graph.parse(accessibility_file, format=RDF_MEDIA_TYPE)
        self.graph = graph
        self.merged_things = []     # list of building/sites merged into departments

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
            logger.info('Ignoring {subject} -- merged with Thing already'.format(subject=subject.toPython()))
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
                    # adding accessibility data of the site to the doc
                    # this happens when a building == an organisation
                    # e.g. Sackler Library -- makes sense to merge accessibility data
                    doc.update(self._handle_accessibility_data(main_site))
                    doc.update(self._handle_mapped_properties(main_site))

            if not main_site_id:
                # Thing and its main site haven't been merged
                # adding a relation between the site and the thing
                parent_of.add(self._get_formatted_oxpoints_id(main_site))

            doc.update(self._handle_location(main_site))
            doc.update(self._handle_shape(main_site))
        else:
            # else attempt to get a location from the actual thing
            doc.update(self._handle_shape(subject))
            doc.update(self._handle_location(subject))

            if 'location' not in doc:
                # try to find location from the parent element
                parent = self.graph.value(subject, DCTERMS.isPartOf)
                if parent:
                    doc.update(self._handle_location(parent))

        doc[self.identifier_key] = list(ids)

        doc.update(self._handle_alternative_names(subject))

        doc.update(self._handle_address_data(subject))

        doc.update(self._handle_social_accounts(subject))

        doc.update(self._handle_mapped_properties(subject))

        if '_accessibility_has_access_guide_information' not in doc:
            # no access info from main site, attempt to get from the thing directly
            doc.update(self._handle_accessibility_data(subject))

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

    def _get_formatted_oxpoints_id(self, uri_ref):
        """Split an URI to get the OxPoints ID
        :param uri_ref: URIRef object
        :return string representing oxpoints ID
        """
        return 'oxpoints:%s' % uri_ref.toPython().rsplit('/')[-1]

    def _handle_location(self, subject):
        if (subject, Geo.lat, None) in self.graph and (subject, Geo.long, None) in self.graph:
            lat = self.graph.value(subject, Geo.lat).toPython()
            lon = self.graph.value(subject, Geo.long).toPython()
            return {'location': "{lat},{lon}".format(lat=lat, lon=lon)}
        else:
            return {}

    def _handle_shape(self, subject):
        shape = self.graph.value(subject, Geometry.extent)
        if shape:
            return {'shape': self.graph.value(shape, Geometry.asWKT).toPython()}
        else:
            return {}

    def _handle_alternative_names(self, subject):
        alternative_names = set()
        alternative_names.update(self._get_values_for_property(subject, SKOS.altLabel))
        alternative_names.update(self._get_values_for_property(subject, SKOS.hiddenLabel))
        alternative_names.update(self._get_values_for_property(subject, AdHocDataOx.accessGuideBuildingName))
        alternative_names.update(self._get_values_for_property(subject, AdHocDataOx.accessGuideBuildingContents))
        alt_names = list(alternative_names)
        if alt_names:
            return {'alternative_names': alt_names}
        else:
            return {}

    def _handle_accessibility_data(self, subject):
        """Handle data from the accessibility guide
        """
        values = {}

        accessibility_parking_type = self.graph.value(subject, Accessibility.nearbyParkingType)
        if accessibility_parking_type:
            values['_accessibility_parking_type'] = PARKING_TYPES.get(accessibility_parking_type)

        accessibility_number_of_accessible_toilets = self.graph.value(subject, Accessibility.numberOfAccessibleToilets)
        if accessibility_number_of_accessible_toilets:
            number = accessibility_number_of_accessible_toilets.toPython()
            if number > 0:
                values['_accessibility_has_accessible_toilets'] = True
            else:
                values['_accessibility_has_accessible_toilets'] = False

        accessibility_guide_url = self.graph.value(subject, LinkingYou['space-accessibility'])
        if accessibility_guide_url:
            values['_accessibility_has_access_guide_information'] = True

        accessibility_contact = self.graph.value(subject, Accessibility.contact)
        if accessibility_contact:
            accessibility_contact_name = self.graph.value(accessibility_contact, RDFS.label)
            if accessibility_contact_name:
                values['_accessibility_contact_name'] = accessibility_contact_name.toPython()
            accessibility_contact_email = self.graph.value(accessibility_contact, VCard.email)
            if accessibility_contact_email:
                values['_accessibility_contact_email'] = accessibility_contact_email.toPython()
            accessibility_contact_tel = self.graph.value(accessibility_contact, VCard.tel)
            if accessibility_contact_tel:
                values['_accessibility_contact_tel'] = accessibility_contact_tel.toPython()

        primary_entrance = self.graph.value(subject, Rooms.primaryEntrance)
        if primary_entrance:
            entrance_opening_type = self.graph.value(primary_entrance, Accessibility.entranceOpeningType)
            if entrance_opening_type:
                entrance_value = ENTRANCE_OPENING_TYPES.get(entrance_opening_type)
                if not entrance_value:
                    logger.warning('No entrance opening type value found for {entrance_type}'.format(entrance_type=entrance_opening_type.toPython()))
                else:
                    values['_accessibility_primary_entrance_opening_type'] = entrance_value
            levelness = self.graph.value(primary_entrance, Accessibility.levelness)
            if levelness:
                levelness_value = ENTRANCE_LEVEL_TYPES.get(levelness)
                if not levelness_value:
                    logger.warning('No entrance level type value found for {entrance_type}'.format(entrance_type=levelness.toPython()))
                else:
                    values['_accessibility_primary_entrance_levelness'] = levelness_value

        return values

    def _handle_social_accounts(self, subject):
        doc = {}
        social_accounts = self._get_values_for_property(subject, FOAF.account)
        if social_accounts:
            for account in social_accounts:
                if 'facebook.com' in account:
                    doc['_social_facebook'] = account
                elif 'twitter.com' in account:
                    doc['_social_twitter'] = account
        return doc

    def _handle_address_data(self, subject):
        address_node = self.graph.value(subject, VCard.adr)
        if address_node:
            address = self._get_address_for_subject(address_node)
            if address:
                return {'address': address}
        return {}

    def _handle_mapped_properties(self, subject):
        values = {}
        # defined properties that matches our structure
        for prop, rdf_prop in MAPPED_PROPERTIES:
            val = self.graph.value(subject, rdf_prop)
            if val is not None:
                values[prop] = val.toPython()
        return values


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
