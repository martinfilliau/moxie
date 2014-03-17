from rdflib.term import URIRef


class OxPoints(object):

    _BASE = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'
    SITE = URIRef(_BASE+'Site')
    UNIVERSITY = URIRef(_BASE+'University')
    COLLEGE = URIRef(_BASE+'College')
    DEPARTMENT = URIRef(_BASE+'Department')
    LIBRARY = URIRef(_BASE+'Library')
    SUB_LIBRARY = URIRef(_BASE+'SubLibrary')
    DIVISION = URIRef(_BASE+'Division')
    FACULTY = URIRef(_BASE+'Faculty')
    UNIT = URIRef(_BASE+'Unit')
    ROOM = URIRef(_BASE+'Room')
    HALL = URIRef(_BASE+'Hall')
    MUSEUM = URIRef(_BASE+'Museum')
    BUILDING = URIRef(_BASE+'Building')
    SPACE = URIRef(_BASE+'Space')
    CAR_PARK = URIRef(_BASE+'Carpark')
    PRIMARY_PLACE = URIRef(_BASE+'primaryPlace')
    IDENTIFIERS = {
        URIRef(_BASE+'hasOUCSCode'): 'oucs',
        URIRef(_BASE+'hasOLISCode'): 'olis',
        URIRef(_BASE+'hasOLISAlephCode'): 'olis-aleph',
        URIRef(_BASE+'hasOSMIdentifier'): 'osm',
        URIRef(_BASE+'hasFinanceCode'): 'finance',
        URIRef(_BASE+'hasOBNCode'): 'obn',
        URIRef(_BASE+'hasLibraryDataId'): 'librarydata'
    }
    SHORT_LABEL = URIRef(_BASE+'shortLabel')


class Org(object):

    _BASE = 'http://www.w3.org/ns/org#'
    HAS_PRIMARY_SITE = URIRef(_BASE+"hasPrimarySite")
    HAS_SITE = URIRef(_BASE+"hasSite")
    SUB_ORGANIZATION_OF = URIRef(_BASE+"subOrganizationOf")


class Geo(object):

    _BASE = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
    LAT = URIRef(_BASE+'lat')
    LONG = URIRef(_BASE+'long')


class Geometry(object):

    _BASE = 'http://data.ordnancesurvey.co.uk/ontology/geometry/'
    AS_WKT = URIRef(_BASE+'asWKT')
    EXTENT = URIRef(_BASE+'extent')


class Vcard(object):

    _BASE = 'http://www.w3.org/2006/vcard/ns#'
    STREET_ADDRESS = URIRef(_BASE+'street-address')
    POSTAL_CODE = URIRef(_BASE+'postal-code')
    ADR = URIRef(_BASE+'adr')


class OpenVocab(object):

    _BASE = 'http://open.vocab.org/terms/'
    SORT_LABEL = URIRef(_BASE+'sortLabel')


class Accessibility(object):

    _BASE = 'http://purl.org/net/accessibility/'
    PARKING_TYPE = URIRef(_BASE+'parkingType')
    MAIN_ENTRANCE_HAS_LEVEL_ACCESS = URIRef(_BASE+'mainEntranceHasLevelAccess')
    HAS_LEVEL_ACCESS = URIRef(_BASE+'hasLevelAccess')
    DOOR_ENTRY_TYPE = URIRef(_BASE+'doorEntryType')
    FLOORS = URIRef(_BASE+'floors')
    LIFT_TO_ALL_FLOORS = URIRef(_BASE+'liftsToAllFloors')
    HAS_HEARING_SYSTEM = URIRef(_BASE+'hasHearingSystem')
    HAS_QUIET_SPACE = URIRef(_BASE+'hasQuietSpace')
    HAS_CAFE_REFRESHMENTS = URIRef(_BASE+'hasCafeRefreshments')
    HAS_ADAPTED_FURNITURE = URIRef(_BASE+'hasAdaptedFurniture')
    HAS_COMPUTER_ACCESS = URIRef(_BASE+'hasComputerAccess')
    NUMBER_OF_ACCESSIBLE_TOILETS = URIRef(_BASE+'numberOfAccessibleToilets')
    FLOORPLAN = URIRef(_BASE+'floorplan')


class AdHocDataOx(object):

    _BASE = 'http://vocab.ox.ac.uk/ad-hoc-data-ox/'
    OPENING_HOURS_TERM_TIME = URIRef(_BASE+'openingHoursTermTime')
    OPENING_HOURS_VACATION = URIRef(_BASE+'openingHoursVacation')
    OPENING_HOURS_CLOSED = URIRef(_BASE+'openingHoursClosed')
