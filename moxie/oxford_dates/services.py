import oxford_term_dates

from moxie.core.service import Service


class OxfordDatesService(Service):

    def get_today_date(self):
        return oxford_term_dates.format_today()