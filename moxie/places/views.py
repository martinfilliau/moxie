from flask import request, current_app, url_for, abort, redirect, jsonify
from moxie.core.views import ServiceView, accepts
from moxie.core.search import searcher
from moxie.places.importers.helpers import find_type_name


class Search(ServiceView):
    methods = ['GET', 'OPTIONS']
    default_search = '*'
    default_allow_headers = 'geo-position'

    def format_results(self, query, results):
        out = []
        for doc in results['response']['docs']:
            lon, lat = doc['location'].split(',')
            poi = {
                'id': doc['id'],
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
            identifiers = doc['identifiers']
            for identifier in identifiers:
                if identifier.startswith('naptan:'):
                    path = url_for('transport.busrti')
                    poi['hasRti'] = "{0}?id={1}".format(path, identifier.split(":")[1])
            try:
                poi['type'] = find_type_name(doc.get('type')[0])
            except KeyError:
                pass
            out.append(poi)
        return {'query': query, 'results': out}

    def get_results(self, original_query, location):
        query = original_query or self.default_search
        results = searcher.search_nearby(query, location)
        if results.json['response']['numFound'] == 0:
            if results.json['spellcheck']['suggestions']:
                suggestion = str(results.json['spellcheck']['suggestions'][-1])
                results = self.get_results(suggestion, location)
                return results
            else:
                return {}
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


class PoiDetail(ServiceView):

    def handle_request(self, id):
        if id.endswith('/'):
            id = id.split('/')[0]
        results = searcher.get_by_ids([id])
        # First do a GET request by its ID
        if results.json['response']['docs']:
            doc = results.json['response']['docs'][0]
            return jsonify(doc)
        else:
            # If no result, do a SEARCH request on IDs
            results = searcher.search_for_ids("identifiers", [id])
            if results.json['response']['docs']:
                doc = results.json['response']['docs'][0]
                path = url_for('places.poidetail', id=doc['id'])
                return redirect(path, code=301)
            else:
                abort(404)

    @accepts('application/json')
    def as_json(self, response):
        return response