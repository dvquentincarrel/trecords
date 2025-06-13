#!/bin/python3
import os
import sys
try:
    os.chdir(os.readlink(sys.argv[0]).rpartition('/')[0])
except OSError:
    pass

import json
import atexit
from main import RecordTable, sec_to_hms
from time_util import Moment
from orm import Database
import argparse

now = Moment.now()
CONFIG_FILE="config.py"
DEFAULT_FILTER="day"
DEFAULT_ACTION="add"
VERSION="0.4"
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    add_help=False,
)
parser.add_argument('-c', '--config-file', default=CONFIG_FILE, help=f"Path to the confilg file. Defaults to {CONFIG_FILE}")
config, args = parser.parse_known_args()
try:
    from config import config as tmp_cfg
    vars(config).update(tmp_cfg)
    err = None
except ModuleNotFoundError:
    err = f'Config file "{config.config_file}" does not exist'

parser.add_argument('-h', '--help', action="help")
parser.add_argument('-f', '--filter', choices=['year', 'month', 'week', 'day', 'hour', 'all'], default=DEFAULT_FILTER, help=f"Which entries to consider. Those of the current {DEFAULT_FILTER} by default.")
parser.add_argument('-d', '--database', help=f"Where to find the database file. Gotten from config, by default")
parser.add_argument('-m', '--moment', help=f"YYYY-MM-DD hh:mm:ss moment to consider. '{now}' (now) by default. Can take shorter formats too: ((YYYY-)MM-DD) (hh:mm(:ss))")
parser.add_argument('-v', '--version', action="version", version=f"trecords {VERSION}")
parser.add_argument('-j', '--json', action="store_true", help="Output data as json")
parser.add_argument('action', nargs='?', choices=['add', 'edit', 'see', 'sum', 'debug', 'report'], default=DEFAULT_ACTION, help=f"Action to execute over the lines corresponding to the filter. {DEFAULT_ACTION} by default.")
parser.parse_args(args, config)

if err:
    raise ValueError(err)

if config.moment:
    config.moment = Moment.from_string(config.moment)
else:
    config.moment = now

db = Database(config.database, RecordTable)
table: "RecordTable" = db.tables['records']
table.default_sort = 'moment'
table._post_refresh()
atexit.register(lambda: db.connection.close())

if config.action == 'add':
    table.add_entry(moment=config.moment)
    exit()

values = table.compute_length() if config.action != 'edit' else table.values
if config.filter != 'all':
    values = table.filter_by_date(config.moment, config.filter, values)

if config.action == 'see':
    if config.json:
        print(json.dumps(values, indent=2))
    else:
        for value in values:
            print(
                f"\x1b[1m{value['moment']}\x1b[m: [{sec_to_hms(value['length'])}] ({value['activity']})"
                + (f" ⇒ {value['comment']}" if value['comment'] else '')
            )
elif config.action == 'sum':
    span = config.filter if config.filter != 'all' else None
    sums = table.time_by_activity(span=span, moment=config.moment, activities_to_exclude=config.activities_to_exclude)
    sums['grand total'] = sum(val for val in sums.values())
    moments = config.moment.range(config.filter if config.filter != 'all' else 'day')
    print(f"from \x1b[1m{moments[0]}\x1b[m to \x1b[1m{moments[1]}\x1b[m\n", file=sys.stderr)
    if config.json:
        print(json.dumps(sums, indent=2))
    else:
        for activity, time in sums.items():
            print(f"{activity}: {sec_to_hms(time)}")
elif config.action == 'report':
    done_time_per_day = table.time_per_day(table.group_by_day(values), ['pause'])
    expected_time_per_day = config.expectation_model.expected_time_by_date
    result = {}
    for date, val in done_time_per_day.items():
        result[date] = val - expected_time_per_day[date]

    for data in result.values():
        cur_code = 32 if data.current > 0 else 31
        sum_code = 32 if data.sum > 0 else 31
        wrapper = lambda code, msg: f"\x1b[{code}m{sec_to_hms(msg, with_sign=False)}\x1b[m"
        print(f"{data.date}: {wrapper(cur_code, data.current)} / {wrapper(sum_code, data.sum)}")

    print()
    print(f"ending time: {now._offset('second', abs(data.sum)).strftime('%T')}")

elif config.action == 'edit':
    table.edit(values)
elif config.action == 'debug':
    breakpoint()
