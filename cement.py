from dataclasses import dataclass, field
import time_util 
import datetime
from typing import Optional
from collections import defaultdict

Seconds = int
DateString = str # YYYY-MM-DD

@dataclass
class DailyExpectation:
    date: DateString
    current: int
    sum: int

    def __neg__(self):
        return DailyExpectation(
            self.date,
            -self.current,
            -self.sum,
        )

    def __add__(self, other):
        if self.date != other.date:
            raise ValueError("Dates aren't the same")
        return DailyExpectation(
            self.date,
            self.current + other.current,
            self.sum + other.sum,
        )

    def __sub__(self, other):
        if self.date != other.date:
            raise ValueError("Dates aren't the same")
        return self + (-other)

@dataclass
class MonthlyExpectations:
    date: DateString
    pause: Seconds
    bidaily_expectations: Seconds
    excluded_half_days: list[datetime.date | DateString] = field(default_factory=list)
    excluded_days: list[datetime.date | DateString] = field(default_factory=list)
    expected_time_by_date: dict[datetime.date, "DailyExpectation"] = None

    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = time_util.Moment.from_string(self.date)
        for _list in (self.excluded_half_days, self.excluded_days) :
            for i, date in enumerate(_list):
                _list[i] = time_util.Moment.from_string(date).date()
        self.__expected_time_by_date()

    @classmethod
    def from_model(cls, model: "MonthlyExpectations", **kwargs):
        base = vars(model)
        base |= kwargs
        return cls(**base)

    def __expected_time_by_date(self):
        """Compute the time to do each day and the running sum for that day
        Excludes weekends by default
        """
        dates = time_util.itermonthdates(self.date)
        running_sum = 0
        expectations = {}
        for date in dates:
            if date.weekday() > 4 or date in self.excluded_days: # 4 is friday
                current = 0
            elif date in self.excluded_half_days:
                current = self.bidaily_expectations
            else:
                current = self.bidaily_expectations * 2
            running_sum += current
            expectations[date] = DailyExpectation(date, current, running_sum)
        self.expected_time_by_date = expectations

    def compare(self, comparison_point: dict[datetime.date, dict]):
        """Compares the expectations with the real data. Returns the difference
        per date"""
        diff_data = {}
        for date, real_data in comparison_point.items():
            expected_data = self.expected_time_by_date[date]
            diff_data[date] = {
                'current': None
            }
            

if __name__ == '__main__':
    now = datetime.date.today()
    expec = MonthlyExpectations(
        '2025-02-18',
        3600,
        3600*39/(5*2),
        ['2025-02-04', '2025-02-01'],
        ['2025-02-05', '2025-02-06'],
    )
    from pprint import pp
    print("date:",expec.date)
    print("excl:",expec.excluded_days)
    print("half excl:",expec.excluded_half_days)
    pp(expec.expected_time_by_date)
