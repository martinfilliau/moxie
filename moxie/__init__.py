from os import path
from moxie.core.configurator import Configurator
from moxie.core.app import Moxie
from moxie.core.healthchecks import check_services


def create_app():
    app = Moxie(__name__)
    configurator = Configurator(app)
    cfg_path = path.join(app.root_path, 'default_settings.yaml')
    configurator.from_yaml(cfg_path)
    configurator.from_envvar('MOXIE_SETTINGS', silent=True)
    app.add_url_rule('/_health', view_func=check_services)
    return app
