import urlparse
import logging
import requests
import os

from moxie.worker import celery
from moxie.core.kv import kv_store
from tempfile import NamedTemporaryFile
from requests.exceptions import RequestException

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


def get_resource(url, force_update=False, media_type=None):
    etag, location = get_cached_etag_location(url)
    headers = {}
    if etag and not force_update:
        headers['if-none-match'] = etag
    if media_type:
        headers['Accept'] = media_type
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
def download_file(url, location):
    """Download a file and store it at location
    :param url: URL to download the file from
    :param location: location where to put the file
    """
    logger.info('Downloading {url} to {location}'.format(url=url,
                                                         location=location))
    try:
        response = requests.get(url)
    except RequestException as re:
        # default behaviour is retry 3 times, every 3 minutes
        #raise self.retry(exc=re)
        raise download_file.retry(exc=re)
    else:
        directory_path = '/'.join(location.split('/')[:-1])
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        f = file(location, 'w+')
        f.write(response.content)
        f.close()
