# Moxie general config
DEBUG = True

# Moxie data API config
SEARCHER_URL = 'solr+http://localhost:8983/solr/collection1'
KV_STORE_URL = 'redis://localhost:6379/0'

# Places app
DEFAULT_LOCATION = (51.7531, -1.2584)
OSM_IMPORT_URL = 'http://download.geofabrik.de/openstreetmap/europe/great_britain/england/oxfordshire.osm.bz2'
OXPOINTS_IMPORT_URL = 'http://oxpoints.oucs.ox.ac.uk/all.json'
NAPTAN_IMPORT_URL = 'http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANxml.zip'

from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider
SERVICES = {
'places': {
    'POIService': ([], {}),
    'TransportService': ([], {'providers': [CloudAmberBusRtiProvider('http://www.oxontime.com')]}),
    },
}
