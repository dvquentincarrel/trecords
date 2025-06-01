#!/bin/python
import os
import sys
try:
    os.chdir(os.readlink(sys.argv[0]).rpartition('/')[0])
except OSError:
    pass

import atexit
from main import RecordTable, sec_to_hms
from time_util import Moment
from orm import Database
import argparse

now = Moment.now()
CONFIG_FILE="config.py"
DEFAULT_FILTER="day"
DEFAULT_ACTION="add"
VERSION="0.1"
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
parser.add_argument('-m', '--moment', help=f"YYYY-MM-DD moment to consider. {now} by default")
parser.add_argument('-v', '--version', action="version", version=f"trecords {VERSION}")
parser.add_argument('action', nargs='?', choices=['add', 'edit', 'see', 'sum', 'debug'], default=DEFAULT_ACTION, help=f"Action to execute over the lines corresponding to the filter. {DEFAULT_ACTION} by default.")
parser.parse_args(args, config)

if err:
    raise ValueError(err)

if config.moment:
    config.moment = Moment.from_string(config.moment)
else:
    config.moment = now

db = Database(config.database, RecordTable)
table: "RecordTable" = db.tables['records']
atexit.register(lambda: db.connection.close())

if config.action == 'add':
    table.add_entry(moment=config.moment)
    exit()

values = table.compute_length() if config.action != 'edit' else table.values
if config.filter != 'all':
    values = table.filter_by_date(config.moment, config.filter, values)

if config.action == 'see':
    for (time, act, comm, duration) in values:
        print(f"\x1b[1m{time}\x1b[m: [{sec_to_hms(duration)}] ({act}) ⇒ {comm}")
elif config.action == 'sum':
    span = config.filter if config.filter != 'all' else None
    sums = table.time_by_activity(span=span, moment=config.moment)
    for activity, time in sums.items():
        print(f"{activity}: {sec_to_hms(time)}")
elif config.action == 'debug':
    breakpoint()
