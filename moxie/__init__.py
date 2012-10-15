from flask import Flask
from moxie.places import create_blueprint as create_places_blueprint
from moxie.library import create_blueprint as create_library_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object('moxie.default_settings')
    try:
        app.config.from_envvar('MOXIE_SETTINGS')
    except RuntimeError:
        # Env variable not set.
        pass

    # Register Moxie apps
    app.register_blueprint(create_places_blueprint('places'),
            url_prefix='/places')
    app.register_blueprint(create_library_blueprint('library'),
            url_prefix='/library')
    return app
