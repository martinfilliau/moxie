from os import path

from werkzeug.exceptions import default_exceptions, HTTPException
from flask import jsonify

from requests.exceptions import Timeout


from moxie.core.configurator import Configurator
from moxie.core.app import Moxie
from moxie.core.exceptions import exception_handler


def create_app():
    app = Moxie(__name__)
    configurator = Configurator(app)
    cfg_path = path.join(app.root_path, 'default_settings.yaml')
    configurator.from_yaml(cfg_path)
    configurator.from_envvar('MOXIE_SETTINGS', silent=True)

    # Exceptions handling
    for code in default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = exception_handler

    return app
