from flask import request, render_template
from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher


class Search(ServiceView):
    methods = ['GET']

    def __init__(self, *args, **kwargs):
        super(Search, self).__init__(*args, **kwargs)

    def format_results(self, query, results):
        out = []
        for doc in results['response']['docs']:
            lon, lat = doc['location'].split(',')
            out.append({
                'name': doc['name'],
                'lon': lon,
                'lat': lat,
                'distance': doc['_dist_'],
                })
        return {'query': query, 'results': out}

    def get_results(self, query, location):
        results = searcher.search_nearby(query, location)
        # TODO(?) new query should be shown to the user
        if results.json['response']['numFound'] == 0:
            new_query = str(results.json['spellcheck']['suggestions'][-1])
            results = self.get_results(new_query, location)
        return self.format_results(query, results.json)

    def handle_request(self):
        if not request.args:
            # No search q and no location
            return dict()
        query = request.args.get('q', '*')
        location = request.args.get('lat', None), request.args.get('lon', None)
        return self.get_results(query, location)

    @accepts('text/html')
    def as_html(self, response):
        return render_template('places/search.html', **response)
