from moxie.places.domain import POI


def doc_to_poi(doc, meta_key="meta_"):
    """Transforms a document from Solr as a POI.
    :param doc: document from Solr
    :return POI object
    """
    poi = POI(doc['id'], doc['name'], doc['type'])
    if 'location' in doc:
        lon, lat = doc['location'].split(',')
        poi.lon = lon
        poi.lat = lat
    poi.type_name = doc.get('type_name', None)
    poi.identifiers = doc.get('identifiers', [])
    poi.distance = doc.get('_dist_', 0)
    poi.address = doc.get('address', "")
    poi.phone = doc.get('phone', "")
    poi.website = doc.get('website', "")
    poi.opening_hours = doc.get('opening_hours', "")
    poi.collection_times = doc.get('collection_times', "")
    if 'parent_of' in doc:
        poi.children = doc['parent_of']
    if 'child_of' in doc:
        poi.parent = doc['child_of'][0]
    if 'alternative_names' in doc:
        poi.alternative_names = doc['alternative_names']
    poi.meta = {}
    for key, val in doc.items():
        if key.startswith(meta_key):
            poi.meta[key.replace(meta_key, '')] = val
    return poi