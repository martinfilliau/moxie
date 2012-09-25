from flask import Blueprint

from .views import BusRti

transport = Blueprint('transport', __name__)

# URL Rules
transport.add_url_rule('/bus/rti', view_func=BusRti.as_view('busrti'))