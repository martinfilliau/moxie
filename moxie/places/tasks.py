import requests
import logging
import urlparse
import bz2

from tempfile import NamedTemporaryFile
from xml.sax import make_parser

from moxie import create_app
from moxie.core.kv import kv_store
from moxie.core.search import searcher
from moxie.worker import celery
from moxie.places.importers.osm import OSMHandler

app = create_app()
logger = logging.getLogger(__name__)


def resource_unchanged(url, etag):
    h = requests.head(url)
    if etag and 'etag' in h.headers:
        if etag == h.headers['etag']:
            return True
    return False


def write_resource(response):
    hostname = urlparse.urlparse(response.url).hostname
    f = NamedTemporaryFile(prefix=app.import_name, suffix=hostname,
            delete=False)
    f.write(response.content)
    location = f.name
    f.close()
    return location


def get_resource(url, force_update=False):
    resource_etag_key = "%s_etag_%s" % (__name__, url)
    resource_location_key = "%s_location_%s" % (__name__, url)
    with app.app_context():
        etag = kv_store.get(resource_etag_key)
        location = kv_store.get(resource_location_key)
    if resource_unchanged(url, etag) and not force_update:
        try:
            f = open(location)
            f.close()
            logger.info("ETag's match. No change resource - %s" % url)
            return location  # No change
        except IOError:
            pass
    response = requests.get(url)
    etag = response.headers.get('etag')
    if response.ok:
        logger.info("Downloaded - %s - Content-length: %s" % (
            url, len(response.content)))
        location = write_resource(response)
        with app.app_context():
            if etag:
                kv_store.set(resource_etag_key, etag)
            if location:
                kv_store.set(resource_location_key, location)
        return location
    else:
        logger.warning("Failed to download: %s Response: %s-%s" % (
            url, response.status_code, response.reason))
        return None


@celery.task
def import_osm(url, force_update=False):
    osm = get_resource(url, force_update)
    logger.info("OSM Downloaded - Stored here: %s" % osm)
    osm = open(osm)
    with app.app_context():
        handler = OSMHandler(searcher, 5)
        parser = make_parser(['xml.sax.xmlreader.IncrementalParser'])
        parser.setContentHandler(handler)
        # Parse in 8k chunks
        buffer = osm.read(8192)
        bunzip = bz2.BZ2Decompressor()
        while buffer:
            parser.feed(bunzip.decompress(buffer))
            buffer = osm.read(8192)
        parser.close()
