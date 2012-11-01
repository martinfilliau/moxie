from flask import url_for

from moxie.core.service import Service
from moxie.library.providers.oxford_z3950 import LibrarySearchQuery
from moxie.places.services import POIService
from moxie.places.importers.helpers import simplify_doc_for_render


class LibrarySearchService(Service):
    """Library search service
    """

    def __init__(self, providers=None):
        self.providers = providers or []

    def get_provider(self):
        """Get a provider for searching libraries
        TODO this currently returns the first provider in the list
        """
        return self.providers[0]

    def search(self, title, author, isbn):
        """Search for media in the given provider.
        :param title: title
        :param author: author
        :param isbn: isbn
        :return list of results
        """
        z = self.get_provider()
        q = LibrarySearchQuery(title, author, isbn)
        poi_service = POIService.from_context()
        results = z.library_search(q)
        for result in results:
            result['_self'] = url_for('library.resourcedetail', id=result['control_number'])
            for location in result['holdings']:
                # TODO place identifier has to be set in configuration
                poi = poi_service.get_place_by_identifier('olis-aleph:{0}'.format(location.replace('/', '\/')))
                if poi:
                    result['holdings'][location]['poi'] = simplify_doc_for_render(poi)
        return results

    def get_media(self, control_number):
        """Get a media by its control number
        :param control_number: ID of the media
        :return result or None
        """
        z = self.get_provider()
        result = z.control_number_search(control_number)
        return result