from flask import Flask
from werkzeug.routing import Rule


class BlueprintNotRegistered(Exception):
    pass


class Moxie(Flask):
    """Moxie subclass of the Flask WSGI application object"""

    def blueprint_context(self, blueprint_name, *args, **kwargs):
        """Returns a WSGI environment. In Flask terms this means creating
        both an application and request context. We then coerce this Request
        into thinking it's calling a blueprint passed as `blueprint_name`.
        Additional paramaters are passed through to
        :func:`flask.app.Flask.test_request_context`.

        Within Moxie this is used for our Celery tasks. Since we don't have
        incoming HTTP requests we can fake one and access all our `Services`
        in the usual manner.

        :param blueprint_name: a string naming the blueprint you want to
                               create a context for.
        """
        request_context = self.test_request_context(*args, **kwargs)
        if blueprint_name not in self.blueprints:
            raise BlueprintNotRegistered(
                    "Couldn't find blueprint: %s" % (blueprint_name))
        endpoint = "%s.*" % blueprint_name
        if request_context.request.url_rule:
            request_context.request.url_rule.endpoint = endpoint
        else:
            mock_rule = Rule('/', endpoint=endpoint)
            request_context.request.url_rule = mock_rule
        return request_context
