import yaml

#TODO managed keys should come from the configuration files
managed_keys = ['name', 'location']
mergable_keys = ['identifiers', 'tags']
precedence_key = 'meta_precedence'


class ACIDException(Exception):
    pass


def prepare_document(doc, results, precedence):
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
    @return: name (singular or plural)
    """
    f = open("moxie/places/poi-types.yaml")
    data = yaml.load(f)
    f.close()
    for part in type_path.split("/"):
        data.get(part)



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
