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
    """ServiceView with some helper methods for calculating a HMAC
    (Keyed-Hashing for Message Authentication).

        http://www.ietf.org/rfc/rfc2104.txt

    This ServiceView handles only calculating a HMAC from a given shared secret
    between the service and user. It does not specify where the shared secret
    is scored or how to access it. This is the responsibility of the service
    itself.

    HMAC Signatures are created from the request headers specified in
    ``HMACView._HMAC_HEADERS``. The template used to assemble the canonical
    representation (before creating a signature) is specified in
    ``HMACView._HMAC_TEMPLATE``.
    """
    _HMAC_HEADERS = ['date', 'x-hmac-nonce']
    _HMAC_TEMPLATE = """{method}\n{url}\n{headers}"""

    def _get_canonical_rep(self):
        headers = []
        try:
            for header in self._HMAC_HEADERS:
                headers.append("%s:%s" % (
                    header.lower(), request.headers[header])
                )
            # Test the authorization header is included
            # however we don't include it in our signature
            request.headers['authorization']
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

    def check_auth(self, secret):
        """Call with the shared secret between the service and user,
        ``check_auth`` will create the HMAC Signature for the current
        ``flask.request`` and check it aligns with the one provided.

        If the signatures are equal (an authorised request) returns True.
        Otherwise raises ``HMACSignatureMismatch`` with the reason for the
        failure.
        """
        rep = self._get_canonical_rep()
        hmac_hash = hmac.new(secret, rep, sha1)
        request_hash = request.headers['Authorization']
        if request_hash == hmac_hash.hexdigest():
            return True
        else:
            raise HMACSignatureMismatch()
