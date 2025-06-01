import datetime
import dateutil
from typing import Literal, TypeAlias

Span: TypeAlias = Literal['year', 'month', 'week', 'day', 'hour', 'minute', 'second']
class Moment(datetime.datetime):

    @classmethod
    def from_row(cls, row: str) -> "Moment":
        """Build Moment from YYYY-mm-dd HH:mm:ss string (returned by the db)"""
        return cls.strptime(row, "%Y-%m-%d %H:%M:%S")

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
