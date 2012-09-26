from flask import request, current_app
from moxie.core.views import ServiceView
from moxie.core.search import searcher
from moxie.places.importers.helpers import find_type_name
from moxie.transport.views import BusRti


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    default_search = '*'
    default_allow_headers = 'geo-position'

    def format_results(self, query, results):
        out = []
        for doc in results['response']['docs']:
            lon, lat = doc['location'].split(',')
            poi = {
                'name': doc['name'],
                'lon': lon,
                'lat': lat,
                'distance': doc['_dist_'],
                'address': doc.get('address', ''),
                'website': doc.get('website', ''),
                'phone': doc.get('phone', ''),
            }
            if 'opening_hours' in doc:
                poi['opening_hours'] = doc.get('opening_hours')
            if 'collection_times' in doc:
                poi['collection_times'] = doc.get('collection_times')
            # TODO URL of API method should NOT be hard-coded like this
            identifiers = doc['identifiers']
            for identifier in identifiers:
                if identifier.startswith('naptan:'):
                    poi['hasRti'] = "/transport/bus/rti?id={0}".format(identifier.split(":")[1])
            try:
                poi['type'] = find_type_name(doc.get('type')[0])
            except KeyError:
                pass
            out.append(poi)
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
        query = request.args.get('q', None)
        if 'lat' in response and 'lon' in response:
            location = response['lat'], response['lon']
        else:
            default_lat, default_lon = current_app.config['DEFAULT_LOCATION']
            location = request.args.get('lat', default_lat), request.args.get('lon', default_lon)
        response.update(self.get_results(query, location))
        return response