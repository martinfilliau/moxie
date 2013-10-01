import yaml
import logging
import os

from flask import _app_ctx_stack
from werkzeug.local import LocalProxy

from moxie.places.importers.loaders import OrderedDictYAMLLoader


logger = logging.getLogger(__name__)

#TODO managed keys should come from the configuration files
MANAGED_KEYS = ['name', 'location']
MERGABLE_KEYS = ['identifiers', 'tags']
PRECEDENCE_KEY = 'meta_precedence'


class ACIDException(Exception):
    pass


def get_types_dict():
    ctx = _app_ctx_stack.top
    types = getattr(ctx, 'places_types', None)
    if types is None:
        types = yaml.load(open(os.path.join(os.path.dirname(__file__), '..', 'poi-types.yaml')), OrderedDictYAMLLoader)
        ctx.places_types = types
    return types
types = LocalProxy(get_types_dict)


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
        doc['type_name'] = find_type_name(doc["type"])
    except KeyError:
        logger.warning("Couldn't find name for type '{0}'.".format(doc["type"]))

    # Attempt to merge documents
    if len(results.results) == 0:
        doc[PRECEDENCE_KEY] = precedence
        return doc
    elif len(results.results) == 1:
        return merge_docs(doc, results.results[0], precedence)
    else:
        raise ACIDException()


def find_type_name(type_path, singular=True):
    """
    Find the name of the type from its path
    @param type_path: a path e.g. /transport/bus-stop
    @param singular: optional parameter whether it should be a singular or plural name
    @return: name (singular or plural) (e.g. "Bus stop")
    """
    to_find = type_path.split("/")[-1]
    node = find_type(types, type_path, to_find, 1)
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
    new_doc = merge_keys(current_doc, new_doc, MERGABLE_KEYS)
    current_precedence = current_doc.get('meta_precedence', -1)
    if new_precedence > current_precedence:
        current_doc['meta_precedence'] = new_precedence
        for key in MANAGED_KEYS:
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


def format_uk_telephone(value):
    """
    Formats UK telephone numbers to E.123 format (national notation)

    University number ranges are also formatted according to internal guidelines
    """

    # Normalise a number
    value = value.replace("(0)", "").replace(" ", "").replace("-", "")
    if value.startswith("0"):
        value = "+44" + value[1:]
    normalised = value

    # Convert UK numbers into national format
    if value.startswith("+44"):
        value = "0" + value[3:]

    # Now apply rules on how to split up area codes
    if value[:8] in ('01332050', '01382006'):
        # Direct dial only
        value = value[:5] + " " + value[5:]
    elif value[:7] in ('0141005', '0117101') or value[:6] in ('011800',):
        # Direct dial only
        value = value[:4] + " " + value[4:7] + " " + value[7:]
    elif value[:7] in ('0200003',):
        # Direct dial only
        value = value[:3] + " " + value[3:7] + " " + value[7:]
    elif value.startswith('01'):
        if value[2] == '1' or value[3] == '1':
            # 4 digit area codes
            area_code = value[:4]
            local_part =  value[4:7] + " " + value[7:]
        elif value[:6] in (
            '013873', # Langholm
            '015242', # Hornby
            '015394', # Hawkshead
            '015395', # Grange-over-Sands
            '015396', # Sedbergh
            '016973', # Wigton
            '016974', # Raughton Head
            '016977', # Brampton
            '017683', # Appleby
            '017684', # Pooley Bridge
            '017687', # Keswick
            '019467', # Gosforth
            ):
            # 6 digit area codes
            area_code = value[:4] + " " + value[4:6]
            local_part = value[6:]
        else:
            # 5 digit
            area_code = value[:5]
            local_part = value[5:]

        value = "(%s) %s" % (area_code, local_part)

    elif value.startswith('02'):
        # 3 digit area codes
        value = "(%s) %s %s" % (value[:3], value[3:7], value[7:])

    elif value.startswith('0500') or value.startswith('0800'):
        # direct dial - 4 digit prefix, short following
        value = "%s %s" % (value[:4], value[4:])

    elif value.startswith('03') or value.startswith('08') or value.startswith('09'):
        # direct dial - 4 digit prefix
        value = "%s %s %s" % (value[:4], value[4:7], value[7:])

    elif value.startswith('05') or value.startswith('070'):
        # direct dial - 3 digit prefix
        value = "%s %s %s" % (value[:3], value[3:7], value[7:])

    elif value.startswith('07'):
        # direct dial - 5 digit prefix, short following
        value = "%s %s" % (value[:5], value[5:])

    # Now apply University rules:
    if value[:10] in ('(01865) 27', '(01865) 28', '(01865) 43', '(01865) 61'):
        # Oxford - list of internal number prefixes here:
        # http://www.oucs.ox.ac.uk/telecom/directories/intdiraccess.xml
        value = "(01865 " + value[8] + ")" + value[9:]

    return value