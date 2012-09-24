import yaml
import logging

logger = logging.getLogger(__name__)

#TODO managed keys should come from the configuration files
managed_keys = ['name', 'location']
mergable_keys = ['identifiers', 'tags']
precedence_key = 'meta_precedence'


class ACIDException(Exception):
    pass


def prepare_document(doc, results, precedence):
    """
    Prepare a document to be inserted in a datastore
    @param doc: doc to be inserted
    @param results: results of the search concerning this doc
    @param precedence: precedence to be applied depending on importers
    @return: document updated to fill
    """
    # TODO this function shouldn't be called by importers but should be part of the import process at a lower level

    # Add the "friendly" name of the type to the full-text search field
    try:
        doc['fts'] = find_type_name(doc["type"])
    except KeyError:
        logger.warning("Couldn't find name for type '{0}'.".format(doc["type"]))

    # Attempt to merge documents
    if len(results['response']['docs']) == 0:
        doc[precedence_key] = precedence
        return doc
    elif len(results['response']['docs']) == 1:
        return merge_docs(doc, results['response']['docs'][0], precedence)
    else:
        raise ACIDException()


def find_type_name(type_path, singular=True):
    """
    Find the name of the type from its path
    @param type_path: a path e.g. /transport/bus-stop
    @param singular: optional parameter whether it should be a singular or plural name
    @return: name (singular or plural) (e.g. "Bus stop")
    """
    # TODO path of yaml file has to be configurable
    data = yaml.load(open("moxie/places/poi-types.yaml"))
    to_find = type_path.split("/")[-1]
    node = find_type(data, type_path, to_find, 1)
    if singular:
        return node["name_singular"]
    else:
        return node["name_plural"]


def find_type(data, path, to_find, count):
    """
    Recursive function used by find_type_name to find a node in a tree
    @param data: dictionary to use
    @param path: path to traverse in the dictionary
    @param to_find: actual node to find
    @param count: current part of the path
    @return: dictionary
    """
    part = path.split("/")[count]
    if part == to_find:
        return data[part]
    else:
        count += 1
        if 'types' in data[part]:
            return find_type(data[part]["types"], path, to_find, count)


def merge_docs(current_doc, new_doc, new_precedence):
    """Given two documents, attempt to merge according to the precedence rules
    So if the new_precedence is greater than our existing we overwrite the
    managed keys in the updated document.

    @param new_precedence Integer proportional to the reliability of new data
    """
    new_doc = merge_keys(current_doc, new_doc, mergable_keys)
    current_precedence = current_doc.get('meta_precedence', -1)
    if new_precedence > current_precedence:
        current_doc['meta_precedence'] = new_precedence
        for key in managed_keys:
            if key in new_doc:
                current_doc[key] = new_doc[key]
    current_doc.update(new_doc)
    return current_doc


def merge_keys(current_doc, new_doc, keys):
    for key in keys:
        new_doc[key] = merge_values(
                current_doc.get(key, []), new_doc.get(key, []))
    return new_doc


def merge_values(current_vals, new_vals):
    current_vals.extend(new_vals)
    merged = list(set(current_vals))
    return merged
