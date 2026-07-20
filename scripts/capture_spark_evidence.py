"""Captures Spark evidence for the report: partition counts, broadcast join, and the query plan/DAG.

Runs a representative pipeline stage over the delay-event table and records:
- partition count before/after an explicit repartition (repartitioning evidence),
- a broadcast() join with a small lookup (broadcast-join evidence, visible as BroadcastHashJoin in the
  plan), with cache()/unpersist() around the reused DataFrame,
- the .explain(True) query plan (lazy-evaluation / DAG evidence per the pyspark skill),
written to outputs/spark_evidence/.

Optional: pass --hold SECONDS to keep the SparkSession (and its UI at http://localhost:4040) alive so a
Spark UI screenshot of partition/stage utilisation can be captured for the report. The screenshot itself
must be taken manually - the UI only exists while the session runs.
"""

import io
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyspark.sql import functions as F  # noqa: E402
from pyspark.sql.functions import broadcast  # noqa: E402

from config.spark_session import get_spark_session  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
DELAY_EVENTS = BASE / "data" / "processed" / "silver" / "delay_events"
OUT_DIR = BASE / "outputs" / "spark_evidence"


def main() -> None:
    hold_s = 0
    if "--hold" in sys.argv:
        hold_s = int(sys.argv[sys.argv.index("--hold") + 1])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spark = get_spark_session("spark-evidence")

    df = spark.read.parquet(str(DELAY_EVENTS))
    before = df.rdd.getNumPartitions()

    df = df.repartition(16, "operator").cache()
    df.count()  # materialise the cache
    after = df.rdd.getNumPartitions()

    # Small per-operator lookup -> broadcast join (BroadcastHashJoin in the plan).
    op_counts = df.groupBy("operator").count().withColumnRenamed("count", "operator_events")
    joined = df.join(broadcast(op_counts), on="operator", how="inner")
    agg = joined.groupBy("operator").agg(F.mean("delay_min").alias("mean_delay"))

    plan = io.StringIO()
    with redirect_stdout(plan):
        agg.explain(True)
    (OUT_DIR / "explain_plan.txt").write_text(plan.getvalue())

    result_rows = agg.count()
    df.unpersist()

    summary = (
        f"Partitions before repartition: {before}\n"
        f"Partitions after repartition(16): {after}\n"
        f"Broadcast join produced aggregated rows: {result_rows}\n"
        f"Query plan saved: {OUT_DIR / 'explain_plan.txt'}\n"
        f"BroadcastHashJoin present in plan: "
        f"{'BroadcastHashJoin' in (OUT_DIR / 'explain_plan.txt').read_text()}\n"
    )
    (OUT_DIR / "summary.txt").write_text(summary)
    print(summary)

    if hold_s > 0:
        print(f"Spark UI at http://localhost:4040 - holding {hold_s}s for a screenshot...")
        time.sleep(hold_s)

    spark.stop()


if __name__ == "__main__":
    main()
