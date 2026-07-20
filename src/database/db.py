"""SQLite access layer: connection config, parameterised queries, batch loading.

All SQL that takes user/data values goes through parameterised placeholders (never string formatting),
per PROJECT_RULES section 4 and the security skill. The database path comes from the BUS_DB_PATH env var
(no hard-coded secrets); SQLite itself needs no credentials, and .env.example documents how PostgreSQL
credentials would be supplied via env if the schema is ported.
"""

import os
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE / "data" / "processed" / "bus_analytics.db"
SCHEMA_PATH = BASE / "sql" / "schema.sql"

INSERT_BATCH = 5000


def db_path() -> Path:
    return Path(os.environ.get("BUS_DB_PATH", str(DEFAULT_DB_PATH)))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")  # SQLite enforces FKs only when this is set per connection.
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def batch_insert(conn: sqlite3.Connection, sql: str, rows: Iterable[Sequence]) -> int:
    """Parameterised bulk insert in chunks. `sql` must use '?' placeholders; values are always bound."""
    cur = conn.cursor()
    total, batch = 0, []
    for row in rows:
        batch.append(row)
        if len(batch) >= INSERT_BATCH:
            cur.executemany(sql, batch)
            total += len(batch)
            batch = []
    if batch:
        cur.executemany(sql, batch)
        total += len(batch)
    conn.commit()
    return total


def query(conn: sqlite3.Connection, sql: str, params: Sequence = ()) -> list:
    """Runs a parameterised SELECT and returns all rows. Never interpolate values into `sql`."""
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur.fetchall()
