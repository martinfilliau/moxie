import unittest

from mock import Mock
from xml.sax import parse, parseString

from moxie.core.search.solr import SolrSearch
from moxie.places.importers.naptan import NaptanXMLHandler, NaPTANImporter


test_stop_areas = """
        <NaPTAN>
            <StopArea CreationDateTime="2003-01-10T00:00:00" ModificationDateTime="2003-01-10T00:00:00" Modification="new" RevisionNumber="0" Status="active">
                <StopAreaCode>639GSHI20121</StopAreaCode>
                <Name>Bullers of Buchan</Name>
                <Location>
                    <Translation>
                        <Longitude>-1.8240700289</Longitude>
                        <Latitude>57.4328198507</Latitude>
                    </Translation>
                </Location>
            </StopArea>
            <StopArea CreationDateTime="2003-01-10T00:00:00" ModificationDateTime="2003-01-10T00:00:00" Modification="new" RevisionNumber="0" Status="active">
                <StopAreaCode>639GSHI21580</StopAreaCode>
                <ParentStopAreaRef Modification="new" Status="inactive">639GSHI20121</ParentStopAreaRef>
                <Name>Old Market Street</Name>
                <Location>
                    <Translation>
                        <Longitude>-2.4932405666</Longitude>
                        <Latitude>57.6708309449</Latitude>
                    </Translation>
                </Location>
            </StopArea>
            <StopArea CreationDateTime="2003-01-10T00:00:00" ModificationDateTime="2003-01-10T00:00:00" Modification="new" RevisionNumber="0" Status="active">
                <StopAreaCode>639GSHI21581</StopAreaCode>
                <ParentStopAreaRef Modification="new" Status="active">639GSHI20121</ParentStopAreaRef>
                <Name>Market Street</Name>
                <Location>
                    <Translation>
                        <Longitude>-2.4932405666</Longitude>
                        <Latitude>57.6708309449</Latitude>
                    </Translation>
                </Location>
            </StopArea>
            <StopPoint CreationDateTime="2003-07-15T00:00:00" ModificationDateTime="2011-10-12T14:10:00" Modification="revise" RevisionNumber="2" Status="active">
                <AtcoCode>639000022</AtcoCode>
                <NaptanCode>23234369</NaptanCode>
                <Descriptor>
                    <CommonName>Albyn Grove</CommonName>
                </Descriptor>
                <Place>
                    <Location>
                        <Translation>
                            <Longitude>-2.1189893199</Longitude>
                            <Latitude>57.1409815049</Latitude>
                        </Translation>
                    </Location>
                </Place>
                <StopAreas>
                    <StopAreaRef CreationDateTime="2009-10-29T00:00:00" ModificationDateTime="2009-10-29T00:00:00" Modification="revise" RevisionNumber="0" Status="active">639GSHI21581</StopAreaRef>
                </StopAreas>
            </StopPoint>
        </NaPTAN>
        """


class NaptanTestCase(unittest.TestCase):

    def setUp(self):
        self.naptan_file = 'moxie/tests/data/naptan.xml'
        self.mock_solr = Mock(spec=SolrSearch)
        self.mock_solr.search_for_ids.return_value.json = {'response': {'docs': []}}

    def test_finds_all_stops(self):
        xml_handler = NaptanXMLHandler(['639'], 'identifiers')
        parse(open(self.naptan_file), xml_handler)
        self.assertEqual(len(xml_handler.stop_points), 5)

    def test_finds_all_stop_areas(self):
        xml_handler = NaptanXMLHandler(['639'], 'identifiers')
        parse(open(self.naptan_file), xml_handler)
        self.assertEqual(len(xml_handler.stop_areas), 6)

    def test_finds_no_stops_in_different_location(self):
        xml_handler = NaptanXMLHandler(['123'], 'identifiers')
        parse(open(self.naptan_file), xml_handler)
        self.assertEqual(len(xml_handler.stop_points), 0)
        self.assertEqual(len(xml_handler.stop_areas), 0)

    def test_search_called_each_result(self):
        naptan_importer = NaPTANImporter(self.mock_solr, 10, file(self.naptan_file), ['639'], 'identifiers')
        naptan_importer.run()
        self.assertEqual(self.mock_solr.search_for_ids.call_count,
                len(naptan_importer.handler.stop_points)+len(naptan_importer.handler.stop_areas))

    def test_parent_child_stop_areas(self):
        xml_handler = NaptanXMLHandler(['639'], 'identifiers')
        parseString(test_stop_areas, xml_handler)
        areas = xml_handler.annotate_stop_area_ancestry(xml_handler.stop_areas)
        self.assertEqual(areas['639GSHI21581']['child_of'][0], areas['639GSHI20121']['id'])
        self.assertEqual(areas['639GSHI20121']['parent_of'][0], areas['639GSHI21581']['id'])

    def test_parent_child_stop_areas_inactive(self):
        xml_handler = NaptanXMLHandler(['639'], 'identifiers')
        parseString(test_stop_areas, xml_handler)
        areas = xml_handler.annotate_stop_area_ancestry(xml_handler.stop_areas)
        with self.assertRaises(KeyError):
            self.assertEqual(areas['639GSHI21580']['child_of'][0], areas['639GSHI20121']['id'])

    def test_parent_child_stop_point(self):
        xml_handler = NaptanXMLHandler(['639'], 'identifiers')
        parseString(test_stop_areas, xml_handler)
        areas = xml_handler.annotate_stop_area_ancestry(xml_handler.stop_areas)
        points, areas = xml_handler.annotate_stop_point_ancestry(xml_handler.stop_points, areas)
        self.assertEqual(points['639000022']['child_of'][0], areas['639GSHI21581']['id'])
        self.assertEqual(areas['639GSHI21581']['parent_of'][0], points['639000022']['id'])
