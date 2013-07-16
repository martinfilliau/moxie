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

E.g. timing a function
----------------------

To use it on a view, you have to decorate your method with `@statsd.timer`
(imported from `moxie.core.metrics`) and specify the name of the metric.

.. code-block:: python

    from moxie.core.views import ServiceView
    from moxie.core.metrics import statsd

    class TimedView(ServiceView):

        @statsd.timer('timed_view')
        def handle_request(self):
            return {'near': 'real-time'}

