import jinja2

from flask import current_app


@current_app.context_processor
def raw_include_wrapper():
    """Return a template without jinja parsing.
    Used by us to pass through handlebars into HTML for debugging
    Adds into the global template context.
    """
    def raw_include(template_name):
        env = current_app.jinja_env
        return jinja2.Markup(env.loader.get_source(env, template_name)[0])
    return {'raw_include': raw_include}
