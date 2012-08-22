import unittest

from moxie.places.importers.helpers import merge_docs, merge_identifiers

class HelpersTestCase(unittest.TestCase):

    current_doc = {
            'meta_precedence': 10,
            'name': 'moxie',
            'foo_url': 'https://github.com/ox-it/moxie',
            'identifier': ['foo:123'],
            }

    def test_lower_precedence(self):
        new_doc = {'name': 'molly', 'identifier': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, 9)
        self.assertEqual(self.current_doc['name'], merged_doc['name'])
        self.assertEqual(self.current_doc['meta_precedence'], merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifier']))

    def test_greater_precedence(self):
        precedence = 11
        new_doc = {'name': 'molly', 'identifier': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, precedence)
        self.assertEqual(new_doc['name'], merged_doc['name'])
        self.assertEqual(precedence, merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifier']))

    def test_equal_precedence(self):
        precedence = 10
        new_doc = {'name': 'molly', 'identifier': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, precedence)
        self.assertEqual(self.current_doc['name'], merged_doc['name'])
        self.assertEqual(self.current_doc['meta_precedence'], merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifier']))

    def test_merge_identifiers(self):
        new_identifiers = ['osm:123', 'naptan:xyz']
        current_identifiers = ['foo:678']
        merged_idents = merge_identifiers(current_identifiers, new_identifiers)
        self.assertEqual(set(['osm:123', 'naptan:xyz', 'foo:678']), set(merged_idents))
