import datetime
import dateutil
import re
from typing import Literal, TypeAlias

Span: TypeAlias = Literal['year', 'month', 'week', 'day', 'hour', 'minute', 'second']
# Regex of supported formats, by their name and with their complement for a full date
MOMENT_REGEXES: dict[str, tuple[re.Pattern, str]] = dict(
    full=(re.compile(r'\d{4}-\d{2}-\d{2}[ _]\d{2}:\d{2}:\d{2}'),
          lambda moment: moment),
    date=(re.compile(r'\d{4}-\d{2}-\d{2}'),
          lambda moment: f'{moment} 00:00:00'),
    date_short=(re.compile(r'\d{2}-\d{2}'),
                lambda moment: f'{datetime.date.today().year}-{moment} 00:00:00'),
    hour=(re.compile(r'\d{2}:\d{2}:\d{2}'),
          lambda moment: f'{datetime.date.today().strftime('%F')} {moment}'),
    hour_short=(re.compile(r'\d{2}:\d{2}'),
                lambda moment: f'{datetime.date.today().strftime('%F')} {moment}:00'),
    hour_offset=(re.compile(r'-\d{2}:\d{2}'),
                 lambda moment: (datetime.datetime.now() - dateutil.relativedelta.relativedelta(hours=int(moment[1:3]), minutes=int(moment[4:]))).strftime("%F %T")),
    minute_offset=(re.compile(r'-\d{1,2}'),
                   lambda moment: (datetime.datetime.now() - dateutil.relativedelta.relativedelta(minutes=int(moment[1:]))).strftime("%F %T")),
)
class Moment(datetime.datetime):

    @classmethod
    def from_string(cls, row: str) -> "Moment":
        """Build Moment from a string, as returned by the db or given as a flag.
        Supported formats:
        - YYYY-MM-DD hh:mm:ss
        - YYYY-MM-DD (implies 00:00:00)
        - MM-DD (implies current year and 00:00:00)
        - hh:mm:ss (implies today)
        - hh:mm (implies today, 00 seconds)
        - -hh:mm (implies today, 00 seconds, offset from now)
        - -mm (implies today, offset from now)
        """
        for type, (pattern, builder) in MOMENT_REGEXES.items():
            if pattern.match(row):
                return cls.strptime(builder(row), "%Y-%m-%d %H:%M:%S")

    def __str__(self) -> str:
        return self.strftime("%F %T")

    def _offset(self, span: Span, offset: int) -> "Moment":
        if span == "week":
            span = "day"
            offset *= 7

        kwarg = {
            f"{span}s": offset
        }
        return self + dateutil.relativedelta.relativedelta(**kwarg)

    def next(self, span: Span) -> "Moment":
        """Return the moment that comes one "span" (minute, day, year, ...) after itself"""
        return self._offset(span, 1)

    def prev(self, span: Span) -> "Moment":
        """Return the moment that comes one "span" (minute, day, year, ...) before itself"""
        return self._offset(span, -1)

    def week_start(self):
        """Returns the moment at the last monday"""
        return self + dateutil.relativedelta.relativedelta(weekday=dateutil.relativedelta.MO(-1))

    def range(self,  span: Span) -> tuple["Moment", "Moment"]:
        """Returns two Moments separated by a given duration.
        For instance, a span of "month" goes from the beginning of the month,
        to the the end of it.

        :param span: Duration by which the Moments are separated
        :return: Start and end moment
        """
        reset_kwargs = {
            'year': self.year,
            'month': 1,
            'day': 1,
            'hour': 0,
            'minute': 0,
            'second': 0,
            'microsecond': 0,
        }
        # Relies on the ordering of the keys. Removes all spans bigger than the
        # range
        for key in list(reset_kwargs.keys()):
            reset_kwargs.pop(key)
            if key == span or key == 'hour' and span == 'week':
                break

        if span == 'week':
            reset_kwargs['weekday'] = dateutil.relativedelta.MO(-1)

        start = self + dateutil.relativedelta.relativedelta(**reset_kwargs)
        end = start.next(span)
        return (start, end)
