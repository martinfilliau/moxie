class POI(object):

    def __init__(self, id, name, type, lat=None, lon=None, type_name=None, identifiers=None, short_name=None,
                 distance=0, address="", phone="", website="", opening_hours="", collection_times="",
                 parent=None, children=None, alternative_names=None, shape=""):
        self.id = id
        self.name = name
        self.type = type
        self.lat = lat
        self.lon = lon
        self.type_name = type_name
        self.identifiers = identifiers or []
        self.short_name = short_name
        self.distance = distance
        self.address = address
        self.phone = phone
        self.website = website
        self.opening_hours = opening_hours
        self.collection_times = collection_times
        self.parent = parent
        self.children = children or []
        self.alternative_names = alternative_names
        self.shape = shape
