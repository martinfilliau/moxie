from flask import Flask
from os import path
from moxie.core.configurator import Configurator


def create_app():
    app = Flask(__name__)
    configurator = Configurator(app)
    cfg_path = path.join(app.root_path, 'default_settings.yaml')
    configurator.from_yaml(cfg_path)
    configurator.from_envvar('MOXIE_SETTINGS', silent=True)
    return app
