from main import RecordTable, sec_to_hms
from orm import FancyRow
from config import Config

def main(table: RecordTable, config: Config, values: list[FancyRow]):
    """Displays the difference between the theoretical and real time spent"""
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

    pause_taken_today = table.time_by_activity(span='day', moment=config.moment).get('pause', 0)
    remaining_pause = max(0, config.expectation_model.pause - pause_taken_today)
    print()
    print(f"ending time: {config.moment._offset('second', abs(data.sum - remaining_pause)).strftime('%T')}")
