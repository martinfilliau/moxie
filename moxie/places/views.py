from flask import request, jsonify, render_template
from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher


class Search(ServiceView):
    methods = ['GET', 'POST']

    def __init__(self, *args, **kwargs):
        super(Search, self).__init__(*args, **kwargs)

    def get_results(self, query, location):
        return searcher.search_nearby(query, location)

    def handle_request(self):
        query = request.args.get('q', '*')
        location = request.args.get('lat', None), request.args.get('lon', None)
        if location == (None, None):
            return dict()
        else:
            results = self.get_results(query, location)
            # TODO should be extracted from this method, and new query should be shown to the user
            if results.json['response']['numFound'] == 0:
                new_query = str(results.json['spellcheck']['suggestions'][-1])
                results = self.get_results(new_query, location)
            return results.json

    @accepts('text/html')
    def as_html(self, response):
        return render_template('search.html', **response)
