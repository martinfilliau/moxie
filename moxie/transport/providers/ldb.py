import logging
import suds
import suds.sudsobject
from suds.sax.element import Element


logger = logging.getLogger(__name__)


class LiveDepartureBoardPlacesProvider():
    _WSDL_URL = "https://realtime.nationalrail.co.uk/ldbws/wsdl.aspx"
    _ATTRIBUTION = { 'title': ("Powered by National Rail Enquiries"),
                  'url': "http://www.nationalrail.co.uk",
                  }

    def __init__(self, token, max_services=15, max_results=1):
        self._max_services = max_services
        self._max_results = max_results
        self._token = token

    def delayed(self, eta, sta, etd, std):
        """
        Try and figure out if a service is delayed based on free text values
        for estimated/scheduled times of arrival/depature
        """
        if eta in ('Delayed', 'Cancelled') or etd in ('Delayed', 'Cancelled'):
            # Easy case
            return True
        else:
            # More complex case, have to parse time stamps
            try:
                # Compare scheduled and expected arrival times
                schedh, schedm = sta.split(':')
                exph, expm = eta.rstrip('*').split(':')
            except ValueError:
                pass
            else:
                # Minutes since midnight, as we can't compare time objects
                sched_msm = int(schedh) * 60 + int(schedm)
                exp_msm = int(exph) * 60 + int(expm)
                
                if exp_msm < sched_msm:
                    # Deal with wraparound at midnight
                    sched_msm += 1440
                
                if exp_msm - sched_msm >= 5:
                    # 5 minute delay
                    return True
            
            try:
                # Compare scheduled and expected departure times
                schedh, schedm = std.split(':')
                exph, expm = etd.rstrip('*').split(':')
            except ValueError:
                pass
            else:
                # Minutes since midnight, as we can't compare time objects
                sched_msm = int(schedh) * 60 + int(schedm)
                exp_msm = int(exph) * 60 + int(expm)
                
                if exp_msm < sched_msm:
                    # Deal with wraparound at midnight
                    sched_msm += 1440
                
                if exp_msm - sched_msm >= 5:
                    # 5 minute delay
                    return True
            
            return False

    def augment_metadata(self, entities, board='departures', **kwargs):
        station_entities = []
        for entity in entities:
            if not entity.get('crs'):
                continue
            station_entities.append(entity)

        station_entities = station_entities[:self._max_results]
        if not station_entities:
            return
        
        try:
            ldb = suds.client.Client(self._WSDL_URL, soapheaders=Element('AccessToken').insert(Element('TokenValue').setText(self._token)))
        except Exception, e:
            logger.warning("Could not instantiate suds client for live departure board.", exc_info=True, extra={'wsdl_url': self._WSDL_URL})
            self._add_error(station_entities)
            return
        
        for entity in station_entities:
            try:
                if board == 'arrivals':
                    db = ldb.service.GetArrivalBoard(self._max_services, entity['crs'])
                else:
                    db = ldb.service.GetDepartureBoard(self._max_services, entity['crs'])
                db = self.transform_suds(db)
                import pprint
                pprint.pprint(db)
                entity['ldb'] = db
                entity['service_details'] = lambda s: self.service_details(s, entity)
                entity['ldb_service'] = lambda s: self.transform_suds(ldb.service.GetServiceDetails(s))
                entity['service_type'] = 'ldb'
                
                # Show bus services too
                if board == 'arrivals':
                    db = self.transform_suds(
                        ldb.service.GetDepartureBoard(self._max_services,
                                                     entity['crs']))
                
                if 'trainServices' in db:
                    for service in db['trainServices']['service']:
                        service['problems'] = self.delayed(
                            service.get('eta', ''), service.get('sta', ''),
                            service.get('etd', ''), service.get('std', ''))

                if 'busServices' in db:
                    for service in db['busServices']['service']:
                        entity['real_time_information'] = {
                            'services':
                                [{
                                    'service': 'BUS',
                                    'destination': service['destination']['location'][0]['locationName'],
                                    'next': service['std'],
                                    'following': [],
                                }]
                        }
                
            except Exception, e:
                raise e
                logger.warning("Could not retrieve departure board for station: %r", entity.get('crs'),
                               exc_info=True)
                self._add_error((entity,))
            entity['meta_refresh'] = 60
    
    def service_details(self, service, entity):
        try:
            service = entity['ldb_service'](service)
        except suds.WebFault as f:
            if f.fault['faultstring'] == 'Unexpected server error: Invalid length for a Base-64 char array.':
                raise Http404
            else:
                return({'error': f.fault['faultstring']})
        if service is None:
            return None
        
        # Trains can split and join, which makes figuring out the list of
        # calling points a bit difficult. The LiveDepartureBoards documentation
        # details how these should be handled. First, we build a list of all
        # the calling points on the "through" train.
        calling_points = service['previousCallingPoints']['callingPointList'][0]['callingPoint'] if len(service['previousCallingPoints']) else []

        # Then attach joining services to our thorough route in the correct
        # point, but only if there is a list of previous calling points
        if len(service['previousCallingPoints']):
            for i, points in enumerate(service['previousCallingPoints']['callingPointList'][1:]):
                # If the other half of the split ends up here, it's not a split, but
                # a change between rail replacement bus of train
                for j, point in enumerate(calling_points):
                    if points['callingPoint'][-1]['crs'] == point['crs']:
                        if j > 0:
                            point['joining'] = points['callingPoint']
                        else:
                            point['service_change'] = service['previousCallingPoints']['callingPointList'][i]['_serviceType']
                            calling_points = points['callingPoint'] + calling_points
                            break
        
        # Add our current station
        calling_points += [{
            'locationName': service['locationName'],
            'crs': service['crs'],
            'st': service['std'] if 'std' in service else service['sta'],
            'et': service['etd'] if 'etd' in service else service['eta'] if 'eta' in service else '',
            'at': service['atd'] if 'atd' in service else '',
        }]
        
        if len(service['subsequentCallingPoints']):
            if service['serviceType'] != service['subsequentCallingPoints']['callingPointList'][0]['_serviceType']:
                calling_points[-1]['service_change'] = (service['subsequentCallingPoints']['callingPointList'][0]['_serviceType'])
        
        if len(service['previousCallingPoints']):
            if service['serviceType'] != service['previousCallingPoints']['callingPointList'][0]['_serviceType']:
                calling_points[-1]['service_change'] = (service['serviceType'])
        
        # Now add services going forward
        if len(service['subsequentCallingPoints']):
            calling_points += service['subsequentCallingPoints']['callingPointList'][0]['callingPoint']
        
        # And do the same with splitting services
        if len(service['subsequentCallingPoints']):
            for i, points in enumerate(service['subsequentCallingPoints']['callingPointList'][1:]):
                # Now we have to handle changes between trains and rail replacement services
                if service['subsequentCallingPoints']['callingPointList'][i]['callingPoint'][-1]['crs'] == points['callingPoint'][0]['crs']:
                    calling_points += points['callingPoint']
                    points['callingPoint'][0]['service_change'] = (points['_serviceType'])
                else:
                    for point in calling_points:
                        if points['callingPoint'][0]['crs'] == point['crs']:
                            point['splitting'] = {'destination': points['callingPoint'][-1]['locationName'], 'list': points['callingPoint']}
            
        sources = [calling_points[0]['locationName']]
        for point in calling_points:
            if 'joining' in point:
                sources.append(point['joining'][0]['locationName'])
        
        destinations = [calling_points[-1]['locationName']]
        for point in calling_points:
            if 'splitting' in point:
                destinations.append(point['splitting']['destination'])

        if 'std' in service:
            title = service['std'] + ' ' + service['locationName'] + ' to ' + ' and '.join(destinations)
        else:
            # This service arrives here
            title = service['sta'] + ' from ' + ' and '.join(sources)
        messages = service.get('adhocAlerts', [])
        if 'disruptionReason' in service:
            messages.append(service['disruptionReason'])
        if 'overdueMessage' in service:
            messages.append(service['overdueMessage'])
        return {
            'title': title,
            'ldb': service,
            'calling_points': calling_points,
            'has_timetable': True,
            'has_realtime': True,
            'operator': service.get('operator'),
            'platform': service.get('platform'),
            'messages': messages
        }

    def transform_suds(self, o):
        if isinstance(o, suds.sudsobject.Object):
            return dict((k, self.transform_suds(v)) for k,v in o)
        elif isinstance(o, list):
            return map(self.transform_suds, o)
        else:
            return o

    def _add_error(self, entities):
        for entity in entities:
            entity['ldb'] = {'error': True}

if __name__=='__main__':
    provider = LiveDepartureBoardPlacesProvider('REDACTED', 10)
    entities = [{'crs': 'OXF'}]
    provider.augment_metadata(entities)
