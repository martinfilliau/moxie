from moxie.core.service import Service
from moxie.core.search import searcher


class TransportService(Service):

    def get_rti(self, ident):
        """TODO: We should have this perform the same redirect as when accessing POI
        detailed info.
        """
        # Should we improve this API to only return the doc?
        results = searcher.get_by_ids([ident])
        # First do a GET request by its ID
        if results.json['response']['docs']:
            doc = results.json['response']['docs'][0]
        return self.invoke_provider(doc)
