#!/bin/python
import atexit
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

now = Moment.now()
class RecordTable(Table):

    def _post_refresh(self):
        # Order by time
        self.values.sort(key=lambda x: x[0])

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

    def filter_by_date(self, moment: Moment, span: Span, values=None) -> list[list]:
        """Returns entries encompassing the given span around the given moment"""
        if values is None:
            values = self.values

        start, end = map(lambda x: str(x), moment.range(span))
        return list(filter(lambda val: start <= val[0] < end , values))


    def get_current(self, span: Span) -> list[list]:
        """Returns current entries encompassing the given span"""
        return self.filter_by_date(now, span)

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
            moment = now
        entries = self.filter_by_date(moment, span, values) if span else values

        rows_map = defaultdict(list)
        for row in entries:
            rows_map[row[1]].append(row)

        if exclude_stop:
            rows_map.pop('stop', None)

        return dict(rows_map)

    def compute_length(self) -> list:
        """Compute time between each value, and returns a list of all values with
        their length appended. The values are assumed to be sorted.

        :return: Table rows, with their time computed
        """
        entries = []
        next_moment = Moment.now()
        for entry in self.values[::-1]:
            cur_moment = Moment.from_row(entry[0])
            if entry[1] == 'stop':
                next_moment = cur_moment
            time = next_moment - cur_moment
            entries.append([*entry, time.total_seconds()])
            next_moment = cur_moment

        entries.reverse()
        return entries


if __name__ == '__main__':
    atexit.register(lambda: db.connection.close())
    db = Database(config['database'], RecordTable)
    table: "RecordTable" = db.tables['records']
    ans = input('\n'.join([
        "Choose an option by its number:",
        "  1 - Add entry",
        "  2 - Add entry before",
        "  3 - See daily entries",
        "  4 - See weekly entries",
        "  5 - See monthly entries",
        "  6 - See yearly entries",
        "  7 - See all entries",
        "  8 - See time per entry today",
        "  99 - debug",
        "",
    ]))
    match ans:
        case '1':
            table.add_entry()
            exit()
        case '2':
            ans = input("Negative minutes offset: ")
            moment = now._offset('minute', -float(ans))
            table.add_entry(moment=moment)
            exit()
        case '3':
            entries = table.get_current('day')
        case '4':
            entries = table.get_current('week')
        case '5':
            entries = table.get_current('month')
        case '6':
            entries = table.get_current('year')
        case '7':
            entries = table.compute_length()
        case '8':
            data = {key:sum(row[-1] for row in rows) for key,rows in table.group_by_activity(span='day', with_length=True).items()}
            for k,v in data.items():
                print(f"{k}: {sec_to_hms(v)}")
            exit(0)
        case '99':
            breakpoint()
            exit(0)
        case _:
            exit(1)
    for (time, act, comm, *other) in entries:
        print(f"{time}: ({act}) ⇒ {comm} {other}")
