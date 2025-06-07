from collections import defaultdict
from typing import Literal
from orm import Database, FancyRow, Table
from config import config
from time_util import Moment, Span

def filter(*args, _filter=filter, **kwargs):
    return list(_filter(*args, **kwargs))

def sec_to_hms(seconds: int, round_seconds=False) -> str:
    seconds = int(seconds)
    if seconds:
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
    else:
        hours = minutes = seconds = 0

    if round_seconds:
        if seconds >= 30:
            minutes += 1
            seconds = 0
        return f"{hours:02}:{minutes:02}"
    else:
        return f"{hours:02}:{minutes:02}:{seconds:02}"

class RecordTable(Table):

    def _post_refresh(self):
        if self.default_sort:
            self.values.sort(key=lambda x: x[self.default_sort])

    def add_entry(
        self,
        moment=None,
        activity=None,
        comment=None
    ):
        if not moment:
            moment = Moment.now()
        print(f"\x1b[1mMoment\x1b[m: {moment}")
        if not activity:
            activity = input("\x1b[1mActivity\x1b[m: ")
        if not comment:
            comment = input("\x1b[1mComment\x1b[m: ")

        self.add([str(moment), activity, comment])
        self.flush()
        # self.parent['activity'].refresh_vals()

    def filter_by_date(self, moment: Moment, span: Span, values: list[dict] | None = None) -> list[dict]:
        """Returns entries encompassing the given span around the given moment"""
        if values is None:
            values = self.values

        start, end = map(lambda x: str(x), moment.range(span))
        return filter(lambda val: start <= val['moment'] < end , values)


    def get_current(self, span: Span) -> list[list]:
        """Returns current entries encompassing the given span"""
        return self.filter_by_date(Moment.now(), span)

    def group_by_activity(self, span=None, moment=None, with_length=False, exclude_stop=True):
        """Regroups activity filtered around a span for a given moment by
        their activity.
        :param span: Timespan around the moment for which to filter. No filtering
        if None
        :param moment: Moment around which to apply the timespan. Now if None
        :param with_length: Compute length of the rows beforehand
        """
        values = self.compute_length() if with_length else self.values
        if moment is None:
            moment = Moment.now()
        entries = self.filter_by_date(moment, span, values) if span else values

        rows_map = defaultdict(list)
        for row in entries:
            rows_map[row['activity']].append(row)

        if exclude_stop:
            rows_map.pop('stop', None)

        return dict(rows_map)

    def time_by_activity(self, span=None, moment=None, exclude_stop=True) -> dict:
        """Compute total time spent on an activity, for a filtered subset of all
        values, according to span and moment.
        :param span: Span of values to consider
        :param moment: Moment around which to consider the span
        :param exclude_stop: Whether to include the "stop" activity or not

        :return: Mapping of activities and the time spent on them, ordered
        by least to most time spent
        """
        aggregate = self.group_by_activity(span=span, moment=moment, with_length=True, exclude_stop=exclude_stop)
        sorted_sums = sorted([(activity, sum(row[-1] for row in rows)) for activity, rows in aggregate.items()], key=lambda x: x[1])
        return {activity: sum for activity, sum in sorted_sums}

    def compute_length(self) -> list[FancyRow]:
        """Compute time between each value, and returns a list of all values with
        their length appended. The values are assumed to be sorted.

        :return: Table rows, with their time computed
        """
        entries = []
        next_moment = Moment.now()
        values = self.values
        for entry in values[::-1]:
            cur_moment = Moment.from_string(entry['moment'])
            if entry['activity'] == 'stop':
                next_moment = cur_moment
            time = next_moment - cur_moment
            entry['length'] = time.total_seconds()
            entries.append(entry)
            next_moment = cur_moment

        entries.reverse()
        return entries
