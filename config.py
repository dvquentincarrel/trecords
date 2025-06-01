import os

config = dict(
    database="database.db"
)

if not os.path.exists(config['database']):
    import subprocess
    with open('schema.sql', 'r') as file:
        schema = file.read()

    subprocess.run(["sqlite3", config['database']], input=schema, text=True)
