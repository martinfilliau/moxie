from flask import Blueprint

from .views import Search, PoiDetail

places = Blueprint('places', __name__)

# URL Rules
places.add_url_rule('/search', view_func=Search.as_view('search'))
places.add_url_rule('/<path:id>', view_func=PoiDetail.as_view('poidetail'))