import requests
import logging
import urlparse
import bz2
import zipfile

from tempfile import NamedTemporaryFile
from xml.sax import make_parser

from moxie import create_app
from moxie.core.kv import kv_store
from moxie.core.search import searcher
from moxie.worker import celery
from moxie.places.importers.osm import OSMHandler
from moxie.places.importers.oxpoints import OxpointsImporter
from moxie.places.importers.naptan import NaPTANImporter

app = create_app()
logger = logging.getLogger(__name__)
ETAG_KEY_FORMAT = "%s_etag_%s"
LOCATION_KEY_FORMAT = "%s_location_%s"


def write_resource(response):
    hostname = urlparse.urlparse(response.url).hostname
    f = NamedTemporaryFile(prefix=app.import_name, suffix=hostname,
            delete=False)
    f.write(response.content)
    location = f.name
    f.close()
    return location


def get_cached_etag_location(url):
    resource_etag_key = ETAG_KEY_FORMAT % (__name__, url)
    resource_location_key = LOCATION_KEY_FORMAT % (__name__, url)
    with app.app_context():
        etag = kv_store.get(resource_etag_key)
        location = kv_store.get(resource_location_key)
        if location:
            # Check to see if the cached file still exists
            try:
                f = open(location)
                f.close()
            except IOError:
                etag, location = None, None
    return etag, location


def cache_etag_location(url, etag, location):
    resource_etag_key = ETAG_KEY_FORMAT % (__name__, url)
    resource_location_key = LOCATION_KEY_FORMAT % (__name__, url)
    success = False
    with app.app_context():
        if etag and location:
            kv_store.set(resource_etag_key, etag)
            kv_store.set(resource_location_key, location)
            success = True
    return success


def get_resource(url, force_update=False):
    etag, location = get_cached_etag_location(url)
    headers = {}
    if etag and not force_update:
        headers['if-none-match'] = etag
    response = requests.get(url, headers=headers)
    etag = response.headers.get('etag', None)
    if response.status_code == 304:
        # Unchanged
        logger.info("ETag's match. No change resource - %s" % url)
        return location
    if response.ok:
        logger.info("Downloaded - %s - Content-length: %s" % (
            response.url, len(response.content)))
        location = write_resource(response)
        if cache_etag_location(url, etag, location):
            logger.info("Successfully cached etag: %s for url: %s" % (etag, url))
        return location
    else:
        logger.warning("Failed to download: %s Response: %s-%s" % (
            url, response.status_code, response.reason))
        return False


@celery.task
def clear_index():
    with app.app_context():
        r = searcher.clear_index()
        logger.info(r)


@celery.task
def import_all(force_update_all=False):
    with app.app_context():
        if force_update_all:
            clear_index()
        import_osm.delay(app.config['OSM_IMPORT_URL'],
                force_update=force_update_all)
        import_oxpoints.delay(app.config['OXPOINTS_IMPORT_URL'],
                force_update=force_update_all)
        import_naptan.delay(app.config['NAPTAN_IMPORT_URL'],
                force_update=force_update_all)


@celery.task
def import_osm(url, precedence, id_prefix=None, force_update=False):
    osm = get_resource(url, force_update)
    logger.info("OSM Downloaded - Stored here: %s" % osm)
    osm = open(osm)
    with app.app_context():
        id_prefix = id_prefix or app.config['DEFAULT_IDENTIFIER_PREFIX']
        handler = OSMHandler(searcher, precedence, id_prefix)
        parser = make_parser(['xml.sax.xmlreader.IncrementalParser'])
        parser.setContentHandler(handler)
        # Parse in 8k chunks
        buffer = osm.read(8192)
        bunzip = bz2.BZ2Decompressor()
        while buffer:
            parser.feed(bunzip.decompress(buffer))
            buffer = osm.read(8192)
        parser.close()


@celery.task
def import_oxpoints(url, precedence, id_prefix=None, force_update=False):
    oxpoints = get_resource(url, force_update)
    logger.info("OxPoints Downloaded - Stored here: %s" % oxpoints)
    oxpoints = open(oxpoints)
    with app.app_context():
        id_prefix = id_prefix or app.config['DEFAULT_IDENTIFIER_PREFIX']
        importer = OxpointsImporter(searcher, precedence, oxpoints, id_prefix)
        importer.import_data()


@celery.task
def import_naptan(url, location_codes, precedence,
        id_prefix=None, force_update=False):
    naptan = get_resource(url, force_update)
    archive = zipfile.ZipFile(open(naptan))
    f = archive.open('NaPTAN.xml')
    with app.app_context():
        id_prefix = id_prefix or app.config['DEFAULT_IDENTIFIER_PREFIX']
        naptan_importer = NaPTANImporter(searcher, precedence, f, location_codes, id_prefix)
        naptan_importer.run()
