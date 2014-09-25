import unittest

import rdflib
from rdflib import URIRef, Literal
from moxie.places.importers.oxpoints_helpers import find_location
from moxie.places.importers.rdf_namespaces import Org, OxPoints, Geo


class OxpointsDescendantsImporterTestCase(unittest.TestCase):

    def setUp(self):
        self.graph = rdflib.Graph()
        sublibrary = URIRef('http://oxpoints/sublibrary1')
        library = URIRef('http://oxpoints/library1')
        building = URIRef('http:/oxpoints/building1')
        self.graph.add([sublibrary, Org.subOrganizationOf, library])
        self.graph.add([library, OxPoints.primaryPlace, building])
        self.graph.add([building, Geo.lat, Literal(51)])
        self.graph.add([building, Geo.long, Literal(12)])

    def test_importer_runs(self):
        result = find_location(self.graph, URIRef('http://oxpoints/sublibrary1'))
        self.assertIsNotNone(result)
        lat, lon = result
        self.assertEqual(lat, 51)
        self.assertEqual(lon, 12)
