import logging
import bz2
import zipfile
import os

import requests
from xml.sax import make_parser

from moxie import create_app
from moxie.worker import celery
from moxie.core.tasks import get_resource
from moxie.core.search import searcher
from moxie.places.importers.osm import OSMHandler
from moxie.places.importers.oxpoints import OxpointsImporter
from moxie.places.importers.naptan import NaPTANImporter
from moxie.places.importers.ox_library_data import OxLibraryDataImporter

logger = logging.getLogger(__name__)
BLUEPRINT_NAME = 'places'


@celery.task
def import_all(force_update_all=False):
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        import_osm.delay(force_update=force_update_all)
        import_oxpoints.delay(force_update=force_update_all)
        import_naptan.delay(force_update=force_update_all)
        import_ox_library_data.delay(force_update=force_update_all)


@celery.task
def import_osm(url=None, force_update=False):
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        url = url or app.config['OSM_IMPORT_URL']
        osm = get_resource(url, force_update)
        if osm:
            logger.info("OSM Downloaded - Stored here: %s" % osm)
            osm = open(osm)
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
        else:
            logger.info("OSM hasn't been imported - resource not loaded")


@celery.task
def import_oxpoints(url=None, force_update=False):
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        url = url or app.config['OXPOINTS_IMPORT_URL']
        static_files_dir = app.config.get('STATIC_FILES_IMPORT_DIRECTORY', None)
        oxpoints = get_resource(url, force_update)

        if 'OXPOINTS_SHAPES_URL' in app.config:
            url_shapes = app.config['OXPOINTS_SHAPES_URL']
            oxpoints_shape = get_resource(url_shapes, force_update, media_type='application/rdf+xml')
        else:
            oxpoints_shape = None

        if oxpoints:
            logger.info("OxPoints Downloaded - Stored here: %s" % oxpoints)
            oxpoints = open(oxpoints)
            if oxpoints_shape:
                shapes = open(oxpoints_shape)
            else:
                shapes = None
            importer = OxpointsImporter(searcher, 10, oxpoints, shapes, static_files_dir)
            importer.import_data()
        else:
            logger.info("OxPoints hasn't been imported - resource not loaded")


@celery.task
def import_naptan(url=None, force_update=False):
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        url = url or app.config['NAPTAN_IMPORT_URL']
        naptan = get_resource(url, force_update)
        if naptan:
            archive = zipfile.ZipFile(open(naptan))
            f = archive.open('NaPTAN.xml')
            naptan = NaPTANImporter(searcher, 10, f, ['340'], 'identifiers')
            naptan.run()
        else:
            logger.info("Naptan hasn't been imported - resource not loaded")


@celery.task
def import_ox_library_data(url=None, force_update=False):
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        url = url or app.config['LIBRARY_DATA_IMPORT_URL']
        library_data = get_resource(url, force_update)
        if library_data:
            file = open(library_data)
            importer = OxLibraryDataImporter(searcher, 10, file)
            importer.run()
        else:
            logger.info("OxLibraryData hasn't been imported - resource not loaded")


@celery.task
def download_file(url, location):
    """Download a file and store it at location
    :param url: URL to download the file from
    :param location: location where to put the file
    """
    logger.info('Downloading {url} to {location}'.format(url=url,
                                                         location=location))
    response = requests.get(url)
    directory_path = '/'.join(location.split('/')[:-1])
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    f = file(location, 'w')
    f.write(response.content)
    f.close()
