import unittest

from moxie.core.provider import Provider


class ProviderTest(unittest.TestCase):

    def test_base_provider_handles(self):
        self.assertFalse(Provider().handles('foo'))

    def test_base_provider_invoke(self):
        with self.assertRaises(NotImplementedError):
            Provider().invoke('foo')
