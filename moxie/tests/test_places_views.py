import unittest

from moxie.places.views import Search


class ServiceViewTestCase(unittest.TestCase):

    def test_acceptable_keys(self):
        arguments = {'filter': 'true',
                     'order': 'asc',
                     'search': 'blah',
                     'accessible_toilets': 'true',
                     'accessible_entrance': 'false'}
        acceptable_values = [('accessible', '_has_accessible')]
        additional_filters = Search._get_additional_filters(arguments, acceptable_values)
        self.assertListEqual(sorted(additional_filters),
                             sorted(['_has_accessible_toilets:true', '_has_accessible_entrance:false']))
