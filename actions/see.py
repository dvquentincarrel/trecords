from main import RecordTable, sec_to_hms
from orm import FancyRow
from config import Config
import json

def main(table: RecordTable, config: Config, values: list[FancyRow]):
    """Displays entries matching the given filter"""
    if config.json:
        print(json.dumps(values, indent=2))
    else:
        for value in values:
            print(
                f"\x1b[1m{value['moment']}\x1b[m: [{sec_to_hms(value['length'])}] ({value['activity']})"
                + (f" ⇒ {value['comment']}" if value['comment'] else '')
            )
