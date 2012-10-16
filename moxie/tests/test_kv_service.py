import unittest
import mock

from moxie.core.kv import SUPPORTED_KV_STORES, KVService


MockKV = mock.Mock()


class KeyValueServiceTestCase(unittest.TestCase):

    def setUp(self):
        SUPPORTED_KV_STORES['foobar'] = ('moxie.tests.test_kv_service', 'MockKV')

    def test_get_kv_backend(self):
        KVService._get_backend('foobar://foo.bar:4000/collection')
        MockKV.assert_called_with(host='foo.bar', password=None, db='collection', port=4000)

    def test_create_kv_service(self):
        kv = KVService('foobar://foo.bar/collection')
        self.assertEqual(kv._backend, MockKV())

    def test_nonexistant_kv_service(self):
        with self.assertRaises(NotImplementedError):
            KVService('mykvstore://localhost/one')
