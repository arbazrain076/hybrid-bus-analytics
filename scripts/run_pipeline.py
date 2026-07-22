"""Runs the full pipeline end to end, in dependency order.

Each stage is independently re-runnable, so the orchestrator exists to guarantee ordering and to give a
single reproducible entry point rather than to add new behaviour. Stages read and write the same paths
the individual scripts use.

Usage:
    python scripts/run_pipeline.py                     # run every stage
    python scripts/run_pipeline.py --dry-run           # list the stages without executing
    python scripts/run_pipeline.py --from compute_delay  # resume from a named stage
    python scripts/run_pipeline.py --only ml           # run one stage
"""

import argparse
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

SERVICE_DAYS = ["20260630", "20260701"]


def _ingest_gtfs(spark):
    from ingestion.load_gtfs import load_greater_manchester_gtfs, write_silver

    write_silver(load_greater_manchester_gtfs(spark))


def _ingest_sirivm(spark):
    from ingestion.load_sirivm import load_greater_manchester_sirivm

    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    out = BASE / "data" / "processed" / "silver" / "sirivm_gm"
    for day in SERVICE_DAYS:
        df = load_greater_manchester_sirivm(spark, day)
        df.write.mode("overwrite").partitionBy("source_date").parquet(str(out))


def _compute_delay(spark):
    from processing.compute_delay import compute_delay_events, write_delay_events

    write_delay_events(compute_delay_events(spark))


def _load_database(spark):
    import subprocess

    subprocess.run([sys.executable, str(BASE / "scripts" / "load_db.py")], check=True)


def _train_models(spark):
    from ml.train import run

    for row in run(spark):
        print("   ", row)


def _domain_metrics(spark):
    from evaluation.domain_metrics import run

    print("   ", run(spark)["service_reliability"])


def _visualise(spark):
    from eda.extended_charts import run as extended
    from eda.visualize import run as basic

    basic(spark)
    extended(spark)


STAGES = [
    ("gtfs", "Ingest GTFS timetables and filter to Greater Manchester", _ingest_gtfs),
    ("sirivm", "Parse SIRI-VM snapshots for each service day", _ingest_sirivm),
    ("compute_delay", "Reconstruct observed delay and clean inconsistent journeys", _compute_delay),
    ("database", "Load the relational store with parameterised batch inserts", _load_database),
    ("ml", "Train and compare the regression models", _train_models),
    ("metrics", "Compute domain reliability metrics", _domain_metrics),
    ("figures", "Generate EDA and evaluation figures", _visualise),
]


def main() -> None:
    names = [name for name, _, _ in STAGES]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="list stages without running them")
    parser.add_argument("--from", dest="start", choices=names, help="resume from this stage")
    parser.add_argument("--only", choices=names, help="run a single stage")
    args = parser.parse_args()

    selected = STAGES
    if args.only:
        selected = [s for s in STAGES if s[0] == args.only]
    elif args.start:
        selected = STAGES[names.index(args.start):]

    if args.dry_run:
        for i, (name, description, _) in enumerate(selected, 1):
            print(f"{i}. {name:<14} {description}")
        return

    from config.spark_session import get_spark_session

    spark = get_spark_session("full-pipeline")
    try:
        for i, (name, description, fn) in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] {name} - {description}")
            started = time.perf_counter()
            fn(spark)
            print(f"    done in {time.perf_counter() - started:.1f}s")
    finally:
        spark.stop()
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
