from flask import Blueprint, current_app

from .views import Search, PoiDetail, BusRti

from moxie.transport.service import TransportService
from moxie.transport.providers.cloudamber import CloudAmberBusRtiProvider

places = Blueprint('places', __name__)


rti_providers = [CloudAmberBusRtiProvider(current_app.config['BUS_RTI_URL'])]
rti_service = TransportService(providers=rti_providers)

# URL Rules
places.add_url_rule('/search', view_func=Search.as_view('search'))
places.add_url_rule('/<path:id>', view_func=PoiDetail.as_view('poidetail'))
places.add_url_rule('/<path:id>/rti', view_func=BusRti.as_view('busrti',
    service=rti_service))
