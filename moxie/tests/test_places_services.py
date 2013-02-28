import unittest, mock

from moxie.places.services import POIService


class POIServiceTestCase(unittest.TestCase):

    def test_get_results_by_id(self):
        with mock.patch('moxie.places.services.searcher') as mock_searcher:
            with mock.patch('moxie.places.services.doc_to_poi') as mock_doc_to_poi:
                poi_service = POIService()
                mock_doc_to_poi.return_value = None
                results = poi_service.get_places_by_identifiers(['123'])

                mock_searcher.get_by_ids.assert_called_with(['123'])
