Metrics
=======

Moxie provides metrics using `Flask-StatsD <https://github.com/cyberdelia/flask-statsd>`_, a wrapper around Statsd python client.

Configuration
-------------

The following configuration variables are available (in the Flask section):

- `STATSD_HOST` hostname of the statsd instance
- `STATSD_PORT` port of statsd (8125 by default)
- `STATSD_PREFIX` prefix to set for all metrics

See `Flask-Statsd documentation <https://github.com/cyberdelia/flask-statsd>`_ for more information.

Views timing
------------

All views are automatically timed (from `moxie.core.views`), metrics are sent in the form of <module name>.<view name>
e.g. `moxie_events.views.Search`.

E.g. timing some code execution
-------------------------------

To time some code execution, you should use a context manager `statsd.timer`
(imported from `moxie.core.metrics` and specify the name of the metric.

.. code-block:: python

    from moxie.core.views import ServiceView
    from moxie.core.metrics import statsd

    class TimedView(ServiceView):

        def handle_request(self):
            self.expensive_method()
            return {'near': 'real-time'}

        def expensive_method(self):
            with statsd.timer('expensive'):
                # some code
