from rdflib.term import URIRef


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


class Vcard(object):

    _BASE = 'http://www.w3.org/2006/vcard/ns#'
    STREET_ADDRESS = URIRef(_BASE+'street-address')
    POSTAL_CODE = URIRef(_BASE+'postal-code')
    ADR = URIRef(_BASE+'adr')
