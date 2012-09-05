from moxie import default_celeryconfig
from celery import Celery

celery = Celery(__name__)

# Default configuration shipped with moxie
celery.config_from_object(default_celeryconfig)

# Import user config using a env variable. Fails silently to use only defaults.
celery.config_from_envvar('MOXIE_CELERYCONFIG', silent=True)

if __name__ == '__main__':
    celery.start()
