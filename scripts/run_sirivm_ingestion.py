"""Parses a day's SIRI-VM snapshots and filters to Greater Manchester.

Usage: python scripts/run_sirivm_ingestion.py <YYYYMMDD> [sample_every_nth]
Writes to data/processed/silver/sirivm_gm/ partitioned by source_date, appending the given day.
Pass sample_every_nth > 1 to subsample snapshots for a quick check.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from ingestion.load_sirivm import load_greater_manchester_sirivm  # noqa: E402

SILVER_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "silver" / "sirivm_gm"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: run_sirivm_ingestion.py <YYYYMMDD> [sample_every_nth]")
    date_str = sys.argv[1]
    sample_every_nth = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    spark = get_spark_session()
    # Dynamic overwrite: re-running one day replaces only that day's partition, leaving other days intact.
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

    df = load_greater_manchester_sirivm(spark, date_str, sample_every_nth=sample_every_nth)
    df.cache()

    count = df.count()
    print(f"{date_str} (sample_every_nth={sample_every_nth}) -> Greater Manchester rows: {count}")

    df.write.mode("overwrite").partitionBy("source_date").parquet(str(SILVER_DIR))
    df.unpersist()
    spark.stop()
    print("SIRI-VM ingestion complete.")


if __name__ == "__main__":
    main()
