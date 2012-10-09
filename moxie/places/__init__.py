from flask import Blueprint

from .views import Search, PoiDetail, RTI

places = Blueprint('places', __name__)


# URL Rules
places.add_url_rule('/search', view_func=Search.as_view('search'))
places.add_url_rule('/<path:ident>', view_func=PoiDetail.as_view('poidetail'))
places.add_url_rule('/<path:ident>/rti', view_func=RTI.as_view('rti'))
