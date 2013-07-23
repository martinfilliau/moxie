from flask.ext.statsd import StatsD


# A no-op stub of the statsd interface from https://github.com/ox-it/humfrey/blob/master/humfrey/utils/statsd.py
class _noop_timer(object):
    def __call__(self, f):
        return f
    def __enter__(self):
        pass
    def __exit__(self, typ, value, tb):
        pass

class _noop_statsd(object):
    def decr(self, stat, count=1, rate=1): pass
    def incr(self, stat, count=1, rate=1): pass
    def gauge(self, stat, count=1, rate=1): pass
    def timing(self, stat, delta, rate=1): pass

    def timer(self, stat, rate=1):
        return _noop_timer()


class MoxieStatsD(StatsD):
    def __init__(self, app=None, config=None):
        self.config = None
        if app is not None:
            # Set self.statsd
            self.init_app(app)
        else:
            # Without correctly initialising the statsd stuff shouldn't
            # cause problems and instead just noop
            self.app = None
            self.init_noop_statsd()

    def init_noop_statsd(self):
        self.statsd = _noop_statsd()

    def init_app(self, app, config=None):
        if config is not None:
            self.config = config
        elif self.config is None:
            self.config = app.config

        # Only init statsd if it's explicitly configured
        if 'STATSD_HOST' in self.config:
            super(MoxieStatsD, self).init_app(app, config=self.config)

statsd = MoxieStatsD()
