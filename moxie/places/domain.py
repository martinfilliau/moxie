class POI(object):

    def __init__(self, id, name, lat, lon, type, type_name=None, identifiers=None, distance=0, address="", phone="",
                 website="", opening_hours="", collection_times="", parent=None, children=None):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.type = type
        self.type_name = type_name
        self.identifiers = identifiers or []
        self.distance = distance
        self.address = address
        self.phone = phone
        self.website = website
        self.opening_hours = opening_hours
        self.collection_times = collection_times
        self.parent = parent
        self.children = children or []