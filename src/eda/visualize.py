"""Business-problem visualisations for the delay analysis.

Aggregations are computed in PySpark, then the small aggregate results are converted to pandas for
matplotlib/seaborn plotting (a justified small-data conversion - each aggregate is <=24 or <=18 rows;
the delay-distribution sample is a single column). Figures are saved as PNGs under outputs/figures/.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: save PNGs without a display.
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

BASE = Path(__file__).resolve().parent.parent.parent
DELAY_EVENTS = BASE / "data" / "processed" / "silver" / "delay_events"
MODEL_CSV = BASE / "outputs" / "model_comparison.csv"
FIG_DIR = BASE / "outputs" / "figures"

sns.set_theme(style="whitegrid")


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name, dpi=120, bbox_inches="tight")
    plt.close(fig)


def plot_delay_distribution(spark: SparkSession) -> None:
    pdf = (
        spark.read.parquet(str(DELAY_EVENTS))
        .select("delay_min")
        .filter((F.col("delay_min") >= -10) & (F.col("delay_min") <= 40))
        .toPandas()
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(pdf["delay_min"], bins=50, ax=ax, color="#3b7dd8")
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.set(title="Distribution of observed bus delay (Greater Manchester)",
           xlabel="Delay (minutes; negative = early)", ylabel="Arrival events")
    _save(fig, "delay_distribution.png")


# Early-morning hours have very few matched events (e.g. 04:00 has ~8), so their mean is noise. Restrict
# the hourly profile to adequately-sampled hours to avoid a misleading small-sample spike.
MIN_HOUR_EVENTS = 200


def plot_delay_by_hour(spark: SparkSession) -> None:
    pdf = (
        spark.read.parquet(str(DELAY_EVENTS))
        .withColumn("sched_hour", (F.col("sched_sec") / 3600).cast("int") % 24)
        .groupBy("sched_hour").agg(F.mean("delay_min").alias("mean_delay"), F.count("*").alias("n"))
        .filter(F.col("n") >= MIN_HOUR_EVENTS)
        .orderBy("sched_hour").toPandas()
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.lineplot(data=pdf, x="sched_hour", y="mean_delay", marker="o", ax=ax, color="#d8763b")
    ax.set(title=f"Mean delay by scheduled hour (hours with >={MIN_HOUR_EVENTS} events)",
           xlabel="Scheduled hour", ylabel="Mean delay (min)")
    _save(fig, "delay_by_hour.png")


def plot_delay_by_operator(spark: SparkSession, top_n: int = 15) -> None:
    pdf = (
        spark.read.parquet(str(DELAY_EVENTS))
        .groupBy("operator").agg(F.mean("delay_min").alias("mean_delay"), F.count("*").alias("n"))
        .filter(F.col("n") >= 500).orderBy(F.desc("mean_delay")).limit(top_n).toPandas()
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(data=pdf, y="operator", x="mean_delay", ax=ax, color="#3bd88a")
    ax.set(title=f"Mean delay by operator (top {top_n}, >=500 events)",
           xlabel="Mean delay (min)", ylabel="Operator")
    _save(fig, "delay_by_operator.png")


def plot_model_comparison() -> None:
    pdf = pd.read_csv(MODEL_CSV)
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(data=pdf, x="model", y="rmse", ax=ax, color="#b03bd8")
    ax.set(title="Model comparison — test RMSE (lower is better)", xlabel="", ylabel="RMSE (min)")
    ax.tick_params(axis="x", rotation=20)
    _save(fig, "model_rmse.png")


def run(spark: SparkSession) -> list[str]:
    plot_delay_distribution(spark)
    plot_delay_by_hour(spark)
    plot_delay_by_operator(spark)
    if MODEL_CSV.exists():
        plot_model_comparison()
    return [str(p.name) for p in sorted(FIG_DIR.glob("*.png"))]
