from moxie.core.exceptions import NotFound
from moxie.core.service import ProviderService
from moxie.places.services import POIService
from moxie.transport.providers.park_and_rides import OxfordParkAndRideProvider


class TransportService(ProviderService):

    def get_rti(self, ident, rti_type):
        """TODO: We should have this perform the same redirect as when
        accessing POI detail view
        """
        # Should we improve this API to only return the doc?
        poi_service = POIService.from_context()
        poi = poi_service.get_place_by_identifier(ident)
        if poi:
            return self.get_rti_from_poi(poi, rti_type)
        else:
            raise NotFound

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
        provider = OxfordParkAndRideProvider()
        provider.import_data()