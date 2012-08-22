#TODO managed keys should come from the configuration files
managed_keys = ['name', 'location']
identifiers_key = 'identifiers'
precedence_key = 'meta_precedence'


class ACIDException(Exception):
    pass


def prepare_document(doc, results, uid_func, uid_key, precedence):
    if len(results['response']['docs']) == 0:
        doc[uid_key] = uid_func()
        doc[precedence_key] = precedence
        return doc
    elif len(results['response']['docs']) == 1:
        return merge_docs(doc, results['response']['docs'][0], precedence)
    else:
        raise ACIDException()


def merge_docs(current_doc, new_doc, new_precedence):
    """Given two documents, attempt to merge according to the precedence rules
    So if the new_precedence is greater than our existing we overwrite the
    managed keys in the updated document.

    @param new_precedence Integer proportional to the reliability of new data
    """
    current_identifiers = current_doc.get(identifiers_key, [])
    new_identifiers = new_doc.get(identifiers_key, [])
    merged_idents = merge_identifiers(current_identifiers, new_identifiers)

    current_precedence = current_doc.get('meta_precedence', -1)
    if new_precedence > current_precedence:
        current_doc['meta_precedence'] = new_precedence
        for key in managed_keys:
            if key in new_doc:
                current_doc[key] = new_doc[key]
    current_doc.update(new_doc)

    current_doc[identifiers_key] = merged_idents
    return current_doc


def merge_identifiers(current_identifiers, new_identifiers):
    current_identifiers.extend(new_identifiers)
    merged_idents = list(set(current_identifiers))
    return merged_idents
