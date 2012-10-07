class NoProviderFound(Exception):
    pass

class Service(object):
    def __init__(self, providers):
        self.providers = providers

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
