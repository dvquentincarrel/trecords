from collections import defaultdict
import datetime
from typing import Literal
from orm import Database, FancyRow, Table
from config import config
from time_util import Moment, Span
from cement import DailyExpectation

def filter(*args, _filter=filter, **kwargs):
    return list(_filter(*args, **kwargs))

def sec_to_hms(seconds: int, round_seconds=False, with_sign=True) -> str:
    seconds = int(seconds)
    sign = '-' if seconds < 0 and with_sign else ''
    seconds = abs(seconds)
    if seconds:
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
    else:
        hours = minutes = seconds = 0

    if round_seconds:
        if seconds >= 30:
            minutes += 1
            seconds = 0
        return f"{sign}{hours:02}:{minutes:02}"
    else:
        return f"{sign}{hours:02}:{minutes:02}:{seconds:02}"

class RecordTable(Table):

    def _post_refresh(self):
        if self.default_sort:
            self.values.sort(key=lambda x: x[self.default_sort])

    def add_entry(
        self,
        moment: Moment = None,
        activity: str = None,
        comment: str = None
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

    def group_by_activity(self, span=None, moment=None, with_length=False, activities_to_exclude: None | list[str] = None):
        """Regroups activity filtered around a span for a given moment by
        their activity.
        :param span: Timespan around the moment for which to filter. No filtering
        if None
        :param moment: Moment around which to apply the timespan. Now if None
        :param with_length: Compute length of the rows beforehand
        :param activities_to_exclude: List of activities to exclude
        """
        values = self.compute_length() if with_length else self.values
        if moment is None:
            moment = Moment.now()
        entries = self.filter_by_date(moment, span, values) if span else values

        rows_map = defaultdict(list)
        for row in entries:
            rows_map[row['activity']].append(row)

        if activities_to_exclude:
            for activity_name in activities_to_exclude:
                rows_map.pop(activity_name, None)

        return dict(rows_map)

    def time_by_activity(self, span=None, moment=None, activities_to_exclude: None | list[str] = None) -> dict[str, int]:
        """Compute total time spent on an activity, for a filtered subset of all
        values, according to span and moment.
        :param span: Span of values to consider
        :param moment: Moment around which to consider the span
        :param activities_to_exclude: List of activities to exclude

        :return: Mapping of activities and the time spent on them, ordered
        by least to most time spent
        """
        aggregate = self.group_by_activity(span=span, moment=moment, with_length=True, activities_to_exclude=activities_to_exclude)
        sorted_sums = sorted([(activity, sum(row[-1] for row in rows)) for activity, rows in aggregate.items()], key=lambda x: x[1])
        return {activity: sum for activity, sum in sorted_sums}

    def compute_length(self) -> list[FancyRow]:
        """Compute time between each value, and returns a list of all values with
        their length (in seconds) appended. The values are assumed to be sorted.

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

    def group_by_day(self, values: list[FancyRow]) -> list[FancyRow]:
        """Group given rows by day"""
        group = defaultdict(list)
        for value in values:
            group[value['moment'][:10]].append(value)

        return group

    def time_per_day(self, day_aggregate: dict[str, list[FancyRow]], activities_to_exclude: None | list[str] = None) -> dict[datetime.date, "DailyExpectation"]:
        expectations = {}
        running_sum = 0
        activities_to_exclude = activities_to_exclude or []
        for day, moments in day_aggregate.items():
            current = 0
            for moment in filter(lambda x: x['activity'] not in activities_to_exclude, moments):
                current += moment['length']
            running_sum += current
            date_day = Moment.from_string(day).date()
            expectations[date_day] = DailyExpectation(date_day, current, running_sum)

        return expectations
