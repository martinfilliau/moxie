import json

from moxie.places.domain import POI, File

# fields specific to Solr that should be ignored
SOLR_IGNORE_FIELDS = ['_version_', '_dist_', '_accessibility_has_access_guide_information',
                      '_is_display_in_maps_department_list']


def doc_to_poi(doc, fields_key="_"):
    """Transforms a document from Solr as a POI.
    :param doc: document from Solr
    :return POI object
    """
    poi = POI(doc['id'], doc['name'], doc['type'])
    if 'location' in doc:
        lat, lon = doc['location'].split(',')
        poi.lon = lon
        poi.lat = lat
    poi.type_name = doc.get('type_name', None)
    poi.type = doc.get('type', None)
    poi.identifiers = doc.get('identifiers', [])
    poi.short_name = doc.get('short_name', None)
    poi.name_sort = doc.get('name_sort', None)
    poi.distance = doc.get('_dist_', 0)
    poi.address = doc.get('address', "")
    poi.phone = doc.get('phone', "")
    poi.website = doc.get('website', "")
    poi.opening_hours = doc.get('opening_hours', "")
    poi.collection_times = doc.get('collection_times', "")
    if 'parent_of' in doc:
        poi.children = doc['parent_of']
    if 'child_of' in doc:
        poi.parent = doc['child_of']
    if 'alternative_names' in doc:
        poi.alternative_names = doc['alternative_names']
    if 'shape' in doc:
        poi.shape = doc['shape']
    if 'files' in doc:
        for fileJSON in doc['files']:
            fileData = json.loads(fileJSON)
            poi.files.append(File(**fileData))
    if 'primary_place' in doc:
        poi.primary_place = doc['primary_place']
    for key, val in doc.items():
        if key.startswith(fields_key) and key not in SOLR_IGNORE_FIELDS:
            if not getattr(poi, 'fields', False):
                poi.fields = {}
            poi.fields[key.replace(fields_key, '', 1)] = val
    return poi
