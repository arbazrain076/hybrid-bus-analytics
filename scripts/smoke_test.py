"""Verifies the Spark environment is working before any real pipeline code is written."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import MIN_PARTITIONS, get_spark_session  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    print(f"Spark version: {spark.version}")

    df = spark.range(0, 1000).repartition(MIN_PARTITIONS)
    partitions = df.rdd.getNumPartitions()
    total = df.count()

    print(f"Partitions: {partitions}")
    print(f"Row count: {total}")

    assert partitions >= 4, "Project requires >=4 partitions"
    assert total == 1000

    spark.stop()
    print("Smoke test passed.")


if __name__ == "__main__":
    main()
