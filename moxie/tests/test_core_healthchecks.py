import unittest
import mock

from moxie.core.healthchecks import check_services, run_healthchecks


class HealthchecksTestCase(unittest.TestCase):

    def setUp(self):
        self.HEALTHCHECKS = {'service': {'moxie.core.kv.KVService': {'backend': 'redis://127.0.0.1:8080/1'}}}

    def test_call_service(self):
        with mock.patch('moxie.core.kv.KVService') as KVService:
            # Needs more test, cannot mock methods as expected (?)
            #KVService._backend.ping.return_value = True
            #KVService.healthcheck.return_value = True
            overall, result = run_healthchecks(self.HEALTHCHECKS)
        KVService.assert_called_with(backend='redis://127.0.0.1:8080/1')