import unittest
import mock
import flask

from moxie.places.importers.helpers import merge_docs, merge_keys, merge_values, find_type_name, prepare_document


app = flask.Flask(__name__)

class HelpersTestCase(unittest.TestCase):


    def setUp(self):
        self.current_doc = {
            'meta_precedence': 10,
            'name': 'moxie',
            'foo_url': 'https://github.com/ox-it/moxie',
            'identifiers': ['foo:123'],
        }
        self.ctx = app.test_request_context()
        self.ctx.push()


    def test_prepare_doc(self):
        """Relates to issue#62"""
        mock_results = mock.MagicMock()
        mock_results.results = [{}]
        doc = {'type': 'test/foo'}
        with mock.patch('moxie.places.importers.helpers.merge_docs') as mock_merge_docs:
            prepare_document(doc, mock_results, 1)
            mock_merge_docs.assert_called_with(mock_results.results[0], doc, 1)

    def test_merge_direction(self):
        """Tests the new document values are copied over to the current doc"""
        key = 'mykey'
        original_value = 'some value'
        current_doc = {key: original_value}
        new_doc = {key: 'some other value'}
        merged_doc = merge_docs(current_doc, new_doc, 9)
        self.assertEqual(merged_doc[key], new_doc[key])
        # original value changed
        self.assertNotEqual(merged_doc[key], original_value)

    def test_lower_precedence(self):
        new_doc = {'name': 'molly', 'identifiers': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, 9)
        self.assertEqual(self.current_doc['name'], merged_doc['name'])
        self.assertEqual(self.current_doc['meta_precedence'], merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifiers']))

    def test_greater_precedence(self):
        precedence = 11
        new_doc = {'name': 'molly', 'identifiers': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, precedence)
        self.assertEqual(new_doc['name'], merged_doc['name'])
        self.assertEqual(precedence, merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifiers']))

    def test_equal_precedence(self):
        precedence = 10
        new_doc = {'name': 'molly', 'identifiers': ['bar:xyz'],
                'bar_url': 'https://github.com/mollyproject/mollyproject'}
        merged_doc = merge_docs(self.current_doc, new_doc, precedence)
        self.assertEqual(self.current_doc['name'], merged_doc['name'])
        self.assertEqual(self.current_doc['meta_precedence'], merged_doc['meta_precedence'])
        self.assertEqual(new_doc['bar_url'], merged_doc['bar_url'])
        self.assertEqual(set(['foo:123', 'bar:xyz']), set(merged_doc['identifiers']))

    def test_merge_keys(self):
        new_doc = {'identifiers': ['osm:123', 'naptan:xyz']}
        current_doc = {'identifiers': ['foo:678']}
        merged_doc = merge_keys(current_doc, new_doc, ['identifiers'])
        self.assertEqual(set(['osm:123', 'naptan:xyz', 'foo:678']),
                set(merged_doc['identifiers']))

    def test_merge_multiple_keys(self):
        new_doc = {'identifiers': ['osm:123', 'naptan:xyz'], 'tags': ['bus stop']}
        current_doc = {'identifiers': ['foo:678'], 'tags': ['public urinal']}
        merged_doc = merge_keys(current_doc, new_doc, ['identifiers', 'tags'])
        self.assertEqual(set(['osm:123', 'naptan:xyz', 'foo:678']),
                set(merged_doc['identifiers']))
        self.assertEqual(set(['bus stop', 'public urinal']),
                set(merged_doc['tags']))

    def test_merge_values(self):
        a = ['a', 1, 2, 3]
        b = ['a', 'b', 'c', 3]
        merged = merge_values(a, b)
        self.assertEqual(set([1, 2, 3, 'a', 'b', 'c']), set(merged))

    def test_find_type_name(self):
        #with app.test_client() as c:
        self.assertEqual("University car park", find_type_name("/transport/car-park/university"))
        self.assertEqual("Transport", find_type_name("/transport"))
        self.assertEqual("Car park", find_type_name("/transport/car-park"))
        self.assertEqual("Book shops", find_type_name("/amenities/shop/book", singular=False))

    def tearDown(self):
        self.ctx.pop()
