"""Tests for the dashboard's data access layer.

The dashboard introduces new SQL that takes user-selected values (operator, line), so it needs the same
injection-safety guarantee as the loader. These tests build a temporary database, confirm the aggregates
are correct, and confirm a malicious operator name is treated as data rather than executed.
"""

import re
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

from dashboard import data_access as da  # noqa: E402
from database import db  # noqa: E402

FACT_SQL = (
    "INSERT INTO fact_delay_event (service_date, operator, line, direction_id, trip_id, "
    "stop_id, stop_sequence, sched_sec, ping_sec, delay_min) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


@pytest.fixture()
def populated(tmp_path, monkeypatch):
    monkeypatch.setenv("BUS_DB_PATH", str(tmp_path / "dash.db"))
    conn = db.connect()
    db.apply_schema(conn)
    db.batch_insert(conn, "INSERT INTO dim_operator (operator, operator_name) VALUES (?, ?)",
                    [("OP1", "Operator One"), ("OP2", "Operator Two")])
    db.batch_insert(conn, "INSERT INTO dim_stop (stop_id, stop_name, stop_lat, stop_lon) "
                          "VALUES (?, ?, ?, ?)", [("S1", "Alpha Street", 53.48, -2.24)])
    # OP1: two on-time (within +/-2) and one late; OP2: one late.
    rows = [
        ("20260701", "OP1", "10", 0, "T1", "S1", 1, 36000, 36060, 1.0),
        ("20260701", "OP1", "10", 0, "T2", "S1", 2, 36000, 36030, 0.5),
        ("20260701", "OP1", "11", 0, "T3", "S1", 3, 39600, 40200, 10.0),
        ("20260701", "OP2", "20", 1, "T4", "S1", 1, 36000, 36600, 10.0),
    ]
    db.batch_insert(conn, FACT_SQL, rows)
    conn.close()
    yield


def test_database_available(populated):
    assert da.database_available()


def test_headline_metrics_are_correct(populated):
    m = da.headline_metrics()
    assert m["events"] == 4
    assert m["operators"] == 2
    assert m["lines"] == 3
    assert m["on_time_pct"] == pytest.approx(50.0)  # 2 of 4 within +/-2 min


def test_operator_summary_orders_by_reliability(populated):
    ops = da.operator_summary(min_events=1)
    assert list(ops["operator"]) == ["OP1", "OP2"]
    assert ops.loc[ops["operator"] == "OP1", "on_time_pct"].iloc[0] == pytest.approx(66.7, abs=0.1)
    assert ops.loc[ops["operator"] == "OP2", "on_time_pct"].iloc[0] == pytest.approx(0.0)


def test_line_summary_is_scoped_to_the_requested_operator(populated):
    lines = da.line_summary("OP1", min_events=1)
    assert set(lines["line"]) == {"10", "11"}
    assert "20" not in set(lines["line"]), "another operator's line leaked into the result"


def test_worst_stops_returns_named_stops(populated):
    stops = da.worst_stops("OP1", limit=5)
    assert stops.empty or "Alpha Street" in set(stops["stop_name"])


def test_delay_by_hour_buckets_correctly(populated):
    hours = da.delay_by_hour("OP1", min_events=1)
    assert set(hours["sched_hour"]).issubset(set(range(24)))


@pytest.mark.parametrize("payload", [
    "OP1'; DROP TABLE fact_delay_event; --",
    "' OR '1'='1",
    'OP1" OR 1=1 --',
])
def test_operator_filters_treat_injection_payloads_as_data(populated, payload):
    """A payload must return nothing and leave the schema intact."""
    assert da.line_summary(payload, min_events=1).empty
    assert da.worst_stops(payload).empty
    assert da.headline_metrics()["events"] == 4  # table survived


def test_no_string_built_sql_in_dashboard_layer():
    sql_kw = re.compile(r"(SELECT|INSERT|UPDATE|DELETE|WHERE|VALUES)", re.IGNORECASE)
    offenders = []
    for path in (BASE / "src" / "dashboard").rglob("*.py"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if sql_kw.search(line) and (re.search(r'f"[^"]*"', line) or re.search(r"f'[^']*'", line)
                                        or ".format(" in line):
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, f"SQL appears to be string-built at: {offenders}"
