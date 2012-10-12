import unittest, mock

from moxie.places.services import POIService


class POIServiceTestCase(unittest.TestCase):

    def test_get_results_by_id(self):
        with mock.patch('moxie.places.services.searcher') as mock_searcher:
            poi_service = POIService()
            results = poi_service.get_place_by_identifier('123')
            mock_searcher.get_by_ids.assert_called_with(['123'])
