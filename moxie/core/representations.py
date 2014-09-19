from flask import url_for, jsonify


# Mimetypes
JSON = "application/json"
HAL_JSON = "application/hal+json"

RELATIONS_CURIE = "http://moxie.readthedocs.org/en/latest/http_api/relations/{rel}.html"
FACET_CURIE = "http://moxie.readthedocs.org/en/latest/http_api/relations/facet.html"


class Representation(object):
    pass


class HALRepresentation(Representation):

    def __init__(self, values, links=None, embed=None):
        """HAL representation of a content with links and embedded documents.
        :param values: main values of the document
        :param links: _links of the document
        :param embed: _embedded documents
        """
        self.links = links or {}
        self.embed = embed or {}
        self.values = values

    # Representations of this object

    def as_dict(self):
        """Get a representation as a dict
        :return dict
        """
        representation = self.values
        representation['_links'] = self.links
        if self.embed:
            representation['_embedded'] = self.embed
        return representation

    def as_json(self):
        """Get a representation as JSON
        :return json string
        """
        return jsonify(self.as_dict())
        
    # Helpers methods
        
    def add_link(self, target, href, **kwargs):
        """Add a link in _links
        :param target: target of the link (e.g. "self")
        :param href: link
        """
        self.links[target] = {'href': href}
        if kwargs:
            self.links[target].update(kwargs)
            
    def add_links(self, links):
        """Add a list of links to the representation
        :param links: list of links
        """
        self.links.update(links)
            
    def update_link(self, target, href, **kwargs):
        """Update a link in _links (when it is a list of many links in a target)
        :param target: target of the link (e.g. "child")
        :param href: link
        """
        if not target in self.links:
            self.links[target] = []
        link = {'href': href}
        if kwargs:
            link.update(kwargs)
        self.links[target].append(link)
        
    def add_curie(self, name, href):
        """Add a curie
        :param name: name of the curie
        :param href: url of the curie
        """
        self.add_link('curie', href, name=name, templated=True)
        
    def add_embed(self, rel, value):
        """Add embedded documents
        :param rel: link relation type
        :param value: resource or list of resources
        """
        if not rel in self.embed:
            self.embed[rel] = value
        else:
            if isinstance(self.embed[rel], list):
                if isinstance(value, list):
                    self.embed[rel].extend(value)
                else:
                    self.embed[rel].append(value)
            else:
                # add to existing in a list
                self.embed[rel] = [self.embed[rel], value]


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
    nav = {'curies': [{'name': 'hl',
                       'href': RELATIONS_CURIE,
                       'templated': True}]}

    if 'facet' in kwargs:
        nav['curies'].append({'name': 'facet',
                              'href': FACET_CURIE})

    if size-count > 0:
        nav['hl:last'] = {
            'href': url_for(endpoint, start=size-count, count=count, **kwargs)}
    else:
        nav['hl:last'] = {
            'href': url_for(endpoint, count=count, **kwargs)}

    nav['hl:first'] = {
        'href': url_for(endpoint, count=count, **kwargs)}

    if size > start+count:
        nav['hl:next'] = {
            'href': url_for(endpoint, start=start+count, count=count, **kwargs)}

    if start > 0:
        nav['hl:prev'] = {
            'href': url_for(endpoint, start=start-count, count=count, **kwargs)}

    return nav
