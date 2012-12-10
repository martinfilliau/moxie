import unittest

import flask
from moxie.core.representations import HalJsonRepresentation, get_nav_links


app = flask.Flask(__name__)


class RepresentationsTestCase(unittest.TestCase):

    def test_hal_json_representation(self):
        links = {'self': {'href': 'abc'}}
        values = {'a': 'b'}
        representation = HalJsonRepresentation(values, links)
        self.assertTrue('_links' in representation.as_dict())
        self.assertFalse('_embedded' in representation.as_dict())
        self.assertDictContainsSubset(values, representation.as_dict())

    def test_hal_json_representation_embed(self):
        links = {'self': {'href': 'ahdhd'}}
        values = {'c': 'd'}
        embed = {'s': 'g'}
        representation = HalJsonRepresentation(values, links, embed)
        self.assertTrue('_links' in representation.as_dict())
        self.assertTrue('_embedded' in representation.as_dict())
        self.assertDictContainsSubset(values, representation.as_dict())

    def test_nav_links(self):
        app.add_url_rule('/', endpoint='a')
        with app.test_request_context():
            links = get_nav_links('a', 0, 10, 20)
            self.assertEqual(links['hl:first']['href'], '/?count=10')
            self.assertEqual(links['hl:next']['href'], '/?count=10&start=10')
            self.assertEqual(links['hl:last']['href'], '/?count=10&start=10')
            self.assertFalse('hl:prev' in links)
            self.assertEqual(links['curie']['name'], 'hl')

            links2 = get_nav_links('a', 20, 10, 30)
            self.assertEqual(links2['hl:first']['href'], '/?count=10')
            self.assertEqual(links2['hl:prev']['href'], '/?count=10&start=10')
            self.assertEqual(links2['hl:last']['href'], '/?count=10&start=20')
            self.assertFalse('hl:next' in links2)
            self.assertEqual(links2['curie']['name'], 'hl')