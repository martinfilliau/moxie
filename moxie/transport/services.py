from moxie.core.service import ProviderService
from moxie.core.search import searcher


class TransportService(ProviderService):

    def get_rti(self, ident):
        """TODO: We should have this perform the same redirect as when
        accessing POI detail view
        """
        # Should we improve this API to only return the doc?
        doc = searcher.get_by_ids([ident]).results[0]
        # First do a GET request by its ID
        provider = self.get_provider(doc)
        return provider(doc)
