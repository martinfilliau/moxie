import logging
import bz2
import zipfile
import requests

from celery import chain
from xml.sax import make_parser

from moxie import create_app
from moxie.worker import celery
from moxie.core.tasks import get_resource
from moxie.core.search import searcher
from moxie.core.kv import kv_store
from moxie.places.importers.osm import OSMHandler
from moxie.places.importers.oxpoints import OxpointsImporter
from moxie.places.importers.oxpoints_descendants import OxpointsDescendantsImporter
from moxie.places.importers.naptan import NaPTANImporter
from moxie.places.importers.ox_library_data import OxLibraryDataImporter
from moxie.places.importers.rdf_namespaces import Org

logger = logging.getLogger(__name__)
BLUEPRINT_NAME = 'places'


@celery.task
def import_all(force_update_all=False):
    """Start all the importers sequentially and attempt
    to move the result index to production
    """
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        solr_server = app.config['PLACES_SOLR_SERVER']
        staging_core = app.config['PLACES_SOLR_CORE_STAGING']
        staging_core_url = '{server}/{core}/update'.format(server=solr_server, core=staging_core)

        # make sure the "staging" index is empty
        delete_response = requests.post(staging_core_url, '<delete><query>*:*</query></delete>', headers={'Content-type': 'text/xml'})
        commit_response = requests.post(staging_core_url, '<commit/>', headers={'Content-type': 'text/xml'})

        if delete_response.ok and commit_response.ok:
            logger.info("Deleted all documents from staging, launching importers")
            # Using a chain (seq) so tasks execute in order
            chain(import_oxpoints.s(force_update=force_update_all),
                  import_osm.s(force_update=force_update_all),
                  import_naptan.s(force_update=force_update_all),
                  import_ox_library_data.s(force_update=force_update_all),
                  swap_places_cores.s())()
            return True
        else:
            logger.warning("Staging core not deleted correctly, aborting", extra={
                'delete_response': delete_response.status_code,
                'commit_response': commit_response.status_code
            })
        return False


@celery.task
def swap_places_cores(previous_result=None):
    """Swap staging and production indices if the
    result of the previous task is True (i.e. success)
    """
    if previous_result in (None, True):
        app = create_app()
        with app.blueprint_context(BLUEPRINT_NAME):
            solr_server = app.config['PLACES_SOLR_SERVER']
            staging_core = app.config['PLACES_SOLR_CORE_STAGING']
            production_core = app.config['PLACES_SOLR_CORE_PRODUCTION']

            swap_response = requests.get("{server}/admin/cores?action=SWAP&core={new}&other={old}".format(server=solr_server,
                                                                                                          new=production_core,
                                                                                                          old=staging_core))
            if swap_response.ok:
                logger.info("Cores swapped")
                return True
            else:
                logger.warning("Error when swapping core {response}".format(response=swap_response.status_code))
    else:
        logger.warning("Didn't swap cores because some errors previously happened")
    return False


@celery.task
def import_osm(previous_result=None, url=None, force_update=False):
    """Run the OSM importer if previous importer has succeeded
    """
    if previous_result in (None, True):
        try:
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
                    return True
                else:
                    logger.info("OSM hasn't been imported - resource not loaded")
        except:
            logger.error("Error running OSM importer", exc_info=True)
    return False


@celery.task
def import_oxpoints_organisation_descendants(previous_result=None, url=None, force_update=False):
    """Run the OxPoints organisation descendants importer
    """
    if previous_result in (None, True):
        try:
            app = create_app()
            RDF_MEDIA_TYPE = 'text/turtle'  # default RDF serialization
            with app.blueprint_context(BLUEPRINT_NAME):
                url = url or app.config['OXPOINTS_IMPORT_URL']
                oxpoints = get_resource(url, force_update, media_type=RDF_MEDIA_TYPE)
                if oxpoints:
                    logger.info("OxPoints Downloaded - Stored here: %s" % oxpoints)
                    oxpoints = open(oxpoints)
                    importer = OxpointsDescendantsImporter(kv_store, oxpoints, Org.subOrganizationOf,
                                                           rdf_media_type=RDF_MEDIA_TYPE)
                    importer.import_data()
                    return True
                else:
                    logger.info("OxPoints descendants hasn't been imported - resource not loaded")
        except:
            logger.error("Error running OxPoints descendants importer", exc_info=True)
    return False


