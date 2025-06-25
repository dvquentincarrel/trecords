#!/bin/env python3
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
import actions

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
    from config import config as tmp_cfg, Config
    vars(config).update(tmp_cfg)
    err = None
except ModuleNotFoundError:
    err = f'Config file "{config.config_file}" does not exist'

parser.add_argument('-h', '--help', action="help")
parser.add_argument('-f', '--filter', choices=['year', 'month', 'week', 'day', 'hour', 'all'], default=DEFAULT_FILTER, help=f"Which entries to consider. Those of the current {DEFAULT_FILTER} by default.")
parser.add_argument('-d', '--database', help=f"Where to find the database file. Gotten from config, by default")
parser.add_argument('-e', '--explode', action="store_true", help="For the 'sum' mode, give the comment and time span of each entry for each activity")
parser.add_argument('-m', '--moment', help=f"YYYY-MM-DD hh:mm:ss moment to consider. '{now}' (now) by default. Can take shorter formats too: ((YYYY-)MM-DD) (hh:mm(:ss))")
parser.add_argument('-v', '--version', action="version", version=f"trecords {VERSION}")
parser.add_argument('-j', '--json', action="store_true", help="Output data as json")
parser.add_argument('action', nargs='?', choices=['add', 'edit', 'see', 'sum', 'debug', 'report'], default=DEFAULT_ACTION, help=f"Action to execute over the lines corresponding to the filter. {DEFAULT_ACTION} by default.")
parser.parse_args(args, config)

if err:
    raise ValueError(err)

config: Config
if config.moment:
    config.moment = Moment.from_string(config.moment)
else:
    config.moment = now

db = Database(config.database, RecordTable)
table: "RecordTable" = db.tables['records']
table.default_sort = 'moment'
table._post_refresh()
atexit.register(lambda: db.connection.close())

values = table.compute_length() if config.action != 'edit' else table.values
if config.filter != 'all':
    values = table.filter_by_date(config.moment, config.filter, values)

match config.action:
    case 'add':
        actions.add(table, config)
        exit()
    case 'see':
        actions.see(table, config, values)
    case 'sum':
        actions.sum(table, config)
    case 'report':
        actions.report(table, config, values)
    case 'edit':
        actions.edit(table, values)
    case 'debug':
        import ipdb; ipdb.set_trace()
