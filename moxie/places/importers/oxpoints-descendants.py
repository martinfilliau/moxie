import logging
import json

from rdflib import Graph, URIRef
from rdflib.namespace import DC
from moxie.places.importers.rdf_namespaces import Org

logger = logging.getLogger(__name__)


UNIVERSITY_OF_OXFORD = URIRef("http://oxpoints.oucs.ox.ac.uk/id/00000000")


class OxpointsDescendantsImporter(object):

    def __init__(self, kv, oxpoints_file, rdf_media_type='text/turtle'):
        """Load the OxPoints graph and iterate through all organisations,
        adding each organisation and all descendant organisations into the
        key-value store.
        """
        self.kv = kv
        graph = Graph()
        graph.parse(oxpoints_file, format=rdf_media_type)
        self.graph = graph

    def import_data(self):
        self.import_subject(UNIVERSITY_OF_OXFORD)

    def format_descendant(self, subject):
        desc = {'id': self._get_formatted_oxpoints_id(subject)}
        title = self.graph.value(subject, DC.title)
        if title:
            desc['title'] = title.toPython()
        return desc

    def import_subject(self, subject):
        """For each sub-organisation of the ``subject`` we recursively add all
        suborganisations to a list of descendants.

        These are placed into JSON and written to the KV Store.
        """
        descendants = []
        suborgs = self.get_suborgs(subject)
        descendants.extend(map(self.format_descendant, suborgs))
        for suborg in suborgs:
            suborg_descendants = self.import_subject(suborg)
            descendants.extend(suborg_descendants)
        self.kv.set(self._get_formatted_oxpoints_id(subject), json.dumps({'descendants': descendants}))
        return descendants

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
    kv = KVService('redis://localhost:6379/12')
    importer = OxpointsDescendantsImporter(kv, ns.oxpointsfile)
    importer.import_data()


if __name__ == '__main__':
    main()
