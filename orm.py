import sqlite3
from collections.abc import Iterable
from typing import Any, Optional
import subprocess
import json
import os
import tempfile

class Table:
    def __init__(self, name: str, parent: "Database"):
        """
        :param name: Table name
        :param connection: Database connection
        """
        self.name = name
        self.enqueued: Iterable[Iterable[Any]] = []
        self.values: dict[int, tuple[Any]] = {}
        self.parent = parent
        self.connection = parent.connection

        cur = self.connection.cursor()
        cur.execute(f"PRAGMA table_info({self.name})")
        self.columns: list[str]  = [row[1] for row in cur.fetchall()]
        self.refresh_vals(cur)
        cur.close()

    def __repr__(self):
        return f"<Table \x1b[96m{self.name}\x1b[m nrows=\x1b[96m{len(self.values)}\x1b[m ncols=\x1b[96m{len(self.columns)}\x1b[m>"

    def _post_refresh(self):
        """Does something after fetching the rows"""
        pass

    def refresh_vals(self, cur: Optional[sqlite3.Cursor] = None):
        """Updates the values field by fetching all rows of the table
            """
        close_cur = not cur
        if not cur:
            cur = self.connection.cursor()

        cur.execute(f"SELECT rowid, * FROM {self.name}")
        self.values = {row[0]: row[1:] for row in cur.fetchall()}
        self._post_refresh()
        if close_cur:
            cur.close()

    def add(self, row: Iterable[Any] | str):
        """Enqueus write of a row
        :param row: Row to write to the table
        """
        if not isinstance(row, (list, tuple)):
            row = [row]

        self.enqueued.append(row)
    def edit(self, filter=None):
        """Edits rows with an external editor"""
        if filter is None:
            values = tuple(self.values.values())
        data = []
        for id, row in self.values.items():
            json_row = {'rowid': id}
            json_row |= {self.columns[i]: col_val for i, col_val in enumerate(row)}
            data.append(json_row)

        tmp_file = tempfile.mktemp(suffix=".json")
        with open(tmp_file, 'w') as file:
            json.dump(data, file, indent=2)

        subprocess.run([os.getenv('EDITOR', 'vim'), tmp_file])
        with open(tmp_file, 'r') as file:
            new_data = json.load(file)
        os.remove(tmp_file)

        # Skip updating rows if no modifications were made
        if data == new_data:
            return None

        new_rows = [tuple(row.values()) for row in new_data]
        col_names = '"{}"'.format(
            '", "'.join(['rowid', *self.columns])
        )
        placeholder = ','.join(['?'] * (1 + len(self.columns)))
        cur = self.connection.cursor()
        cur.executemany(
            f"""
            INSERT OR REPLACE
                INTO {self.name} ({col_names})
            VALUES({placeholder})""",
            new_rows)
        self.connection.commit()
        cur.close()

    def flush(self):
        """Flushes write of enqueued rows. Refreshes all of the object's known rows"""
        cur = self.connection.cursor()
        # Output like "INSERT INTO my_table VALUES(?, ?, ?, ...)"
        cur.executemany(f"INSERT INTO {self.name} VALUES({','.join(['?']*len(self.columns))})", self.enqueued)
        self.refresh_vals(cur)
        self.connection.commit()
        cur.close()

class Database:
    def __init__(self, db_file: str, table_obj = Table):
        self.connection: sqlite3.Connection = sqlite3.Connection(db_file)
        self.tables: dict[str, "Table"] = {}

        cond = lambda row: row[2] == 'table' and not row[1].startswith('sqlite')
        cur = self.connection.cursor()
        cur.execute("PRAGMA table_list")
        _schema_rows = filter(cond, cur.fetchall())
        for row in _schema_rows:
            _table = table_obj(row[1], self)
            self.tables[_table.name] = _table
        cur.close()

if __name__ == '__main__':
    from config import config
    from pprint import pp
    db = Database(config['database'])
    pp(db.tables)
