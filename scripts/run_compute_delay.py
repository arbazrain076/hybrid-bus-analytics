"""Computes observed delay events by matching AVL positions to the scheduled timetable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from processing.compute_delay import compute_delay_events, write_delay_events  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    events = compute_delay_events(spark).cache()

    n = events.count()
    print(f"Delay events: {n}")
    events.select(
        F.round(F.mean("delay_min"), 2).alias("mean_delay_min"),
        F.round(F.expr("percentile_approx(delay_min, 0.5)"), 2).alias("median_delay_min"),
        F.round(F.stddev("delay_min"), 2).alias("std_delay_min"),
        F.round(F.min("delay_min"), 2).alias("min"),
        F.round(F.max("delay_min"), 2).alias("max"),
    ).show(truncate=False)
    on_time = events.filter((F.col("delay_min") >= -1) & (F.col("delay_min") <= 5.99)).count()
    tail = events.filter(F.col("delay_min") > 20).count()
    print(f"On-time [-1,+5.99] min: {on_time} ({100*on_time/n:.1f}%)  |  >20 min tail: {tail} ({100*tail/n:.1f}%)")
    events.select("operator", "line", "trip_id", "stop_sequence", "dist_m", "delay_min").show(8, truncate=False)

    write_delay_events(events)
    events.unpersist()
    spark.stop()
    print("Delay computation complete.")


if __name__ == "__main__":
    main()
