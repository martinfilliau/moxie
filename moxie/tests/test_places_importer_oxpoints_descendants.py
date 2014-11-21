import unittest
import mock

from rdflib import URIRef
from moxie.places.importers.oxpoints_descendants import OxpointsDescendantsImporter
from moxie.places.importers.rdf_namespaces import Org


class OxpointsDescendantsImporterTestCase(unittest.TestCase):

    def setUp(self):
        self.sample_oxpoints = 'moxie/tests/data/sample-oxpoints.rdf'
        self.mock_kv = mock.Mock()
        self.importer = OxpointsDescendantsImporter(self.mock_kv, self.sample_oxpoints,
                                                    Org.subOrganizationOf,
                                                    rdf_media_type='xml')

    def test_importer_runs(self):
        self.importer.import_data()

    def test_importer_writes_kv(self):
        self.importer.import_data()
        self.assertTrue(self.mock_kv.set.called)
        # Sample data has 3 items
        self.assertEqual(self.mock_kv.set.call_count, 3)

    def test_university_descendants(self):
        self.importer.import_data()
        self.mock_kv.set.assert_called_with('oxpoints:00000000', '{"descendants": [{"id": "oxpoints:23232639", "title": "Mathematical, Physical and Life Sciences"}, {"id": "oxpoints:23232673", "title": "Department of Physics"}]}')

    def test_mpls_descendants(self):
        self.importer.import_data()
        self.mock_kv.set.assert_any_call('oxpoints:23232639', '{"descendants": [{"id": "oxpoints:23232673", "title": "Department of Physics"}]}')

    def test_import_only_mpls(self):
        mpls = URIRef("http://oxpoints.oucs.ox.ac.uk/id/23232639")
        desc = self.importer.import_subject(mpls)
        self.assertEqual(desc, [{'id': 'oxpoints:23232673', 'title': u'Department of Physics'}])
        self.mock_kv.set.assert_any_call('oxpoints:23232639', '{"descendants": [{"id": "oxpoints:23232673", "title": "Department of Physics"}]}')
