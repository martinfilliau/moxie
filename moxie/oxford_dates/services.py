import oxford_term_dates

from moxie.core.service import Service


class OxfordDatesService(Service):
    """Service to provide various methods to access dates particular to University of Oxford,
    such as term dates.
    """

    def get_today_date(self):
        """Returns today's date with the name of the term.
        """
        return oxford_term_dates.format_today()