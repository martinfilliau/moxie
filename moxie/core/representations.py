from flask import url_for


# Mimetypes
JSON = "application/json"
HAL_JSON = "application/hal+json"


class Representation(object):
    pass


class JsonRepresentation(Representation):
    content_type = "application/json"


class HalJsonRepresentation(JsonRepresentation):
    content_type = "application/hal+json"

    def __init__(self, values, links=None, embed=None):
        self.links = links or {}
        self.embed = embed or []
        self.values = values

    def as_dict(self):
        representation = self.values
        representation['_links'] = self.links
        if self.embed:
            representation['_embedded'] = self.embed
        return representation
        
    def add_link(self, target, href, **kwargs):
        """Add a link in _links
        :param target: target of the link (e.g. "self")
        :param href: link
        """
        self.links[target] = {'href': href}
        if kwargs:
            self.links[target].update(kwargs)


def get_nav_links(endpoint, start, count, size, **kwargs):
    """Prepare navigation links for a set of results
    :param endpoint: endpoint (URL) to use
    :param start: first result
    :param count: number of results
    :param size: total number of resuts
    :param kwargs: rest of arguments to use
    :return dict of navigation links
    """
    start, count, size = int(start), int(count), int(size)
    nav = {'curie': {
        'name': 'hl',
        'href': 'http://moxie.readthedocs.org/en/latest/http_api/relations.html#{rel}',
        'templated': True,
        },
    }

    if size-count > 0:
        nav['hl:last'] = {
                   'href': url_for(endpoint, start=size-count, count=count, **kwargs)
        }
    else:
        nav['hl:last'] = {
            'href': url_for(endpoint, count=count, **kwargs)
        }
    nav['hl:first'] = {
               'href': url_for(endpoint, count=count, **kwargs)
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