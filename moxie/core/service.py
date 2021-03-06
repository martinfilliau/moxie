import importlib

from flask import _app_ctx_stack, request


class NoConfiguredService(Exception):
    pass


class Service(object):
    """Services are HTTP (transport layer) agnostic instead operating at
    the Application Layer. Services encapsulate all operations made on
    the data. Views should never directly access data sources without going
    through a Service.

    Configuration of services can be done for each Blueprint. Within the
    `Application context <http://flask.pocoo.org/docs/appcontext/>`_ they
    will be cached, this means the following code accesses the same
    Service object.::

        with app.app_context():
            service_one = MyService.from_context()
            service_two = MyService.from_context()
            assert(service_one is service_two)
    """

    @classmethod
    def from_context(cls, blueprint_name=''):
        """Create a :py:class:`Service` from the application and request
        context. args and kwargs for the :py:class:`Service` are read from
        the ``Flask.config``. Configuration should follow this pattern::

            SERVICES = {
                'my_blueprint': {
                    'MyService': (args, kwargs),
                    'MySecondService: ((1,2,3), {'foo': 'bar'},
                    }
                }

        :param blueprint_name: Override the blueprint name so it isn't read
                               from the request context.
        """
        ctx = _app_ctx_stack.top
        name = cls.__name__
        if not blueprint_name and request:
            blueprint_name = request.blueprint
        service_key = '.'.join((blueprint_name, name))
        if not hasattr(ctx, 'moxie_services'):
            ctx.moxie_services = dict()
        if service_key in ctx.moxie_services:
            return ctx.moxie_services[service_key]
        else:
            try:
                kwargs = ctx.app.config['SERVICES'][blueprint_name][name]
            except KeyError:
                raise NoConfiguredService('The service: %s is not configured on blueprint: %s' % (name, blueprint_name))
            service = cls(**kwargs)
            ctx.moxie_services[service_key] = service
            return service

    def _import_provider(self, config):
        """Given a provider config of the form::

            ('moxie.app.providers.ProviderClass', {'location': 'Oxford'})

        Imports the first element and instantiate using the `**kwargs` in the
        second element. Providers are used throughout Moxie, this is the
        consistent way to import them in your `Service`.
        """
        provider, conf = config
        module_name, _, klass_name = provider.rpartition('.')
        module = importlib.import_module(module_name)
        klass = getattr(module, klass_name)
        return klass(**conf)


class ProviderException(Exception):
    pass


class NoSuitableProviderFound(ProviderException):
    pass


class MultipleProvidersFound(ProviderException):
    pass


class ProviderService(Service):
    """Used where a :class:`Service` deals with many external providers.
    Example usage can be found in the
    :class:`~moxie.transport.services.TransportService`
    """
    def __init__(self, providers={}):
        self.providers = map(self._import_provider, providers.items())

    def get_provider(self, doc, *args, **kwargs):
        """Returns a :class:`~moxie.core.provider.Provider` which can handle
        your ``doc``.

        If no (single) approrpriate provider can be found for your document
        we raise a :class:`ProviderException`. Two subclasses are currently
        raised:
         - :class:`NoSuitableProviderFound` if we can't find *any* provider.
         - :class:`MultipleProvidersFound` if we find more than one provider.
        """
        suitable_providers = []
        for provider in self.providers:
            if provider.handles(doc, *args, **kwargs):
                suitable_providers.append(provider)
        if len(suitable_providers) == 1:
            return suitable_providers[0]
        elif len(suitable_providers) > 1:
            raise MultipleProvidersFound()
        elif len(suitable_providers) == 0:
            raise NoSuitableProviderFound()
