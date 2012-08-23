from flask import Blueprint, request, jsonify
from moxie.core.views import ServiceView, register_mimetype
from moxie.core.search.solr import SolrSearch


places = Blueprint('places', __name__, template_folder='templates')


class Search(ServiceView):

    def __init__(self, searcher, *args, **kwargs):
        self.searcher = searcher
        super(Search, self).__init__(*args, **kwargs)

    def get_results(self, query, location):
        return self.searcher.search_nearby(query, location)

    @register_mimetype('application/json')
    def json_results(self):
        query = request.args.get('q', '*')
        location = request.args.get('lat', None), request.args.get('lon', None)
        results = self.get_results(query, location)
        return jsonify(results.json)


solr = SolrSearch('collection1')
places.add_url_rule('/search', view_func=Search.as_view('search', solr))
