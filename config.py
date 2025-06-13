import os
import cement

config = dict(
    database="database.db",
    expectation_model=cement.MonthlyExpectations(
        date="2020-01-01",
        pause=3600,
        bidaily_expectations=int(39*3600/5/2),
        excluded_half_days=[],
        excluded_days=[],
    ),
    activities_to_exclude=['stop', 'pause'],
)

if not os.path.exists(config['database']):
    import subprocess
    with open('schema.sql', 'r') as file:
        schema = file.read()

    subprocess.run(["sqlite3", config['database']], input=schema, text=True)
