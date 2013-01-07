import os
import yaml
import importlib


class Configurator(object):
    """Provides basic configuration within Moxie.  Currently we handle
    our configuration through `YAML <http://yaml.org>`_ files.
    """

    def __init__(self, app):
        self.app = app

    def update_flask_config(self, conf):
        self.app.config.update(conf)

    def register_blueprints(self, blueprints):
        """Expects a dictionary of blueprints, something like this::

            {'courses': {
                'url_prefix': '/courses',
                'factory': 'moxie_courses.create_blueprint'},
            }

        The *factory* represents a function which given a name will
        return a `Flask.blueprint`. This method will import the factory
        and call it with the blueprint key.
        """
        for name, conf in blueprints.items():
            module, _, func = conf.pop('factory').rpartition('.')
            module = importlib.import_module(module)
            factory = getattr(module, func)
            bp = factory(name)
            self.app.register_blueprint(bp, **conf)

    def register_services(self, services):
        registered_services = self.app.config.get('SERVICES', {})
        registered_services.update(services)
        self.app.config['SERVICES'] = registered_services
        
    def register_healthchecks(self, healthchecks):
        registered_healthchecks = self.app.config.get('HEALTHCHECKS', {})
        registered_healthchecks.update(healthchecks)
        self.app.config['HEALTHCHECKS'] = registered_healthchecks

    def from_yaml(self, yaml_path, silent=False):
        """Read in the file and parse (safely) as YAML.
        Update the Flask conf, blueprints, services.
        """
        try:
            conf = yaml.safe_load(open(yaml_path))
        except IOError as e:
            if silent:
                return False
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        self.update_flask_config(conf.get('flask', {}))
        self.register_blueprints(conf.get('blueprints', {}))
        self.register_services(conf.get('services', {}))
        self.register_healthchecks(conf.get('healthchecks', {}))

    def from_envvar(self, envvar, silent=False):
        """Lifted from `Flask.config`"""
        rv = os.environ.get(envvar)
        if not rv:
            if silent:
                return False
            raise RuntimeError('The environment variable %r is not set '
                               'and as such configuration could not be '
                               'loaded.  Set this variable and make it '
                               'point to a configuration file' %
                               envvar)
        return self.from_yaml(rv, silent=silent)
