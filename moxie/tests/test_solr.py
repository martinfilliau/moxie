import unittest


class SolrTest(unittest.TestCase):

    def test_solr_escape(self):
        # moving import here as it was causing errors with statsd
        from moxie.core.search.solr import SolrSearch
        self.assertEqual(SolrSearch.solr_escape("osm:1234"), "osm\:1234")