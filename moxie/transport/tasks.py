from celery.utils.log import get_task_logger

from moxie import create_app
from moxie.worker import celery

from moxie.transport.services import TransportService

logger = get_task_logger(__name__)

BLUEPRINT_NAME = 'transport'


@celery.task
def import_park_and_ride():
    """Imports data from park and rides, it is recommended to run it quite often
    """
    app = create_app()
    with app.blueprint_context(BLUEPRINT_NAME):
        service = TransportService.from_context()
        service.import_park_and_ride()