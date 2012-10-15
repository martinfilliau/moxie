import urlparse

from moxie.core.service import Service
from werkzeug.local import LocalProxy

SUPPORTED_KV_STORES = ('redis',)


class KVService(Service):

    def __init__(self, backend_uri):
        self.backend = self._get_backend(backend_uri)

    @staticmethod
    def _get_backend(kv_url):
        kv_url = urlparse.urlparse(kv_url)
        if kv_url.scheme not in SUPPORTED_KV_STORES:
            raise NotImplemented("Moxie does not support %s." % kv_url.scheme)
        if kv_url.scheme == 'redis':
            import redis
            host = kv_url.hostname
            port = int(kv_url.port) if kv_url.port else 6379
            db = kv_url.path.strip('/')
            db = db or 0
            kv = redis.StrictRedis(host=host, port=port, db=db,
                    password=kv_url.password)
        return kv

    def get(self, key):
        return self.backend.get(key)

    def set(self, key, value):
        return self.backend.set(key, value)

    def setex(self, key, expiry, value):
        return self.backend.setex(key, expiry, value)

kv_store = LocalProxy(KVService.from_context)
