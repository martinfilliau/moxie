from moxie.places.importers.rdf_namespaces import Geo, OxPoints, Org


def find_location(graph, subject):
    """
    Find Geo.lat and Geo.lon for a given subject
    Will browse the graph until it finds it
    :param graph: graph to browse
    :param subject: subject to search
    :return tuple (lat, lon) or None
    """
    if (subject, Geo.lat, None) in graph and (subject, Geo.long, None) in graph:
        lat = graph.value(subject, Geo.lat).toPython()
        lon = graph.value(subject, Geo.long).toPython()
        return lat, lon
    elif (subject, Org.subOrganizationOf, None) in graph:
        org = graph.value(subject, Org.subOrganizationOf)
        return find_location(graph, org)
    elif (subject, OxPoints.primaryPlace, None) in graph:
        place = graph.value(subject, OxPoints.primaryPlace)
        return find_location(graph, place)
    else:
        return None