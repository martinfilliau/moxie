import unittest, mock

from moxie.places.services import POIService


class POIServiceTestCase(unittest.TestCase):

    def test_get_results_by_id(self):
        with mock.patch('moxie.places.services.searcher') as mock_searcher:
            with mock.patch('moxie.places.services.doc_to_poi') as mock_doc_to_poi:
                poi_service = POIService()
                mock_doc_to_poi.return_value = None
                poi_service.get_place_by_identifier('123')
                mock_searcher.get_by_ids.assert_called_with(['123'])

    def test_get_results_by_multiple_ids(self):
        with mock.patch('moxie.places.services.searcher') as mock_searcher:
            with mock.patch('moxie.places.services.doc_to_poi') as mock_doc_to_poi:
                poi_service = POIService()
                mock_doc_to_poi.return_value = None
                poi_service.get_places_by_identifiers(['123', '456'])
                mock_searcher.get_by_ids.assert_called_with(['123', '456'])

    def test_transform_args_internal(self):
        POIService.key_transforms = [('foo', 'bar')]
        poi_service = POIService()
        before = ['foobar']
        after = poi_service._args_to_internal(before)
        self.assertEqual(after, ['barbar'])

    def test_transform_args_friendly(self):
        POIService.key_transforms = [('foo', 'bar')]
        poi_service = POIService()
        before = ['barbar']
        after = poi_service._args_to_friendly(before)
        self.assertEqual(after, ['foobar'])

    def test_transform_args_reversibile(self):
        POIService.key_transforms = [('foo', 'bar')]
        poi_service = POIService()
        args = ['foobar', 'foofoo']
        self.assertEqual(args, poi_service._args_to_friendly(poi_service._args_to_internal(args)))
