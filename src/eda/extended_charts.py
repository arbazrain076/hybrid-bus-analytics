"""Extended exploratory and model-evaluation charts.

Complements `visualize.py` with the descriptive-statistics profile, correlation structure, spatial
distribution and model-comparison views used in the report's Results section. Aggregations run in PySpark
and only the small aggregate results are converted to pandas for plotting.

Domain-metric values are read from `evaluation.domain_metrics` rather than hard-coded, so the chart can
never drift from the computed result.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from pyspark.sql import DataFrame, SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from evaluation.domain_metrics import ON_TIME_TOL_MIN, TTV_CV_TARGET  # noqa: E402
from evaluation.domain_metrics import SERVICE_RELIABILITY_TARGET  # noqa: E402

BASE = Path(__file__).resolve().parent.parent.parent
DELAY_EVENTS = BASE / "data" / "processed" / "silver" / "delay_events"
MODEL_CSV = BASE / "outputs" / "model_comparison.csv"
FIG_DIR = BASE / "outputs" / "figures"

NAVY = "#1F3A5F"
BLUE = "#2E6DA4"
TEAL = "#2E8B8B"
ORANGE = "#D97A34"
GREEN = "#3F8F5B"
RED = "#B03A3A"
GREY = "#6B7280"

MIN_EVENTS_PER_GROUP = 200  # below this a group mean is sampling noise rather than signal
sns.set_theme(style="whitegrid")


def _save(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def describe_delay(df: DataFrame) -> dict:
    """Descriptive statistics for the target, including shape measures."""
    row = df.select(
        F.count("delay_min").alias("n"),
        F.mean("delay_min").alias("mean"),
        F.expr("percentile_approx(delay_min, 0.5)").alias("median"),
        F.stddev("delay_min").alias("std"),
        F.skewness("delay_min").alias("skewness"),
        F.kurtosis("delay_min").alias("kurtosis"),
        F.expr("percentile_approx(delay_min, 0.25)").alias("q1"),
        F.expr("percentile_approx(delay_min, 0.75)").alias("q3"),
        F.min("delay_min").alias("min"),
        F.max("delay_min").alias("max"),
    ).collect()[0].asDict()
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}


def plot_delay_by_stop_sequence(df: DataFrame) -> None:
    pdf = (
        df.filter(F.col("stop_sequence") <= 40)
        .groupBy("stop_sequence")
        .agg(F.mean("delay_min").alias("mean_delay"), F.count("*").alias("n"))
        .filter(F.col("n") >= MIN_EVENTS_PER_GROUP)
        .orderBy("stop_sequence").toPandas()
    )
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    sns.lineplot(data=pdf, x="stop_sequence", y="mean_delay", marker="o", ms=4, color=ORANGE, ax=ax)
    ax.axhline(0, color=GREY, ls="--", lw=1)
    ax.set(title="Mean delay by position along the journey",
           xlabel="Stop sequence (position along route)", ylabel="Mean delay (min)")
    _save(fig, "eda_delay_by_stop_sequence.png")


def plot_delay_by_day(df: DataFrame) -> None:
    pdf = (
        df.filter((F.col("delay_min") >= -10) & (F.col("delay_min") <= 30))
        .select("service_date", "delay_min").toPandas()
    )
    pdf["Service day"] = pdf["service_date"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    sns.kdeplot(data=pdf, x="delay_min", hue="Service day", fill=True, alpha=.35,
                palette=[BLUE, TEAL], ax=ax)
    ax.axvline(0, color=GREY, ls="--", lw=1)
    ax.set(title="Delay distribution across service days", xlabel="Delay (minutes)", ylabel="Density")
    _save(fig, "eda_delay_by_day.png")


def plot_ontime_by_operator(df: DataFrame, min_events: int = 500) -> None:
    pdf = (
        df.groupBy("operator")
        .agg(F.count("*").alias("n"),
             (100 * F.mean((F.abs(F.col("delay_min")) <= ON_TIME_TOL_MIN).cast("int"))).alias("on_time_pct"))
        .filter(F.col("n") >= min_events).orderBy(F.desc("on_time_pct")).toPandas()
    )
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    sns.barplot(data=pdf, y="operator", x="on_time_pct", color=GREEN, ax=ax)
    ax.axvline(SERVICE_RELIABILITY_TARGET, color=RED, ls="--", lw=1.6)
    ax.text(SERVICE_RELIABILITY_TARGET, -0.7, f" target {SERVICE_RELIABILITY_TARGET:.0f}%",
            color=RED, fontsize=8.5, va="center")
    ax.set(title=f"Service Reliability by operator (% within +/-{ON_TIME_TOL_MIN:.0f} min)",
           xlabel="On-time arrivals (%)", ylabel="Operator", xlim=(0, SERVICE_RELIABILITY_TARGET + 7))
    _save(fig, "eda_ontime_by_operator.png")


def plot_correlation(df: DataFrame, sample_fraction: float = 0.25, seed: int = 42) -> None:
    cols = ["delay_min", "stop_sequence", "sched_hour", "stop_lat", "stop_lon", "direction_id"]
    pdf = df.select(*cols).sample(False, sample_fraction, seed=seed).toPandas()
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    sns.heatmap(pdf.corr(numeric_only=True), annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax)
    ax.set_title("Correlation between delay and model features", fontsize=12,
                 fontweight="bold", color=NAVY, pad=12)
    fig.tight_layout()
    _save(fig, "eda_correlation.png")


def plot_spatial_delay(df: DataFrame, min_events: int = 100) -> None:
    pdf = (
        df.withColumn("lat", F.round("stop_lat", 2)).withColumn("lon", F.round("stop_lon", 2))
        .groupBy("lat", "lon")
        .agg(F.mean("delay_min").alias("mean_delay"), F.count("*").alias("n"))
        .filter(F.col("n") >= min_events).toPandas()
    )
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    sc = ax.scatter(pdf["lon"], pdf["lat"], c=pdf["mean_delay"], s=pdf["n"] / 25,
                    cmap="RdYlGn_r", vmin=0, vmax=10, edgecolor="white", linewidth=.4)
    fig.colorbar(sc, ax=ax, shrink=.85).set_label("Mean delay (minutes)")
    ax.set(title="Spatial distribution of delay", xlabel="Longitude", ylabel="Latitude")
    ax.title.set_color(NAVY); ax.title.set_fontweight("bold")
    fig.tight_layout()
    _save(fig, "eda_spatial_delay.png")


def plot_model_error() -> None:
    m = pd.read_csv(MODEL_CSV)
    long = m.melt(id_vars="model", value_vars=["rmse", "mae"], var_name="Metric", value_name="Minutes")
    long["Metric"] = long["Metric"].str.upper()
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    sns.barplot(data=long, x="model", y="Minutes", hue="Metric", palette=[BLUE, TEAL], ax=ax)
    ax.set(title="Prediction error by model (lower is better)", xlabel="", ylabel="Error (minutes)")
    ax.tick_params(axis="x", rotation=15)
    _save(fig, "metrics_error_by_model.png")


def plot_accuracy_vs_cost() -> None:
    m = pd.read_csv(MODEL_CSV)
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ax.scatter(m["train_time_s"], m["r2"], s=140, color=BLUE, zorder=3)
    for _, r in m.iterrows():
        ax.annotate(r["model"], (r["train_time_s"], r["r2"]), textcoords="offset points",
                    xytext=(8, 6), fontsize=8.5, color=NAVY)
    ax.set(title="Accuracy versus training cost", xlabel="Training time (seconds)",
           ylabel="R2 (variance explained)")
    _save(fig, "metrics_accuracy_vs_cost.png")


def plot_domain_vs_target(service_reliability_pct: float, median_cv: float) -> None:
    """Observed domain metrics against the brief's targets. Values are passed in, never hard-coded."""
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.5))
    for ax, obs, target, title, ylab, top in [
        (axes[0], service_reliability_pct, SERVICE_RELIABILITY_TARGET,
         "Service Reliability (%)", f"% within +/-{ON_TIME_TOL_MIN:.0f} min", 100),
        (axes[1], median_cv, TTV_CV_TARGET,
         "Travel Time Variability (CV)", "Coefficient of variation", max(median_cv, TTV_CV_TARGET) * 1.4),
    ]:
        ax.bar(["Observed", "Target"], [obs, target], color=[ORANGE, GREY])
        ax.set(title=title, ylabel=ylab, ylim=(0, top))
        for i, v in enumerate([obs, target]):
            ax.text(i, v + top * 0.02, f"{v}", ha="center", fontsize=9.5,
                    fontweight="bold", color=NAVY)
    fig.suptitle("Domain reliability metrics against brief targets", fontsize=12,
                 fontweight="bold", color=NAVY)
    fig.tight_layout()
    _save(fig, "metrics_domain_vs_target.png")


def run(spark: SparkSession) -> dict:
    """Builds every extended chart and returns the descriptive statistics."""
    from evaluation.domain_metrics import service_reliability, travel_time_variability

    df = (spark.read.parquet(str(DELAY_EVENTS))
          .withColumn("sched_hour", (F.col("sched_sec") / 3600).cast("int") % 24)).cache()

    stats = describe_delay(df)
    plot_delay_by_stop_sequence(df)
    plot_delay_by_day(df)
    plot_ontime_by_operator(df)
    plot_correlation(df)
    plot_spatial_delay(df)

    if MODEL_CSV.exists():
        plot_model_error()
        plot_accuracy_vs_cost()
    plot_domain_vs_target(service_reliability(df)["on_time_pct"],
                          travel_time_variability(df)["median_cv"])

    df.unpersist()
    return stats
