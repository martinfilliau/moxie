from flask import Blueprint, request, jsonify, render_template
from moxie.core.views import ServiceView, register_mimetype
from moxie.core.search.solr import SolrSearch


places = Blueprint('places', __name__, template_folder='templates')


class Search(ServiceView):
    methods = ['GET', 'POST']

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
        # TODO should be extracted from this method, and new query should be shown to the user
        if results.json['response']['numFound'] == 0:
            new_query = str(results.json['spellcheck']['suggestions'][-1])
            results = self.get_results(new_query, location)
        return jsonify(results.json)

    @register_mimetype('text/html')
    def html_form(self):
        return render_template('search.html')


solr = SolrSearch('collection1')
places.add_url_rule('/search', view_func=Search.as_view('search', solr))
