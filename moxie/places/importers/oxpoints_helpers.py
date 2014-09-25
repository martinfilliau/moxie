from moxie.places.importers.rdf_namespaces import Geo, OxPoints, Org, SpatialRelations


def find_location(graph, subject, depth=1, max_depth=10):
    """Find Geo.lat and Geo.lon for a given subject
    Will browse the graph until it finds it
    Prevent "infinite" recursion
    :param graph: graph to browse
    :param subject: subject to search
    :param depth: actual depth
    :param max_depth: maximum depth
    :return tuple (lat, lon) or None
    """
    if depth <= max_depth:
        if (subject, Geo.lat, None) in graph and (subject, Geo.long, None) in graph:
            lat = graph.value(subject, Geo.lat).toPython()
            lon = graph.value(subject, Geo.long).toPython()
            return lat, lon
        elif (subject, Org.subOrganizationOf, None) in graph:
            org = graph.value(subject, Org.subOrganizationOf)
            depth += 1
            return find_location(graph, org, depth=depth)
        elif (subject, OxPoints.primaryPlace, None) in graph:
            place = graph.value(subject, OxPoints.primaryPlace)
            depth += 1
            return find_location(graph, place, depth=depth)
        elif (subject, SpatialRelations.within, None) in graph:
            within = graph.value(subject, SpatialRelations.within)
            depth += 1
            return find_location(graph, within, depth=depth)
    return None
