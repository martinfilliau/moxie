import oxford_term_dates

from moxie.core.views import ServiceView

class OxfordDateToday(ServiceView):

    def handle_request(self):
        response = {
            'today': oxford_term_dates.format_today()
        }
        return response