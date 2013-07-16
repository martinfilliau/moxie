import unittest

from moxie.transport.providers.park_and_rides import OxfordParkAndRideProvider


class OxfordParkAndRideProviderTestCase(unittest.TestCase):

    def setUp(self):
        self.html_test_file = 'moxie/tests/data/voyager_oxfordshire_carpark.html'


    def test_parse(self):
        with open(self.html_test_file) as f:
            content = f.read()
            f.close()

        provider = OxfordParkAndRideProvider()
        carparks = provider.parse_html(content)

        seacourt = carparks["osm:34425625"]
        self.assertEqual(seacourt['percentage'], 34)
        self.assertEqual(seacourt['spaces'], 514)
        self.assertEqual(seacourt['name'], "Seacourt Park & Ride OX2 0HP")
        self.assertEqual(seacourt['capacity'], 784)
        self.assertEqual(seacourt['unavailable'], False)

        pear_tree = carparks["osm:4333225"]
        self.assertEqual(pear_tree['percentage'], 100)
        self.assertEqual(pear_tree['spaces'], 0)
        self.assertEqual(pear_tree['name'], "Pear Tree Park & Ride OX2 8JD")
        self.assertEqual(pear_tree['capacity'], 1084)
        self.assertEqual(pear_tree['unavailable'], True)