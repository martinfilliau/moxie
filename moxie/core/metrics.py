from flask.ext.statsd import StatsD
from werkzeug.local import LocalProxy
from flask import current_app


def _get_statsd():
    return StatsD(current_app)

statsd = LocalProxy(_get_statsd)
