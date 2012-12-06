from moxie.core.service import ProviderService
from moxie.core.search import searcher
from moxie.places.solr import doc_to_poi


class TransportService(ProviderService):

    def get_rti(self, ident):
        """TODO: We should have this perform the same redirect as when
        accessing POI detail view
        """
        # Should we improve this API to only return the doc?
        doc = searcher.get_by_ids([ident]).results[0]
        return self.get_rti_from_poi(doc_to_poi(doc))
        # First do a GET request by its ID

    def get_rti_from_poi(self, poi):
        """Get RTI from a POI object
        :param poi: POI object
        :return RTI
        """
        provider = self.get_provider(poi)
        return provider(poi)