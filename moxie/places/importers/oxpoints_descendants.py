import logging
import json

from rdflib import Graph, URIRef
from rdflib.namespace import DC

logger = logging.getLogger(__name__)


UNIVERSITY_OF_OXFORD = URIRef("http://oxpoints.oucs.ox.ac.uk/id/00000000")


class OxpointsDescendantsImporter(object):

    def __init__(self, kv, oxpoints_file, relation, rdf_media_type='text/turtle'):
        """From a given start point follow all edges through the specified ``relation``
        and collect a set of all descendants recursively.

        :param kv: key-value store
        :param oxpoints_file: path to the oxpoints representation
        :param relation: the predicate we are following through the graph
        :param rdf_media_type: file format of oxpoints_file
        """
        self.kv = kv
        self.relation = relation
        graph = Graph()
        graph.parse(oxpoints_file, format=rdf_media_type)
        self.graph = graph

    def import_data(self):
        """Import all of oxpoints by starting with the University itself
        """
        self.import_subject(UNIVERSITY_OF_OXFORD)

    def format_descendant(self, subject):
        desc = {'id': self._get_formatted_oxpoints_id(subject)}
        title = self.graph.value(subject, DC.title)
        if title:
            desc['title'] = title.toPython()
        return desc

    def import_subject(self, subject):
        """For each object following the ``self.relation`` predicate of the
        ``subject`` we recursively add all objects to a list of descendants.

        These are placed into JSON and written to the KV Store.
        """
        descendants = []
        children = self.get_children(subject)
        descendants.extend(map(self.format_descendant, children))
        for child in children:
            child_descendants = self.import_subject(child)
            descendants.extend(child_descendants)
        self.kv.set(self._get_formatted_oxpoints_id(subject), json.dumps({'descendants': descendants}))
        return descendants

    def get_children(self, subject):
        return [triple[0] for triple in self.graph.triples((None, self.relation, subject))]

    def _get_formatted_oxpoints_id(self, uri_ref, separator=':'):
        """Split an URI to get the OxPoints ID
        :param uri_ref: URIRef object
        :return string representing oxpoints ID
        """
        return 'oxpoints{separator}{ident}'.format(separator=separator,
                                                   ident=uri_ref.toPython().rsplit('/')[-1])

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('oxpointsfile', type=argparse.FileType('r'))
    ns = parser.parse_args()
    from moxie.core.kv import KVService
    from moxie.places.importers.rdf_namespaces import Org
    kv = KVService('redis://localhost:6379/12')
    importer = OxpointsDescendantsImporter(kv, ns.oxpointsfile, Org.subOrganizationOf)
    importer.import_data()


if __name__ == '__main__':
    main()
