"""Loads the cleaned analysis data from silver Parquet into the relational database (see ADR-005).

Dimensions are loaded before the fact table so the foreign keys resolve. All inserts are parameterised
batch executemany calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyspark.sql import functions as F  # noqa: E402

from config.spark_session import get_spark_session  # noqa: E402
from database.db import apply_schema, batch_insert, connect  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
SILVER = BASE / "data" / "processed" / "silver"
AGENCY_CSV = BASE / "data" / "raw" / "timetables" / "north_west_gtfs" / "agency.txt"

FACT_COLS = [
    "service_date", "operator", "line", "direction_id", "trip_id",
    "stop_id", "stop_sequence", "sched_sec", "ping_sec", "delay_min",
]


def main() -> None:
    spark = get_spark_session()
    delay = spark.read.parquet(str(SILVER / "delay_events"))
    stops = spark.read.parquet(str(SILVER / "gtfs_gm" / "stops"))
    agency = spark.read.csv(str(AGENCY_CSV), header=True)

    # dim_operator: operators present in the fact, with names where available.
    operators = (
        delay.select("operator").distinct()
        .join(agency.select(F.col("agency_noc").alias("operator"), F.col("agency_name").alias("operator_name")),
              on="operator", how="left")
        .select("operator", "operator_name")
    )
    # dim_stop: stops present in the fact, with name/location.
    dim_stops = (
        delay.select("stop_id").distinct()
        .join(stops.select("stop_id", "stop_name", "stop_lat", "stop_lon"), on="stop_id", how="left")
    )

    fact = delay.select(*FACT_COLS)

    conn = connect()
    apply_schema(conn)

    n_op = batch_insert(
        conn, "INSERT INTO dim_operator (operator, operator_name) VALUES (?, ?)",
        ((r.operator, r.operator_name) for r in operators.toLocalIterator()),
    )
    n_stop = batch_insert(
        conn, "INSERT INTO dim_stop (stop_id, stop_name, stop_lat, stop_lon) VALUES (?, ?, ?, ?)",
        ((r.stop_id, r.stop_name, r.stop_lat, r.stop_lon) for r in dim_stops.toLocalIterator()),
    )
    n_fact = batch_insert(
        conn,
        "INSERT INTO fact_delay_event "
        "(service_date, operator, line, direction_id, trip_id, stop_id, stop_sequence, "
        "sched_sec, ping_sec, delay_min) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (tuple(r[c] for c in FACT_COLS) for r in fact.toLocalIterator()),
    )

    print(f"Loaded: dim_operator={n_op}, dim_stop={n_stop}, fact_delay_event={n_fact}")
    conn.close()
    spark.stop()
    print("DB load complete.")


if __name__ == "__main__":
    main()
