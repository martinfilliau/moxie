from moxie.core.service import Service
from moxie.core.search import searcher


class TransportService(Service):

    def __init__(self, providers=None):
        self.providers = providers or []

    def get_provider(self, doc):
        """Returns a :class:`~moxie.core.provider.Provider` which can handle
        your ``doc``.  If no provider can be found, returns ``None``.
        """
        for provider in self.providers:
            if provider.handles(doc):
                return provider
        return None

    def get_rti(self, ident):
        """TODO: We should have this perform the same redirect as when
        accessing POI detail view
        """
        # Should we improve this API to only return the doc?
        doc = searcher.get_by_ids([ident]).results[0]
        # First do a GET request by its ID
        provider = self.get_provider(doc)
        return provider(doc)
