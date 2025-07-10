from main import RecordTable, sec_to_hms
from orm import FancyRow
from config import Config
from time_util import Moment

def main(table: RecordTable, config: Config, values: list[FancyRow]):
    """Displays the difference between the theoretical and real time spent"""
    done_time_per_day = table.time_per_day(table.group_by_day(values), ['pause'])
    expected_time_per_day = config.expectation_model.expected_time_by_date
    result = {}
    for date, val in done_time_per_day.items():
        result[date] = val - expected_time_per_day[date]

    print("            for day    for month")
    for data in result.values():
        cur_code = 32 if data.current > 0 else 31
        sum_code = 32 if data.sum > 0 else 31
        wrapper = lambda code, msg: f"\x1b[{code}m{sec_to_hms(msg, with_sign=False)}\x1b[m"
        print(f"{data.date}: {wrapper(cur_code, data.current)} / {wrapper(sum_code, data.sum)}")
    assert data, "No entries over which to report, it seems"

    pause_taken_today = table.time_by_activity(span='day', moment=config.moment).get('pause', 0)
    remaining_pause = max(0, config.expectation_model.pause - pause_taken_today)
    print()

    # Incoherencies with pause time because the data to get completely accurate
    # feedback is not available to us directly here. We do not which entries
    # are done after the required time is fulfilled, thus, we cannot ignore those
    # that come after, or the surplus on the one that fulfilled the need.
    # Getting accurate feedback on ending time would require iterating over
    # today's entries and computing a running sum of the time done, until the
    # quota is met.
    # Also, we cannot say with certainty when a quota will be met until is IS met,
    # becaues pauses/stops can be added in the middle of the day, which will postpone
    # its meeting. Until it is met, we MUST base our calculations on the current moment.
    # Afterwards, we MUST base our computations on the starting time of the day, because
    # the current moment can keep on moving without adding anything to the time done or 
    # pause time done (last activity is stop)
    if data.sum < 0:
        ending_moment = config.moment._offset('second', abs(data.sum - remaining_pause))
    else:
        first_entry_today = table.group_by_day(values)[date.strftime("%F")][0]
        yesterday = list(result.keys())[-2]
        expected_time_today = expected_time_per_day[date].sum - done_time_per_day[yesterday].sum
        ending_moment = Moment.from_string(first_entry_today['moment'])._offset('second', expected_time_today + pause_taken_today)

    print(f"ending time: {ending_moment.strftime('%T')}")
