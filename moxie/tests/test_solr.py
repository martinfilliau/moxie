import unittest

from moxie.core.search.solr import SolrSearch

class SolrTest(unittest.TestCase):

    def test_solr_escape(self):
        self.assertEqual(SolrSearch.solr_escape("osm:1234"), "osm\:1234")