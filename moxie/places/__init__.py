from flask import Blueprint

from .views import Search

places = Blueprint('places', __name__, template_folder='templates')

# URL Rules
places.add_url_rule('/search', view_func=Search.as_view('search'))
