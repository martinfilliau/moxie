import urlparse

from flask import _app_ctx_stack
from werkzeug.local import LocalProxy

SUPPORTED_KV_STORES = ('redis',)


def get_kv_store():
    ctx = _app_ctx_stack.top
    kv_store = getattr(ctx, 'moxie_kv_store', None)
    if kv_store is None:
        kv_store_url = ctx.app.config['KV_STORE_URL']
        kv_store = _find_kv_store(kv_store_url)
        ctx.moxie_kv_store = kv_store
    return kv_store
kv_store = LocalProxy(get_kv_store)


def _find_kv_store(kv_url):
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
