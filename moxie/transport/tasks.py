from celery.utils.log import get_task_logger

from moxie import create_app
from moxie.worker import celery

from moxie.transport.services import TransportService

logger = get_task_logger(__name__)

BLUEPRINT_NAME = 'places'


@celery.task
def import_park_and_ride():
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        service = TransportService.from_context()
        service.import_park_and_ride()