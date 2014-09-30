import unittest

import rdflib
from rdflib import URIRef, Literal
from moxie.places.importers.oxpoints_helpers import find_location
from moxie.places.importers.rdf_namespaces import Org, OxPoints, Geo, SpatialRelations


class OxpointsHelpersImporterTestCase(unittest.TestCase):

    def setUp(self):
        self.graph = rdflib.Graph()
        sublibrary = URIRef('http://oxpoints/sublibrary1')
        library = URIRef('http://oxpoints/library1')
        building = URIRef('http://oxpoints/building1')
        building2 = URIRef('http://oxpoints/building2')
        room = URIRef('http://oxpoints/room1')
        university = URIRef('http://oxpoints/university')

        self.graph.add([sublibrary, Org.subOrganizationOf, library])
        self.graph.add([library, OxPoints.primaryPlace, building])
        self.graph.add([library, Org.subOrganizationOf, university])
        self.graph.add([building, Geo.lat, Literal(51)])
        self.graph.add([building, Geo.long, Literal(12)])
        self.graph.add([building2, Geo.lat, Literal(52)])
        self.graph.add([building2, Geo.long, Literal(13)])
        self.graph.add([room, SpatialRelations.within, building2])

    def test_suborg(self):
        result = find_location(self.graph, URIRef('http://oxpoints/sublibrary1'))
        self.assertIsNotNone(result)
        lat, lon = result
        self.assertEqual(lat, 51)
        self.assertEqual(lon, 12)

    def test_room(self):
        result = find_location(self.graph, URIRef('http://oxpoints/room1'))
        self.assertIsNotNone(result)
        lat, lon = result
        self.assertEqual(lat, 52)
        self.assertEqual(lon, 13)
