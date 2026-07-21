"""Tests for the database layer's injection safety and referential integrity.

Required by PROJECT_RULES section 6 and the security standard: all SQL must use bound parameters, and
foreign keys must actually be enforced rather than merely declared. The injection test uses a classic
payload against a temporary database, so a regression to string-built SQL would fail the suite rather
than pass silently.
"""

import re
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from database import db  # noqa: E402


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("BUS_DB_PATH", str(tmp_path / "test.db"))
    connection = db.connect()
    db.apply_schema(connection)
    db.batch_insert(connection, "INSERT INTO dim_operator (operator, operator_name) VALUES (?, ?)",
                    [("OP1", "Operator One"), ("OP2", "Operator Two")])
    yield connection
    connection.close()


def test_schema_applies_and_dimensions_load(conn):
    assert db.query(conn, "SELECT COUNT(*) FROM dim_operator")[0][0] == 2


def test_parameterised_query_treats_injection_payload_as_data(conn):
    """A classic payload must return no rows, not execute, and must leave the table intact."""
    payload = "OP1'; DROP TABLE dim_operator; --"
    rows = db.query(conn, "SELECT operator FROM dim_operator WHERE operator = ?", (payload,))
    assert rows == []
    assert db.query(conn, "SELECT COUNT(*) FROM dim_operator")[0][0] == 2


def test_parameterised_query_returns_the_intended_row(conn):
    rows = db.query(conn, "SELECT operator_name FROM dim_operator WHERE operator = ?", ("OP1",))
    assert rows == [("Operator One",)]


def test_foreign_keys_are_enforced(conn):
    """A fact row referencing a non-existent operator must be rejected, not silently accepted."""
    import sqlite3

    db.batch_insert(conn, "INSERT INTO dim_stop (stop_id, stop_name, stop_lat, stop_lon) "
                          "VALUES (?, ?, ?, ?)", [("S1", "Stop One", 53.48, -2.24)])
    with pytest.raises(sqlite3.IntegrityError):
        db.batch_insert(
            conn,
            "INSERT INTO fact_delay_event (service_date, operator, line, direction_id, trip_id, "
            "stop_id, stop_sequence, sched_sec, ping_sec, delay_min) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [("20260701", "NOPE", "42", 0, "T1", "S1", 1, 100, 160, 1.0)],
        )


def test_valid_fact_row_is_accepted(conn):
    db.batch_insert(conn, "INSERT INTO dim_stop (stop_id, stop_name, stop_lat, stop_lon) "
                          "VALUES (?, ?, ?, ?)", [("S1", "Stop One", 53.48, -2.24)])
    inserted = db.batch_insert(
        conn,
        "INSERT INTO fact_delay_event (service_date, operator, line, direction_id, trip_id, "
        "stop_id, stop_sequence, sched_sec, ping_sec, delay_min) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [("20260701", "OP1", "42", 0, "T1", "S1", 1, 100, 160, 1.0)],
    )
    assert inserted == 1
    assert db.query(conn, "SELECT delay_min FROM fact_delay_event WHERE trip_id = ?", ("T1",)) == [(1.0,)]


def test_no_string_built_sql_in_database_layer_or_scripts():
    """Guards the rule directly: no f-string, concatenation or .format() used to build SQL."""
    sql_kw = re.compile(r"(SELECT|INSERT|UPDATE|DELETE|WHERE|VALUES)", re.IGNORECASE)
    offenders = []
    targets = list((SRC / "database").rglob("*.py"))
    targets += [Path(__file__).resolve().parent.parent / "scripts" / "load_db.py"]
    for path in targets:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not sql_kw.search(line):
                continue
            if re.search(r'f"[^"]*"', line) or re.search(r"f'[^']*'", line) or ".format(" in line:
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, f"SQL appears to be string-built at: {offenders}"


def test_no_hardcoded_credentials_in_database_layer():
    pattern = re.compile(r"(password|passwd|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE)
    for path in (SRC / "database").rglob("*.py"):
        assert not pattern.search(path.read_text(encoding="utf-8")), f"possible literal secret in {path}"
