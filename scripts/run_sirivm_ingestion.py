"""Parses SIRI-VM snapshots and filters to Greater Manchester.

Usage: python scripts/run_sirivm_ingestion.py [sample_every_nth]
Pass a sample_every_nth > 1 to subsample snapshots (e.g. 100 for a quick check across the whole day
instead of parsing all 2,761 files).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from ingestion.load_sirivm import load_greater_manchester_sirivm  # noqa: E402

SILVER_DIR = Path(__file__).resolve().parent.parent / "data" / "processed" / "silver" / "sirivm_gm"


def main() -> None:
    sample_every_nth = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    spark = get_spark_session()
    df = load_greater_manchester_sirivm(spark, sample_every_nth=sample_every_nth)
    df.cache()

    count = df.count()
    print(f"sample_every_nth={sample_every_nth} -> Greater Manchester vehicle activity rows: {count}")
    df.show(5, truncate=False)

    df.write.mode("overwrite").parquet(str(SILVER_DIR))
    df.unpersist()
    spark.stop()
    print("SIRI-VM ingestion complete.")


if __name__ == "__main__":
    main()
