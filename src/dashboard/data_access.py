"""Read-only data access for the dashboard.

Queries the relational store built by scripts/load_db.py through the project's parameterised query
helpers, so the dashboard inherits the same injection safety as the rest of the system. It computes no
new results: every figure it shows is derived from data the pipeline already produced.

Pandas is used here rather than PySpark because the dashboard serves small aggregates interactively,
where a Spark session per request would add latency without benefit.
"""

from pathlib import Path

import pandas as pd

from database import db

BASE = Path(__file__).resolve().parent.parent.parent
MODEL_CSV = BASE / "outputs" / "model_comparison.csv"
FIG_DIR = BASE / "outputs" / "figures"

ON_TIME_TOL_MIN = 2.0


def database_available() -> bool:
    return db.db_path().exists()


def _frame(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = db.connect()
    try:
        rows = db.query(conn, sql, params)
        cols = [d[0] for d in conn.execute(sql, params).description]
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=cols)


def headline_metrics() -> dict:
    df = _frame(
        "SELECT COUNT(*) AS events, "
        "       ROUND(AVG(delay_min), 2) AS mean_delay, "
        "       ROUND(100.0 * AVG(CASE WHEN ABS(delay_min) <= ? THEN 1 ELSE 0 END), 1) AS on_time_pct, "
        "       COUNT(DISTINCT operator) AS operators, "
        "       COUNT(DISTINCT line) AS lines "
        "FROM fact_delay_event",
        (ON_TIME_TOL_MIN,),
    )
    return df.iloc[0].to_dict()


def operator_summary(min_events: int = 500) -> pd.DataFrame:
    return _frame(
        "SELECT f.operator, o.operator_name, COUNT(*) AS events, "
        "       ROUND(AVG(f.delay_min), 2) AS mean_delay, "
        "       ROUND(100.0 * AVG(CASE WHEN ABS(f.delay_min) <= ? THEN 1 ELSE 0 END), 1) AS on_time_pct "
        "FROM fact_delay_event f JOIN dim_operator o ON f.operator = o.operator "
        "GROUP BY f.operator, o.operator_name HAVING COUNT(*) >= ? "
        "ORDER BY on_time_pct DESC",
        (ON_TIME_TOL_MIN, min_events),
    )


def line_summary(operator: str, min_events: int = 50) -> pd.DataFrame:
    """Per-line reliability for one operator. `operator` is always bound, never interpolated."""
    return _frame(
        "SELECT line, COUNT(*) AS events, ROUND(AVG(delay_min), 2) AS mean_delay, "
        "       ROUND(100.0 * AVG(CASE WHEN ABS(delay_min) <= ? THEN 1 ELSE 0 END), 1) AS on_time_pct "
        "FROM fact_delay_event WHERE operator = ? "
        "GROUP BY line HAVING COUNT(*) >= ? ORDER BY mean_delay DESC",
        (ON_TIME_TOL_MIN, operator, min_events),
    )


def delay_by_hour(operator: str | None = None, min_events: int = 200) -> pd.DataFrame:
    if operator:
        return _frame(
            "SELECT (sched_sec / 3600) % 24 AS sched_hour, COUNT(*) AS events, "
            "       ROUND(AVG(delay_min), 2) AS mean_delay FROM fact_delay_event "
            "WHERE operator = ? GROUP BY sched_hour HAVING COUNT(*) >= ? ORDER BY sched_hour",
            (operator, min_events),
        )
    return _frame(
        "SELECT (sched_sec / 3600) % 24 AS sched_hour, COUNT(*) AS events, "
        "       ROUND(AVG(delay_min), 2) AS mean_delay FROM fact_delay_event "
        "GROUP BY sched_hour HAVING COUNT(*) >= ? ORDER BY sched_hour",
        (min_events,),
    )


def worst_stops(operator: str, limit: int = 15) -> pd.DataFrame:
    return _frame(
        "SELECT s.stop_name, f.stop_sequence, COUNT(*) AS events, "
        "       ROUND(AVG(f.delay_min), 2) AS mean_delay "
        "FROM fact_delay_event f JOIN dim_stop s ON f.stop_id = s.stop_id "
        "WHERE f.operator = ? GROUP BY s.stop_name, f.stop_sequence "
        "HAVING COUNT(*) >= 30 ORDER BY mean_delay DESC LIMIT ?",
        (operator, limit),
    )


def model_comparison() -> pd.DataFrame | None:
    if not MODEL_CSV.exists():
        return None
    return pd.read_csv(MODEL_CSV)


def figure(name: str) -> Path | None:
    path = FIG_DIR / name
    return path if path.exists() else None
