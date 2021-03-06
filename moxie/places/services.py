import logging
import urllib
import json

from itertools import izip
from functools import partial

from moxie.core.service import Service
from moxie.core.kv import kv_store
from moxie.core.search import searcher
from moxie.places.importers.helpers import get_types_dict
from moxie.places.solr import doc_to_poi


logger = logging.getLogger(__name__)


TYPE_FACET = 'type'


class POIService(Service):

    default_search = '*:*'
    # (friendly_name, internal_name) pairs of key prefixes
    key_transforms = [
        ('accessibility', '_accessibility'),
        ('library', '_library'),
        ('is', '_is')
    ]
    INBOUND = 1
    OUTBOUND = 2

    def __init__(self, prefix_keys="_", identifiers_field='identifiers'):
        """POI service
        :param prefix_keys: prefix used for keys not being in the schema of the search engine
        """
        self.prefix_keys = prefix_keys
        self.identifiers_field = identifiers_field

    def _transform_arg(self, arg, direction=1):
        for transform in self.key_transforms:
            before, after = transform
            if direction is self.OUTBOUND:
                before, after = after, before
            if arg.startswith(before):
                return arg.replace(before, after, 1)
        return arg

    def _args_to_internal(self, args):
        transformer = partial(self._transform_arg, direction=self.INBOUND)
        return map(transformer, args)

    def _args_to_friendly(self, args):
        transformer = partial(self._transform_arg, direction=self.OUTBOUND)
        return map(transformer, args)

    def get_results(self, original_query, location, start, count,
                    pois_type=None, types_exact=None, filter_queries=None,
                    facets=(TYPE_FACET,), geofilter_centre=None, geofilter_distance=None):
        """Search POIs
        :param original_query: fts query
        :param location: latitude,longitude
        :param start: index of the first result of the page
        :param count: number of results for the page
        :param pois_type: (optional) type from the hierarchy of types to look for
        :param types_exact: (optional) exact types to search for (cannot be used in combination of type atm)
        :param facets: (optional) list of fields to be returned as facets defaults to the `type` facet.
        :param geofilter_centre: (optional) lat/lon of the centre to start geofiltering
        :param geofilter_distance: (optional) distance in km to geofilter
        :return list of domain objects (POIs), total size of results and facets on type
        """
        filter_queries = filter_queries or []
        filter_queries = self._args_to_internal(filter_queries)
        query = original_query or ''

        SEARCH_FIELDS = {
            'name': None,
            'alternative_names': 0.8,
            'type_name': 0.3,
            'tags': 0.5,
            '_courses_name': 0.7,
            'hidden_names': 0.7,
        }

        # boost the score of documents in cases where all of the terms
        # in the "q" param appear in close proximity
        PHRASE_FIELDS = {
            'name': 1.0,
            'alternative_names': 0.9,
            'hidden_names': 0.9,
        }

        if ' ' not in query and query:
            # only search in identifiers if it's a single
            # word query
            SEARCH_FIELDS[self.identifiers_field] = 0.8
            query = "{original} OR {field}:*\:{value}".format(original=query,
                                                              field=self.identifiers_field,
                                                              value=query)

        q = {'defType': 'edismax',
             'spellcheck.collate': 'true',
             'q': query,
             'q.alt': self.default_search,
             'qf': self._build_parameter_value(SEARCH_FIELDS),
             'pf': self._build_parameter_value(PHRASE_FIELDS)
             }

        internal_facets = []
        if facets:
            internal_facets = self._args_to_internal(facets)
            q.update({'facet': 'true',
                      'facet.sort': 'index',
                      'facet.mincount': '1',
                      'facet.field': internal_facets})
        if location:
            lat, lon = location
            q['sfield'] = 'location'
            q['pt'] = '%s,%s' % (lat, lon)
            q['boost'] = 'recip(geodist(),2,200,20)'  # boost by geodist (linear function: 200/2*x+20)
            q['sort'] = 'score desc'                  # sort by score
            q['fl'] = '*,_dist_:geodist()'
        elif original_query:
            # no location provided but full-text search query provided
            q['sort'] = 'score desc'
        else:
            # no full-text query provided, sorting by name
            q['sort'] = 'name_sort asc'

        if geofilter_centre and geofilter_distance:
            filter_queries.append("{{!geofilt sfield=location pt={lat},{lon} d={distance}}}".format(lat=geofilter_centre[0],
                                                                                                    lon=geofilter_centre[1],
                                                                                                    distance=geofilter_distance))

        # TODO make a better filter query to handle having type and types_exact at the same time
        if pois_type:
            # filter on one specific type (and its subtypes)
            q['f.type.facet.prefix'] = pois_type + "/"  # we only want to display sub-types as the facet
            filter_queries.append('type_exact:{pois_type}*'.format(pois_type=pois_type.replace('/', '\/')))
        elif types_exact:
            # filter by a list of specific types (exact match)
            filter_queries.append('type_exact:({types})'.format(types=" OR ".join('"{t}"'.format(t=t)
                                                                                  for t in types_exact)))

        response = searcher.search(q, fq=filter_queries, start=start, count=count)

        # if no results, try to use spellcheck suggestion to make a new request
        if not response.results:
            if response.query_suggestion:
                suggestion = response.query_suggestion
                return self.get_results(suggestion, location, start, count,
                                        pois_type=pois_type, types_exact=types_exact,
                                        facets=facets,
                                        filter_queries=filter_queries)
            else:
                return [], 0, None
        if response.facets:
            facet_values = {}
            for internal_name, friendly_name in zip(internal_facets, facets):
                vals = response.facets['facet_fields'].get(internal_name, None)
                if vals:
                    # Place in iterator so zip steps through vals
                    vals = iter(vals)
                    vals = dict(zip(vals, vals))
                    facet_values[friendly_name] = vals
        else:
            facet_values = None
        return [doc_to_poi(r, self.prefix_keys) for r in response.results], response.size, facet_values

    def get_place_by_identifier(self, ident):
        """Get place by identifier
        :param ident: identifier to lookup
        :return one POI or None if no result
        """
        results = self.get_places_by_identifiers([ident])
        if results:
            return results[0]
        else:
            return None

    def get_places_by_identifiers(self, idents):
        """Get places by identifiers
        Search in all identifiers if not found.
        :param idents: identifiers to lookup
        :return list of POI or None if no result
        """
        response = searcher.get_by_ids(idents)
        # First do a GET request by IDs
        if response.results:
            return [doc_to_poi(result, self.prefix_keys) for result in response.results]
        else:
            # If no result, do a SEARCH request on IDs
            return self.search_places_by_identifiers(idents)

    def search_place_by_identifier(self, ident):
        """Search for a place by an identifier
        :param ident: identifier to lookup
        :return a POI or None if no result
        """
        results = self.search_places_by_identifiers([ident])
        if results:
            return results[0]
        else:
            return None

    def search_places_by_identifiers(self, idents):
        """Search for a place by its identifiers
        :param ident: identifier to lookup
        :return POI or None if no result
        """
        response = searcher.search_for_ids(self.identifiers_field, idents)
        if response.results:
            return [doc_to_poi(result, self.prefix_keys) for result in response.results]
        else:
            return None

    def get_types(self):
        """Get types of POI
        :return dict of types
        """
        return get_types_dict()

    def get_organisational_descendants(self, ident):
        desc = kv_store.get(ident)
        if desc:
            return json.loads(desc)
        else:
            return None

    def suggest_pois(self, query, types_exact, start, count):
        """Suggest POIs based on name
        :param query: full-text query
        :param types_exact: list of type to filter
        :return list of documents
        """
        filter_queries = []
        q = {'q': query,
             'fl': 'id,name,type,type_name,address'}
        # TODO no need to return the full response?
        if types_exact:
            filter_queries.append('type_exact:({types})'.format(types=" OR ".join('"{t}"'.format(t=t)
                                                                              for t in types_exact)))
        response = searcher.suggest(q, fq=filter_queries, start=start, count=count)
        return [doc_to_poi(r) for r in response.results]

    def _build_parameter_value(self, d):
        """Build a solr string for fields/boost
        :param d: dict
        :return string
        """
        qfs = []
        for field_name, boost in d.iteritems():
            if boost:
                qfs.append("{name}^{boost}".format(name=field_name,
                                                   boost=boost))
            else:
                qfs.append(field_name)
        return ' '.join(qfs)