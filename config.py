import os
import cement
import datetime

config = dict(
    database="database.db",
    expectation_model=cement.MonthlyExpectations(
        date=datetime.date.today().strftime("%F"),
        pause=3600,
        bidaily_expectations=int(39*3600/5/2),
        excluded_half_days=[],
        excluded_days=['2025-06-20', '2025-06-21'],
    ),
    activities_to_exclude=['stop', 'pause'],
)

if not os.path.exists(config['database']):
    import subprocess
    with open('schema.sql', 'r') as file:
        schema = file.read()

    subprocess.run(["sqlite3", config['database']], input=schema, text=True)
