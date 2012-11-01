# Moxie general config
DEBUG = True
SECRET_KEY = 'put-your-secret-key-here-dummy'
DEFAULT_ALLOW_ORIGINS = ['http://localhost']

# Places app
DEFAULT_LOCATION = (51.7531, -1.2584)
OSM_IMPORT_URL = 'http://download.geofabrik.de/openstreetmap/europe/great_britain/england/oxfordshire.osm.bz2'
OXPOINTS_IMPORT_URL = 'http://oxpoints.oucs.ox.ac.uk/all.json'
NAPTAN_IMPORT_URL = 'http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANxml.zip'

from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider
bus_provider = CloudAmberBusRtiProvider('http://www.oxontime.com')

from moxie.library.providers.oxford_z3950 import Z3950
z = Z3950('library.ox.ac.uk', 'ALEPH', results_encoding='unicode')

SERVICES = {
'places': {
    'POIService': ([], {}),
    'TransportService': ([], {'providers': [bus_provider]}),
    'SearchService': (['solr+http://localhost:8080/solr/places'], {}),
    'KVService': (['redis://localhost:6379/0'], {}),
    },
'library': {
    'POIService': ([], {}),
    'LibrarySearchService': ([], {'providers': [z]}),
    'KVService': (['redis://localhost:6379/0'], {}),
    'SearchService': (['solr+http://localhost:8983/solr/collection1'], {}),
    },
'oxford_dates': {
    'OxfordDatesService': ([], {}),
    }
}
