from flask import _app_ctx_stack, request


class NoProviderFound(Exception):
    pass


class Service(object):

    def __init__(self, providers=None):
        self.providers = providers or []

    @classmethod
    def from_context(cls, name='', blueprint_name=''):
        ctx = _app_ctx_stack.top
        name = name or cls.__name__
        if not blueprint_name and request:
            blueprint_name = request.blueprint
        service_key = '.'.join((blueprint_name, name))
        if not hasattr(ctx, 'moxie_services'):
            ctx.moxie_services = dict()
        if service_key in ctx.moxie_services:
            return ctx.moxie_services[service_key]
        else:
            args, kwargs = ctx.app.config['SERVICES'][blueprint_name][name]
            service = cls(*args, **kwargs)
            ctx.moxie_services[service_key] = service
            return service

    def provider_exists(self, doc):
        for provider in self.providers:
            if provider.handles(doc):
                return True
        return False

    def invoke_provider(self, doc):
        for provider in self.providers:
            if provider.handles(doc):
                return provider.invoke(doc)
        raise NoProviderFound()