@celery.task
def import_oxpoints(previous_result=None, url=None, force_update=False):
    """Run the OxPoints importer
    """
    if previous_result in (None, True):
        try:
            app = create_app()
            RDF_MEDIA_TYPE = 'text/turtle'  # default RDF serialization
            with app.blueprint_context(BLUEPRINT_NAME):
                url = url or app.config['OXPOINTS_IMPORT_URL']

                static_files_dir = app.config.get('STATIC_FILES_IMPORT_DIRECTORY', None)
                oxpoints = get_resource(url, force_update, media_type=RDF_MEDIA_TYPE)

                if 'OXPOINTS_SHAPES_URL' in app.config:
                    url_shapes = app.config['OXPOINTS_SHAPES_URL']
                    oxpoints_shape = get_resource(url_shapes, force_update, media_type=RDF_MEDIA_TYPE)
                else:
                    oxpoints_shape = None

                if 'OXPOINTS_ACCESSIBILITY_URL' in app.config:
                    url_accessibility = app.config['OXPOINTS_ACCESSIBILITY_URL']
                    oxpoints_accessibility = get_resource(url_accessibility,
                                                          force_update=force_update,
                                                          media_type=RDF_MEDIA_TYPE)
                else:
                    oxpoints_accessibility = None

                if 'OXPOINTS_COURSES_LOCATIONS_URL' in app.config:
                    url_courses = app.config['OXPOINTS_COURSES_LOCATIONS_URL']
                    oxpoints_courses = get_resource(url_courses,
                                                    force_update=force_update,
                                                    media_type=RDF_MEDIA_TYPE)
                else:
                    oxpoints_courses = None

                if oxpoints:
                    logger.info("OxPoints Downloaded - Stored here: %s" % oxpoints)
                    oxpoints = open(oxpoints)
                    if oxpoints_shape:
                        shapes = open(oxpoints_shape)
                    else:
                        shapes = None

                    if oxpoints_accessibility:
                        accessibility = open(oxpoints_accessibility)
                    else:
                        accessibility = None

                    if oxpoints_courses:
                        courses = open(oxpoints_courses)
                    else:
                        courses = None

                    importer = OxpointsImporter(searcher, 10, oxpoints, shapes, accessibility, courses, static_files_dir,
                                                rdf_media_type=RDF_MEDIA_TYPE)
                    importer.import_data()
                    return True
                else:
                    logger.info("OxPoints hasn't been imported - resource not loaded")
        except:
            logger.error("Error running OxPoints importer", exc_info=True)
    return False


@celery.task
def import_naptan(previous_result=None, url=None, force_update=False):
    if previous_result in (None, True):
        try:
            app = create_app()
            with app.blueprint_context(BLUEPRINT_NAME):
                url = url or app.config['NAPTAN_IMPORT_URL']
                naptan = get_resource(url, force_update)
                if naptan:
                    archive = zipfile.ZipFile(open(naptan))
                    f = archive.open('NaPTAN.xml')
                    naptan = NaPTANImporter(searcher, 10, f, ['340'], 'identifiers')
                    naptan.run()
                    return True
                else:
                    logger.info("Naptan hasn't been imported - resource not loaded")
        except:
            logger.error("Error running NaPTAN importer", exc_info=True)
    return False


@celery.task
def import_ox_library_data(previous_result=None, url=None, force_update=False):
    if previous_result in (None, True):
        try:
            app = create_app()
            with app.blueprint_context(BLUEPRINT_NAME):
                url = url or app.config['LIBRARY_DATA_IMPORT_URL']
                library_data = get_resource(url, force_update)
                if library_data:
                    file = open(library_data)
                    importer = OxLibraryDataImporter(searcher, 10, file)
                    importer.run()
                    return True
                else:
                    logger.info("OxLibraryData hasn't been imported - resource not loaded")
        except:
            logger.error("Error running OxLibraryData importer", exc_info=True)
    return False
