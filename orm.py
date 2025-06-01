import sqlite3
from collections.abc import Iterable
from typing import Any, Optional

class Table:
    def __init__(self, name: str, parent: "Database"):
        """
        :param name: Table name
        :param connection: Database connection
        """
        self.name = name
        self.enqueued: Iterable[Iterable[Any]] = []
        self.values = []
        self.parent = parent
        self.connection = parent.connection

        cur = self.connection.cursor()
        cur.execute(f"PRAGMA table_info({self.name})")
        self.columns: list[str] = [row[1] for row in cur.fetchall()]
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

        cur.execute(f"SELECT * FROM {self.name}")
        self.values = cur.fetchall()
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
