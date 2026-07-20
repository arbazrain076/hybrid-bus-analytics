"""Loads the North West GTFS feed, filters to Greater Manchester, and writes the silver layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from ingestion.load_gtfs import load_greater_manchester_gtfs, write_silver  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    tables = load_greater_manchester_gtfs(spark)
    write_silver(tables)
    spark.stop()
    print("GTFS ingestion complete.")


if __name__ == "__main__":
    main()
