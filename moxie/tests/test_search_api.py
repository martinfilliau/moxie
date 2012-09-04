import unittest
import mock

from moxie.core.search import _find_searcher, SEARCH_SCHEMES


MockSearcher = mock.Mock()


class SearchAPITestCase(unittest.TestCase):

    def setUp(self):
        SEARCH_SCHEMES['foobar'] = ('moxie.tests.test_search_api', 'MockSearcher')

    def test_find_searcher(self):
        searcher = _find_searcher('foobar+http://localhost:1234/foo/bar/baz')
        MockSearcher.assert_called_with('baz', 'http://localhost:1234/foo/bar/')
        self.assertEqual(MockSearcher(), searcher)

    def test_find_missing_searcher(self):
        with self.assertRaises(KeyError):
            _find_searcher('fooboo+http://localhost:1234/foo/bar/baz')
