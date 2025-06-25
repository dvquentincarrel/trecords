import sys
import json
from main import RecordTable, sec_to_hms
from config import Config

def main(table: RecordTable, config: Config):
    """Display the sum of the time spent per activity over the given span"""
    span = config.filter if config.filter != 'all' else None
    if config.explode:
        detail = table.group_by_activity(span=span, moment=config.moment, with_length=True)
    sums = table.time_by_activity(span=span, moment=config.moment, activities_to_exclude=['stop'])
    sums['grand total'] = sum(val for key, val in sums.items() if key != 'pause')
    moments = config.moment.range(config.filter if config.filter != 'all' else 'day')
    print(f"from \x1b[1m{moments[0]}\x1b[m to \x1b[1m{moments[1]}\x1b[m\n", file=sys.stderr)
    if config.json:
        print(json.dumps(sums, indent=2))
    else:
        for activity, time in sums.items():
            print(f"{activity}: {sec_to_hms(time)}")
            if config.explode:
                for entry in filter(lambda x: x['comment'], detail.get(activity, [])):
                    print(f"  \x1b[90m[{sec_to_hms(entry['length'])}]\x1b[m {entry['comment']}")
