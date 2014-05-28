import logging
import json

from rdflib import Graph, URIRef
from moxie.places.importers.rdf_namespaces import Org

logger = logging.getLogger(__name__)


UNIVERSITY_OF_OXFORD = URIRef("http://oxpoints.oucs.ox.ac.uk/id/00000000")


class OxpointsDescendantsImporter(object):

    def __init__(self, kv, oxpoints_file):
        self.kv = kv
        graph = Graph()
        graph.parse(oxpoints_file)
        self.graph = graph

    def import_data(self):
        self.import_subject(UNIVERSITY_OF_OXFORD)

    def import_subject(self, subject):
        uris = set()
        suborgs = self.get_suborgs(subject)
        uris.update(map(self._get_formatted_oxpoints_id, suborgs))
        for suborg in suborgs:
            suborg_uris = self.import_subject(suborg)
            uris.update(suborg_uris)
        print ("%s: %s" % (subject, uris))
        return uris

    def get_suborgs(self, subject):
        return [triple[0] for triple in self.graph.triples((None, Org.subOrganizationOf, subject))]

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
    kv = KVService('redis://localhost:6379/5')
    importer = OxpointsDescendantsImporter(kv, ns.oxpointsfile)
    importer.import_data()


if __name__ == '__main__':
    main()
