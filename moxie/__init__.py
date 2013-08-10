import logging

from os import path

try:
    from raven.contrib.flask import Sentry
    from raven.handlers.logging import SentryHandler
    from raven.conf import setup_logging
    raven_available = True
except ImportError:
    raven_available = False

from moxie.core.configurator import Configurator
from moxie.core.cache import cache
from moxie.core.metrics import statsd
from moxie.core.app import Moxie
from moxie.core.healthchecks import check_services
from moxie.core.browser import RootView


def create_app(use_default_settings=True):
    app = Moxie(__name__)
    configurator = Configurator(app)
    if use_default_settings:
        cfg_path = path.join(app.root_path, 'default_settings.yaml')
        configurator.from_yaml(cfg_path)
    configurator.from_envvar('MOXIE_SETTINGS', silent=True)

    # logging configuration for Raven/Sentry
    if raven_available and 'SENTRY_DSN' in app.config:
        sentry = Sentry(dsn=app.config['SENTRY_DSN'])
        # capture uncaught exceptions within Flask
        sentry.init_app(app)
        handler = SentryHandler(app.config['SENTRY_DSN'],
                                level=logging.getLevelName(
                                    app.config.get('SENTRY_LEVEL', 'WARNING')))
        setup_logging(handler)

    statsd.init_app(app)
    cache.init_app(app)

    # Static URL Route for API Health checks
    app.add_url_rule('/_health', view_func=check_services)
    app.add_url_rule('/', view_func=RootView.as_view('root'))
    return app
