from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object('moxie.default_settings')
    try:
        app.config.from_envvar('MOXIE_SETTINGS')
    except RuntimeError:
        # Env variable not set.
        pass

    with app.app_context():
        # Import Moxie apps
        from moxie.places import places
        from moxie.library import library
        # Register Moxie apps
        app.register_blueprint(places, url_prefix='/places')
        app.register_blueprint(library, url_prefix='/library')
    return app
