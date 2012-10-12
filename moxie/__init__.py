from flask import Flask
from moxie.places import places_blueprint
from moxie.library import library_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object('moxie.default_settings')
    try:
        app.config.from_envvar('MOXIE_SETTINGS')
    except RuntimeError:
        # Env variable not set.
        pass

    # Register Moxie apps
    app.register_blueprint(places_blueprint, url_prefix='/places')
    app.register_blueprint(library_blueprint, url_prefix='/library')
    return app
