from flask import url_for


class Representation(object):
    pass


class JsonRepresentation(Representation):
    content_type = "application/json"


class HalJsonRepresentation(JsonRepresentation):
    content_type = "application/hal+json"

    def __init__(self, values, links, embed=None):
        self.links = links
        self.embed = embed or []
        self.values = values

    def as_dict(self):
        representation = self.values
        representation['_links'] = self.links
        if self.embed:
            representation['_embedded'] = self.embed
        return representation


def get_nav_links(endpoint, start, count, size, **kwargs):
    """Prepare navigation links for a set of results
    :param endpoint: endpoint (URL) to use
    :param start: first result
    :param count: number of results
    :param size: total number of resuts
    :param kwargs: rest of arguments to use
    :return dict of navigation links
    """
    nav = {'curie': {
        'name': 'hl',
        'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
        'templated': True,
        },
           'hl:last': {
               'href': url_for(endpoint, start=size-count, count=count, **kwargs)
           },
           'hl:first': {
               'href': url_for(endpoint, count=count, **kwargs)
           }
    }
    if size > start+count:
        nav['hl:next'] = {
            'href': url_for(endpoint, start=start+count, count=count, **kwargs)
        }
    if start > 0 and size >= start+count:
        nav['hl:prev'] = {
            'href': url_for(endpoint, start=start-count, count=count, **kwargs)
        }
    return nav