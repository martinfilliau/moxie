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

    def test_proxy_attr(self):
        """All attr access should be pased through to the _backend on the
        KVService, this applies also when calling methods.

        See docs on KVService.__getattr__ for more info
        """
        kv = KVService('foobar://foo.bar/collection')
        m1 = kv.nonexistantattr
        m2 = MockKV().nonexistantattr
        self.assertEqual(m1, m2)

    def test_proxy_method(self):
        kv = KVService('foobar://foo.bar/collection')
        m1 = kv.nonexistantmethod()
        m2 = MockKV().nonexistantmethod()
        self.assertEqual(m1, m2)
