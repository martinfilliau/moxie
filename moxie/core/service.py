from flask import _app_ctx_stack, request


class NoProviderFound(Exception):
    pass


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

    def __init__(self, providers=None):
        self.providers = providers or []

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
                args, kwargs = ctx.app.config['SERVICES'][blueprint_name][name]
            except KeyError:
                raise NoConfiguredService('The service: %s is not configured on blueprint: %s' % (name, blueprint_name))
            service = cls(*args, **kwargs)
            ctx.moxie_services[service_key] = service
            return service

    def provider_exists(self, doc):
        for provider in self.providers:
            if provider.handles(doc):
                return provider
        return False

    def invoke_provider(self, doc):
        for provider in self.providers:
            if provider.handles(doc):
                return provider.invoke(doc)
        raise NoProviderFound()
