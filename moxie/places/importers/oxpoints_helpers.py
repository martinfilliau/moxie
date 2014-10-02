import logging
from rdflib.namespace import RDF

from moxie.places.importers.rdf_namespaces import (Geo, OxPoints, Org, SpatialRelations,
                                                   Geometry)
from shapely.wkt import loads as wkt_loads

logger = logging.getLogger(__name__)


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
        depth += 1
        if (subject, Geo.lat, None) in graph and (subject, Geo.long, None) in graph:
            lat = graph.value(subject, Geo.lat).toPython()
            lon = graph.value(subject, Geo.long).toPython()
            return lat, lon
        elif (subject, OxPoints.primaryPlace, None) in graph:
            place = graph.value(subject, OxPoints.primaryPlace)
            return find_location(graph, place, depth=depth)
        elif (subject, SpatialRelations.within, None) in graph:
            within = graph.value(subject, SpatialRelations.within)
            return find_location(graph, within, depth=depth)
        elif (subject, Org.subOrganizationOf, None) in graph:
            org = graph.value(subject, Org.subOrganizationOf)
            return find_location(graph, org, depth=depth)
    return None


def find_shape(graph, subject, depth=1, max_depth=10):
    """Find shape for a given subject
    :param graph: graph to browse
    :param subject: subject to be used
    :param depth: actual depth
    :param max_depth: maximum depth
    :return string or None
    """
    if depth <= max_depth:
        depth += 1
        shape = graph.value(subject, Geometry.extent)
        if shape:
            wkt = graph.value(shape, Geometry.asWKT)
            if wkt:
                wkt = wkt.toPython()
                try:
                    # make sure that it is a correct WKT shape
                    result = wkt_loads(wkt)
                    if not result:
                        raise ValueError("No WKT shape")
                    return wkt
                except:
                    print "zut"
                    logger.warning("Unable to detect a valid WKT shape", exc_info=True, extra={
                        'data': {
                            'oxpoints_subject': subject.toPython()
                        }
                    })
                    return None

        # if we're at a Building level, do not try to go further
        current_type = graph.value(subject, RDF.type)
        if current_type and current_type == OxPoints.Building:
            return None

        # find shape from parent container
        if (subject, OxPoints.primaryPlace, None) in graph:
            place = graph.value(subject, OxPoints.primaryPlace)
            return find_shape(graph, place, depth=depth)
        elif (subject, SpatialRelations.within, None) in graph:
            within = graph.value(subject, SpatialRelations.within)
            return find_shape(graph, within, depth=depth)
        elif (subject, Org.subOrganizationOf, None) in graph:
            org = graph.value(subject, Org.subOrganizationOf)
            return find_shape(graph, org, depth=depth)
    return None
