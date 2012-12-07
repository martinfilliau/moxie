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