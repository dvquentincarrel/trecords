#!/bin/python
import atexit
from orm import Database, Table
from config import config
from time_util import Moment, Span

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

    def filter_by_date(self, moment: Moment, span: Span) -> list[list]:
        """Returns entries encompassing the given span around the given moment"""
        start, end = map(lambda x: str(x), moment.range(span))
        return list(filter(lambda val: start <= val[0] < end ,self.values))


    def get_current(self, span: Span) -> list[list]:
        """Returns current entries encompassing the given span"""
        return self.filter_by_date(now, span)

if __name__ == '__main__':
    db = Database(config['database'], RecordTable)
    table: "RecordTable" = db.tables['records']
    table.add_entry()
    atexit.register(lambda: db.connection.close())
