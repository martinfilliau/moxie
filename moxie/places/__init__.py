from .views import Search


# URL Rules
places.add_url_rule('/search', view_func=Search.as_view('search'))
