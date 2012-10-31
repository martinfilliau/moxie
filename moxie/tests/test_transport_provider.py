import unittest

from moxie.transport.providers import TransportRTIProvider


class FooProvider(TransportRTIProvider):

    def handles(self, foo):
        if foo == 'foo':
            return True

    def invoke(self, doc):
        return "bar"


class ProviderTest(unittest.TestCase):

    def setUp(self):
        self.provider = FooProvider()

    def test_base_provider_handles(self):
        self.assertFalse(TransportRTIProvider().handles('foo'))

    def test_base_provider_invoke(self):
        with self.assertRaises(NotImplementedError):
            TransportRTIProvider().invoke('foo')

    def test_foo_provider_callable(self):
        self.assertTrue(callable(self.provider))

    def test_foo_provider_invoke(self):
        self.assertEqual("bar", self.provider.invoke('foo'))

    def test_foo_provider_call(self):
        self.assertEqual(self.provider.invoke('foo'), self.provider('foo'))
