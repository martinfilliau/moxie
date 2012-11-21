import urlparse
import logging
import requests

from moxie.core.search import searcher
from moxie.core.kv import kv_store
from tempfile import NamedTemporaryFile

ETAG_KEY_FORMAT = "%s_etag_%s"
LOCATION_KEY_FORMAT = "%s_location_%s"
logger = logging.getLogger(__name__)


def write_resource(response):
    hostname = urlparse.urlparse(response.url).hostname
    f = NamedTemporaryFile(suffix=hostname,
            delete=False)
    f.write(response.content)
    location = f.name
    f.close()
    return location


def get_cached_etag_location(url):
    resource_etag_key = ETAG_KEY_FORMAT % (__name__, url)
    resource_location_key = LOCATION_KEY_FORMAT % (__name__, url)
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
