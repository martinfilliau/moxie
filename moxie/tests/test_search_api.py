import unittest
import mock

from moxie.core.search import SEARCH_SCHEMES, SearchService


MockSearcher = mock.Mock()


class SearchAPITestCase(unittest.TestCase):

    def setUp(self):
        SEARCH_SCHEMES['foobar'] = ('moxie.tests.test_search_api', 'MockSearcher')

    def test_find_searcher(self):
        searcher = SearchService._get_backend('foobar+http://localhost:1234/foo/bar/baz')
        MockSearcher.assert_called_with('baz', 'http://localhost:1234/foo/bar/')
        self.assertEqual(MockSearcher(), searcher)

    def test_find_missing_searcher(self):
        with self.assertRaises(KeyError):
            SearchService._get_backend('fooboo+http://localhost:1234/foo/bar/baz')

    def test_create_service(self):
        ss = SearchService('foobar+http://localhost:1234/foo/bar/baz')
        self.assertEqual(MockSearcher(), ss._backend)
