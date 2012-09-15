from flask import Flask
from moxie.places import places


def create_app():
    app = Flask(__name__, static_folder='core/static', template_folder='core/templates')
    app.config.from_object('moxie.default_settings')
    try:
        app.config.from_envvar('MOXIE_SETTINGS')
    except RuntimeError:
        # Env variable not set.
        pass
    # Add context_processors to global context
    with app.app_context():
        import moxie.context_processors

    # Register Moxie apps
    app.register_blueprint(places, url_prefix='/places')
    return app
