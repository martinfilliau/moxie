import yaml
import os

from moxie import default_celeryconfig
from celery import Celery

# Set the log level of requests
import logging
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)


class MoxieCelery(Celery):

    def config_from_yaml_envvar(self, envvar, silent=False):
        """Reads a config in from `envvar` and parses as YAML and applies
        this as the configuration.
        """
        yaml_path = os.environ.get(envvar)
        if not yaml_path:
            if silent:
                return False
            raise RuntimeError('The environment variable %r is not set '
                               'and as such configuration could not be '
                               'loaded.  Set this variable and make it '
                               'point to a configuration file' %
                               envvar)
        try:
            conf = yaml.safe_load(open(yaml_path))
        except IOError as e:
            if silent:
                return False
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        self.config_from_object(conf)

celery = MoxieCelery(__name__)
# Default configuration shipped with moxie
celery.config_from_object(default_celeryconfig)
# Import user config using a env variable. Fails silently to use only defaults.
celery.config_from_yaml_envvar('MOXIE_CELERYCONFIG', silent=True)

if __name__ == '__main__':
    celery.start()
