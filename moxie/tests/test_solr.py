import unittest
import mock

from moxie.core.search.solr import SolrSearch


class SolrTest(unittest.TestCase):
    def setUp(self):
        self.test_solr = SolrSearch('test', 'foo.bar')
        mock_search = mock.Mock(return_value='Test Results')
        self.test_solr.search = mock_search

    def test_build_search_identifiers(self):
        prefix = 'id_'
        identifiers = [('osm', 123), ('oxpoints', 654)]
        self.test_solr.search_for_ids(prefix, identifiers)
        self.test_solr.search.assert_called_with({
            'q': 'id_osm:123 OR id_oxpoints:654'})

    def test_same_identifier_key(self):
        prefix = 'id_'
        identifiers = [('osm', 123), ('osm', 654)]
        self.test_solr.search_for_ids(prefix, identifiers)
        self.test_solr.search.assert_called_with({
            'q': 'id_osm:123 OR id_osm:654'})
