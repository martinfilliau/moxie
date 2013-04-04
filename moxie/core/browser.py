import logging

from flask import _app_ctx_stack, redirect

from moxie.core.views import ServiceView, accepts
from moxie.core.representations import HALRepresentation, JSON, HAL_JSON

logger = logging.getLogger(__name__)


class RootView(ServiceView):

    def handle_request(self):
        ctx = _app_ctx_stack.top
        services = ctx.app.blueprints.keys()
        self.browser_url = ctx.app.config.get('HAL_BROWSER_REDIRECT', None)
        representation = HALRepresentation({})
        representation.add_link('self', '/')
        representation.add_curie('hl', 'http://moxie.readthedocs.org/en/latest/http_api/services.html#{rel}')
        for service in services:
            representation.add_link('hl:{app}'.format(app=service), '/{blueprint}'.format(blueprint=service))
        return representation

    @accepts(JSON, HAL_JSON)
    def as_json(self, representation):
        return representation.as_json()

    @accepts("text/html")
    def as_html(self, representation):
        if self.browser_url:
            return redirect(self.browser_url)
        else:
            return self.as_json(representation)
