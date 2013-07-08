from moxie.core.service import ProviderService
from moxie.core.search import searcher
from moxie.places.solr import doc_to_poi
from moxie.transport.providers.park_and_rides import OxfordParkAndRideProvider


class TransportService(ProviderService):

    def get_rti(self, ident, rti_type):
        """TODO: We should have this perform the same redirect as when
        accessing POI detail view
        """
        # Should we improve this API to only return the doc?
        doc = searcher.get_by_ids([ident]).results[0]
        return self.get_rti_from_poi(doc_to_poi(doc), rti_type)

    def get_rti_from_poi(self, poi, rti_type):
        """Get RTI from a POI object
        :param poi: POI object
        :return tuple of services and messages
        """
        provider = self.get_provider(poi, rti_type)
        return provider(poi, rti_type)

    def get_park_and_ride(self):
        provider = OxfordParkAndRideProvider()
        return provider.get_all()
        
    def import_park_and_ride(self):
        self.get_park_and_ride()