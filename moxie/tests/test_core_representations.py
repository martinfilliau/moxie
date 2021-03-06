import unittest

import flask
from moxie.core.representations import HALRepresentation, get_nav_links


app = flask.Flask(__name__)


class RepresentationsTestCase(unittest.TestCase):

    def test_hal_json_representation(self):
        links = {'self': {'href': 'abc'}}
        values = {'a': 'b'}
        representation = HALRepresentation(values, links)
        self.assertTrue('_links' in representation.as_dict())
        self.assertFalse('_embedded' in representation.as_dict())
        self.assertDictContainsSubset(values, representation.as_dict())

    def test_hal_json_helper_representation(self):
        representation = HALRepresentation({'a':'b'})
        representation.add_link('self', '/a/b')
        representation.add_link('list', '/list', templated=True)
        representation.update_link('child', '/child/1')
        representation.update_link('child', '/child/2')
        representation.add_curie('cu', 'http://curie.com')
        representation.add_embed('rel', [HALRepresentation({'embed': 'yes'},
            links={'self':{'href':'a'}}).as_dict()])
        self.assertDictContainsSubset({'_links': {
            'self': {'href': '/a/b'},
            'list': {'href': '/list', 'templated': True},
            'child': [{'href': '/child/1'}, {'href': '/child/2'}],
            'curie': {'href': 'http://curie.com', 'name': 'cu', 'templated': True}}},
            representation.as_dict())
        self.assertDictContainsSubset(
            {'_embedded': {'rel': [{'embed': 'yes',
            '_links': {'self': {'href': 'a'}}}]}},
            representation.as_dict())

    def test_hal_json_representation_embed(self):
        links = {'self': {'href': 'ahdhd'}}
        values = {'c': 'd'}
        embed = {'s': 'g'}
        representation = HALRepresentation(values, links, embed)
        self.assertTrue('_links' in representation.as_dict())
        self.assertTrue('_embedded' in representation.as_dict())
        self.assertDictContainsSubset(values, representation.as_dict())

    def test_hal_json_embedded(self):
        representation = HALRepresentation({'key': 'value'})
        representation.add_embed('a', {'1': 'oo'})
        representation.add_embed('a', {'2': 'oo'})
        representation.add_embed('a', {'3': 'oo'})
        representation.add_embed('b', [{'a': 'oo'}, {'b': 'oo'}])
        representation.add_embed('b', {'c': 'oo'})
        self.assertDictContainsSubset({'_embedded': {'a': [{'1': 'oo'}, {'2': 'oo'}, {'3': 'oo'}],
                                                        'b': [{'a': 'oo'}, {'b': 'oo'}, {'c': 'oo'}]}},
                                      representation.as_dict())

    def test_nav_links(self):
        app.add_url_rule('/', endpoint='a')
        with app.test_request_context():
            links = get_nav_links('a', 0, 10, 20)
            self.assertEqual(links['hl:first']['href'], '/?count=10')
            self.assertEqual(links['hl:next']['href'], '/?count=10&start=10')
            self.assertEqual(links['hl:last']['href'], '/?count=10&start=10')
            self.assertFalse('hl:prev' in links)
            self.assertEqual(len(links['curies']), 1)
            self.assertEqual(links['curies'][0]['name'], 'hl')

            links2 = get_nav_links('a', 20, 10, 30)
            self.assertEqual(links2['hl:first']['href'], '/?count=10')
            self.assertEqual(links2['hl:prev']['href'], '/?count=10&start=10')
            self.assertEqual(links2['hl:last']['href'], '/?count=10&start=20')
            self.assertFalse('hl:next' in links2)
            self.assertEqual(len(links['curies']), 1)
            self.assertEqual(links2['curies'][0]['name'], 'hl')

            links3 = get_nav_links('a', 0, 10, 5)
            self.assertEqual(links3['hl:first']['href'], '/?count=10')
            self.assertEqual(links3['hl:last']['href'], '/?count=10')
            self.assertFalse('hl:next' in links3)
            self.assertFalse('hl:prev' in links3)
            self.assertEqual(len(links['curies']), 1)
            self.assertEqual(links3['curies'][0]['name'], 'hl')

            links4 = get_nav_links('a', 20, 20, 30)
            self.assertEqual(links4['hl:first']['href'], '/?count=20')
            self.assertEqual(links4['hl:last']['href'], '/?count=20&start=10')
            self.assertFalse('hl:next' in links4)
            self.assertEqual(links4['hl:prev']['href'], '/?count=20&start=0')
            self.assertEqual(len(links4['curies']), 1)
            self.assertEqual(links4['curies'][0]['name'], 'hl')

    def test_nav_links_with_facet(self):
        app.add_url_rule('/', endpoint='a')
        with app.test_request_context():
            links = get_nav_links('a', 0, 10, 20, facet=['this'])
            self.assertEqual(len(links['curies']), 2)
            curie_names = set([c['name'] for c in links['curies']])
            self.assertTrue('facet' in curie_names)
            self.assertTrue('hl' in curie_names)
