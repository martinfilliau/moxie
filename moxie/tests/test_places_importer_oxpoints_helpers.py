import unittest

import rdflib
from rdflib import URIRef, Literal, RDF
from moxie.places.importers.oxpoints_helpers import find_location, find_shape
from moxie.places.importers.rdf_namespaces import (Org, OxPoints, Geo,
                                                   SpatialRelations, Geometry)


class OxpointsHelpersImporterTestCase(unittest.TestCase):

    def setUp(self):
        self.graph = rdflib.Graph()
        sublibrary = URIRef('http://oxpoints/sublibrary1')
        library = URIRef('http://oxpoints/library1')
        building = URIRef('http://oxpoints/building1')
        building2 = URIRef('http://oxpoints/building2')
        room = URIRef('http://oxpoints/room1')
        university = URIRef('http://oxpoints/university')
        building_shape = URIRef('http://oxpoints/buildings1/shape')
        site = URIRef('http://oxpoints/site1')
        site_shape = URIRef('http://oxpoints/site1/shape')
        self.building_shape_value = "POLYGON ((-1.2674743 51.753493400000004 0,-1.2663551 51.753694199999998 0,-1.2662089 51.7533819 0,-1.2672244 51.753199600000002 0,-1.2672569 51.753269199999998 0,-1.2673606 51.7532506 0,-1.2674743 51.753493400000004 0))"
        self.site_shape_value = self.building_shape_value       # just for tests

        self.graph.add([sublibrary, Org.subOrganizationOf, library])
        self.graph.add([library, OxPoints.primaryPlace, building])
        self.graph.add([library, Org.subOrganizationOf, university])
        self.graph.add([building, Geo.lat, Literal(51)])
        self.graph.add([building, Geo.long, Literal(12)])
        self.graph.add([building2, RDF.type, OxPoints.Building])
        self.graph.add([building2, Geometry.extent, building_shape])
        self.graph.add([building_shape, Geometry.asWKT, Literal(self.building_shape_value)])
        self.graph.add([building2, Geo.lat, Literal(52)])
        self.graph.add([building2, Geo.long, Literal(13)])
        self.graph.add([room, SpatialRelations.within, building2])
        self.graph.add([building, SpatialRelations.within, site])
        self.graph.add([building, RDF.type, OxPoints.Building])
        self.graph.add([site, Geometry.extent, site_shape])
        self.graph.add([site, RDF.type, OxPoints.Site])
        self.graph.add([site_shape, Geometry.asWKT, Literal(self.site_shape_value)])

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

    def test_shape(self):
        result = find_shape(self.graph, URIRef('http://oxpoints/room1'))
        self.assertIsNotNone(result)
        self.assertEqual(self.building_shape_value, result)

    def test_no_shape(self):
        result = find_shape(self.graph, URIRef('http://oxpoints/sublibrary1'))
        self.assertIsNone(result)

    def test_do_not_go_to_site(self):
        result = find_shape(self.graph, URIRef('http://oxpoints/building1'))
        self.assertIsNone(result)

    def test_shape_site(self):
        result = find_shape(self.graph, URIRef('http://oxpoints/site1'))
        self.assertEqual(self.site_shape_value, result)
