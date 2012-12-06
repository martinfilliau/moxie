from moxie.places.domain import POI


def doc_to_poi(doc):
    """Transforms a document from Solr as a POI.
    :param doc: document from Solr
    :return POI object
    """
    lon, lat = doc['location'].split(',')
    poi = POI(doc['id'], doc['name'], lat, lon, doc['type'])
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
    return poi