from os import path

from werkzeug.exceptions import default_exceptions
try:
    from raven.contrib.flask import Sentry
    from raven.handlers.logging import SentryHandler
    from raven.conf import setup_logging
    raven_available = True
except ImportError:
    raven_available = False

from moxie.core.configurator import Configurator
from moxie.core.cache import cache
from moxie.core.app import Moxie
from moxie.core.exceptions import exception_handler
from moxie.core.healthchecks import check_services


def create_app():
    app = Moxie(__name__)
    configurator = Configurator(app)
    cfg_path = path.join(app.root_path, 'default_settings.yaml')
    configurator.from_yaml(cfg_path)
    configurator.from_envvar('MOXIE_SETTINGS', silent=True)

    # logging configuration for Raven/Sentry
    if raven_available and 'SENTRY_DSN' in app.config:
        sentry = Sentry(dsn=app.config['SENTRY_DSN'])
        # capture uncaught exceptions within Flask
        sentry.init_app(app)
        handler = SentryHandler(app.config['SENTRY_DSN'])
        setup_logging(handler)

    # Custom exceptions handler
    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = exception_handler
    cache.init_app(app)
    # Static URL Route for API Health checks
    app.add_url_rule('/_health', view_func=check_services)
    return app
