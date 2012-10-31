import hashlib
import json
import logging

from flask import request

from moxie.core.views import ServiceView
from moxie.core.kv import kv_store
from moxie.library.services import LibrarySearchService

logger = logging.getLogger(__name__)


class Search(ServiceView):

    CACHE_KEY_FORMAT = '{0}_library_{1}'
    CACHE_EXPIRE = 120   # seconds for cache to expire

    def handle_request(self):
        # 1. Request from Service
        title = request.args.get('title', None)
        author = request.args.get('author', None)
        isbn = request.args.get('isbn', None)

        # TODO validation

        results = self.get_search_result(title, author, isbn)

        # 2. Do pagination
        start = int(request.args.get('start', 0))
        count = int(request.args.get('count', 10))

        context = { 'size': len(results),
                    'results': results[start:(start+count)] }
        # TODO add "link" to next page or so (HATEOAS-like navigation?)
        return context

    def get_search_result(self, title, author, isbn):
        """Check the cache or call the service to retrieve
        search results
        :param title: search title
        :param author: search author
        :param isbn: search isbn
        :return list of results
        """
        search_string = "{0}{1}{2}".format(removeNonAscii(title), removeNonAscii(author), removeNonAscii(isbn))
        hash = hashlib.md5()
        hash.update(search_string)
        service = LibrarySearchService.from_context()
        cache = kv_store.get(self.CACHE_KEY_FORMAT.format(__name__, hash.hexdigest()))
        if cache:
            logger.debug("Search results from cache")
            return json.loads(cache)
        else:
            logger.debug("Search results from service")
            results = service.search(title, author, isbn)
            kv_store.setex(self.CACHE_KEY_FORMAT.format(__name__, hash.hexdigest()), self.CACHE_EXPIRE, json.dumps(results))
            return results


def removeNonAscii(s):
    if s:
        return "".join(i for i in s if ord(i)<128)
    else:
        return ""


class ResourceDetail(ServiceView):

    def handle_request(self, id):
        pass