import hmac

from hashlib import sha1
from flask import request
from moxie.core.views import ServiceView


class HMACView(ServiceView):
    _HMAC_HEADERS = ['date']
    _HMAC_TEMPLATE = "{url}{data}{headers}"

    def _check_auth(self, user):
        headers = [request.headers[header] for header in self._HMAC_HEADERS]
        headers = ''.join(headers)
        context = {
            'url': request.url,
            'data': request.get_data(),
            'headers': headers,
        }
        message = self._HMAC_TEMPLATE.format(**context)
        print message
        hmac_hash = hmac.new(user.secret_key, message, sha1)
        print hmac_hash
        request_hash = request.headers['Authorization']
        print request_hash
        return request_hash == hmac_hash.hexdigest()
