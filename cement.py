from dataclasses import dataclass, field
import datetime
from typing import Optional
from collections import defaultdict

Seconds = int
DateString = str # YYYY-MM-DD

@dataclass
class MonthlyExpectations:
    date: DateString
    pause: Seconds
    bidaily_expectations: Seconds
    excluded_half_days: list[DateString] = field(default_factory=list)
    excluded_days: list[DateString] = field(default_factory=list)

    @classmethod
    def from_model(cls, model: "MonthlyExpectations", **kwargs):
        base = vars(model)
        base |= kwargs
        return cls(**base)

def itermonthdates(date: datetime.date, end: Optional[datetime.date] = None) -> list[datetime.date]:
    """Get list of all days in the month of the given date
    
    :param: date: date for which the month is considered
    :param: end: optional end date. End of the month by default
    :return: Iterator to get all the days of the month (up to the given end point)
    """
    first = datetime.datetime(year=date.year, month=date.month, day=1)
    if not end:
        end = datetime.datetime(year=date.year, month=date.month+1, day=1) - datetime.timedelta(days=1)
    for day in range(first.day, end.day+1):
        yield datetime.datetime(year=date.year, month=date.month, day=day)

def expected_time(dates: list[datetime.date], expectations: MonthlyExpectations) -> dict[datetime.date, int]:
    """Computes time expected to be done by all the days that are considered

    :param: dates: list of days to consider
    :param: expectations: Expectation containing the specific days to filter out,
        as well as how much time is expected for a regular day
    :return: Map of days and their expected time, ordered from first day to last
    """
    kept_dates = {}
    for day in dates:
        if day.weekday() > 4: # 4 is friday
            continue
        elif day in expectations.excluded_days:
            continue
        elif day in expectations.excluded_half_days:
            kept_dates[day] = expectations.bidaily_expectations
        else:
            kept_dates[day] = expectations.bidaily_expectations * 2
    return kept_dates

def time_by_date(rows: dict) -> dict[datetime.date, int]:
    date_time_map = defaultdict(lambda: 0)
    for row in rows:
        date = row['moment'][:10]
        date_time_map[date] += row['length']
    return {datetime.datetime.strptime(date_str, '%Y-%m-%d'):time for date_str, time in date_time_map.items()}

if __name__ == '__main__':
    from config import config
    now = datetime.date.today()
    dates = itermonthdates(now)
    ex_time = expected_time(dates, config['expectation_model'])
