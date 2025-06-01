from collections import defaultdict
from orm import Database, Table
from config import config
from time_util import Moment, Span

def sec_to_hms(seconds: int) -> str:
    seconds = int(seconds)
    if seconds:
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
    else:
        hours = minutes = seconds = 0
    return f"{hours:02}:{minutes:02}:{seconds:02}"

class RecordTable(Table):

    def _post_refresh(self):
        # Order by time
        #self.values.sort(key=lambda x: x[0])
        pass

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

    def filter_by_date(self, moment: Moment, span: Span, values: list[tuple] | None = None) -> list[list]:
        """Returns entries encompassing the given span around the given moment"""
        if values is None:
            values = tuple(self.values.values())

        start, end = map(lambda x: str(x), moment.range(span))
        return list(filter(lambda val: start <= val[0] < end , values))


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
        values = self.compute_length() if with_length else tuple(self.values.values())
        if moment is None:
            moment = Moment.now()
        entries = self.filter_by_date(moment, span, values) if span else values

        rows_map = defaultdict(list)
        for row in entries:
            rows_map[row[1]].append(row)

        if exclude_stop:
            rows_map.pop('stop', None)

        return dict(rows_map)

    def time_by_activity(self, span=None, moment=None, exclude_stop=True):
        aggregate = self.group_by_activity(span=span, moment=moment, with_length=True, exclude_stop=exclude_stop)
        return {activity: sum(row[-1] for row in rows) for activity, rows in aggregate.items()}

    def compute_length(self) -> list:
        """Compute time between each value, and returns a list of all values with
        their length appended. The values are assumed to be sorted.

        :return: Table rows, with their time computed
        """
        entries = []
        next_moment = Moment.now()
        values = sorted(list(self.values.values()), key=lambda x: x[0])
        for entry in values[::-1]:
            cur_moment = Moment.from_string(entry[0])
            if entry[1] == 'stop':
                next_moment = cur_moment
            time = next_moment - cur_moment
            entries.append([*entry, time.total_seconds()])
            next_moment = cur_moment

        entries.reverse()
        return entries
