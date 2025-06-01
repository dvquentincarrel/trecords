#!/bin/python
import os
import sys
try:
    os.chdir(os.readlink(sys.argv[0]).rpartition('/')[0])
except OSError:
    pass

import atexit
from main import RecordTable, sec_to_hms
from config import config
from time_util import Moment
from orm import Database

now = Moment.now()

if __name__ == '__main__':
    db = Database(config['database'], RecordTable)
    table: "RecordTable" = db.tables['records']
    atexit.register(lambda: db.connection.close())

    ans = input('\n'.join([
        "Choose an option by its number:",
        "  1 - Add entry",
        "  2 - Add entry before",
        "  3 - Edit entries",
        "  4 - See daily entries",
        "  5 - See weekly entries",
        "  6 - See monthly entries",
        "  7 - See yearly entries",
        "  8 - See all entries",
        "  9 - See time per entry today",
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
            table.edit()
            exit()
        case '4':
            entries = table.get_current('day')
        case '5':
            entries = table.get_current('week')
        case '6':
            entries = table.get_current('month')
        case '7':
            entries = table.get_current('year')
        case '8':
            entries = table.compute_length()
        case '9':
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
