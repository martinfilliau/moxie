from flask import Blueprint

from .views import OxfordDateToday


def create_blueprint(blueprint_name):
    oxford_dates_blueprint = Blueprint(blueprint_name, __name__)

    # URL Rules
    oxford_dates_blueprint.add_url_rule('/',
        view_func=OxfordDateToday.as_view('default'))

    return oxford_dates_blueprint