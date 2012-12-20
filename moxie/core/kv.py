import urlparse
import importlib

from moxie.core.service import Service
from werkzeug.local import LocalProxy

SUPPORTED_KV_STORES = {'redis': ('redis', 'StrictRedis')}


class KVService(Service):
    """:class:`~moxie.core.service.Service` for accessing a Key-Value store.
    This is the secondary datastore used within Moxie. General usage should
    be for caching and as a non-critical data store.

    Most development has taken place with `redis <http://redis.io>`_ being used
    as the KV store. Currently this is the only fully supported KV store, see:
    :py:data:`moxie.core.kv.SUPPORTED_KV_STORES` for details.
    """

    def __init__(self, backend_uri):
        self._backend = self._get_backend(backend_uri)

    @staticmethod
    def _get_backend(kv_uri):
        """Following the same pattern found in
        :py:func:`moxie.core.search.SearchService._get_backend`

        :param kv_uri: URI to the Key-value store for example
                       ``redis://foo.bar/bucket``.
        """
        kv_uri = urlparse.urlparse(kv_uri)
        if kv_uri.scheme in SUPPORTED_KV_STORES:
            host = kv_uri.hostname
            port = int(kv_uri.port) if kv_uri.port else 6379
            db = kv_uri.path.strip('/')
            db = db or 0
            kv_module, kv_klass = SUPPORTED_KV_STORES[kv_uri.scheme]
            kv_imp = importlib.import_module(kv_module)
            kv = getattr(kv_imp, kv_klass)
            return kv(host=host, port=port, db=db, password=kv_uri.password)
        else:
            raise NotImplementedError("Moxie could not find an implementation for %s." % kv_uri.scheme)

    def get(self, key):
        return self._backend.get(key)

    def set(self, key, value):
        return self._backend.set(key, value)

    def setex(self, key, expiry, value):
        return self._backend.setex(key, expiry, value)
        
    def healthcheck(self):
        """Healthcheck query to the backend
        """
        # TODO this query (ping) is specific to Redis, it should be made generic at some points
        try:
            result = self._backend.ping()
            if result:
                return True, "OK"
            else:
                return False, "FAILED TO PING"
        except Exception as e:
            return False, e

kv_store = LocalProxy(KVService.from_context)
