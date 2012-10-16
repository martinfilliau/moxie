from moxie.core.views import ServiceView
from .services import OxfordDatesService


class OxfordDateToday(ServiceView):
    """View that exposes today's date
    """

    def handle_request(self):
        dates_service = OxfordDatesService.from_context()
        response = {
            'today': dates_service.get_today_date()
        }
        return response