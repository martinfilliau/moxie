from flask import request, render_template, jsonify, current_app
from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher
from moxie.places.importers.helpers import find_type_name


class Search(ServiceView):
    methods = ['GET']
    default_search = '*'

    def format_results(self, query, results):
        out = []
        for doc in results['response']['docs']:
            lon, lat = doc['location'].split(',')
            out.append({
                'name': doc['name'],
                'lon': lon,
                'lat': lat,
                'distance': doc['_dist_'],
                'opening_hours': doc.get('opening_hours', ''),
                'address': doc.get('address', ''),
                'website': doc.get('website', ''),
                'phone': doc.get('phone', ''),
                'type': find_type_name(doc.get('type')[0])
                })
        return {'query': query, 'results': out}

    def get_results(self, original_query, location):
        query = original_query or self.default_search
        results = searcher.search_nearby(query, location)
        # TODO(?) new query should be shown to the user
        if results.json['response']['numFound'] == 0:
            new_query = str(results.json['spellcheck']['suggestions'][-1])
            results = self.get_results(new_query, location)
        return self.format_results(original_query, results.json)

    def handle_request(self):
        response = dict()
        if 'Geo-Position' in request.headers:
            response['lat'], response['lon'] = request.headers['Geo-Position'].split(';')
        return response

    @accepts('application/json')
    def as_json(self, response):
        query = request.args.get('q', None)
        if 'lat' in response and 'lon' in response:
            location = response['lat'], response['lon']
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = request.args.get('lat', default_lat), request.args.get('lon', default_lon)
        response.update(self.get_results(query, location))
        return jsonify(response)

    @accepts('text/html')
    def as_html(self, response):
        response['query'] = request.args.get('q', '')
        lat, lon = current_app.config['DEFAULT_LOCATION']
        response['lat'] = request.args.get('lat', lat)
        response['lon'] = request.args.get('lon', lon)
        return render_template('places/search.html', **response)
