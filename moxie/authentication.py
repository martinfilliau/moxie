import hmac

from hashlib import sha1
from flask import request

from moxie.core.views import ServiceView
from moxie.core.exceptions import ApplicationException


class HMACSignatureMismatch(ApplicationException):
    status_code = 401
    message = "Unauthorized"
    digest_header = 'HMACDigest realm="{realm}", '
    digest_header += 'reason="{reason}", '
    digest_header += 'algorithm="{algorithm}", '

    def __init__(self, realm="HMACDigest Moxie", reason="unauthorized",
                 algorithm="HMAC-SHA-1", payload=None):
        self.payload = payload
        self.headers = {
            'WWW-Authenticate': self.digest_header.format(
                realm=realm, reason=reason, algorithm=algorithm
            ),
        }


class HMACView(ServiceView):
    _HMAC_HEADERS = ['date', 'x-hmac-nonce']
    _HMAC_TEMPLATE = """{method}\n{url}\n{headers}"""

    def _get_canonical_rep(self):
        headers = []
        try:
            for header in self._HMAC_HEADERS:
                headers.append("%s:%s" % (
                    header.lower(), request.headers[header])
                )
        except KeyError as e:
            raise HMACSignatureMismatch(
                reason="missing header: %s" % e.message)
        headers = '\n'.join(headers)
        context = {
            'method': request.method.upper(),
            'url': request.url,
            'headers': headers,
        }
        representation = self._HMAC_TEMPLATE.format(**context)
        return representation

    def _check_auth(self, user):
        rep = self._get_canonical_rep()
        hmac_hash = hmac.new(user.secret_key, rep, sha1)
        request_hash = request.headers['Authorization']
        if request_hash == hmac_hash.hexdigest():
            return True
        else:
            raise HMACSignatureMismatch()
