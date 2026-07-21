"""Maps the reconstructed delay data onto the brief's transport-domain reliability metrics.

Definitions (per the assignment brief's metric table):
- Service Reliability: % of arrivals within +/-2 min (urban) of schedule; target >=85%.
- Travel Time Variability (TTV): coefficient of variation (CV = std/mean) of observed trip duration;
  target CV <=15%. This is the natural domain target for the delay-regression model.

Both are computed from the actual observed data (not model predictions), so the report can state the
network's real reliability alongside the model's predictive accuracy.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

BASE = Path(__file__).resolve().parent.parent.parent
DELAY_EVENTS = BASE / "data" / "processed" / "silver" / "delay_events"

ON_TIME_TOL_MIN = 2.0          # +/-2 min urban window
SERVICE_RELIABILITY_TARGET = 85.0  # percent
TTV_CV_TARGET = 0.15           # 15%
MIN_STOPS_PER_TRIP = 3         # need a few matched stops to define a trip duration
MIN_TRIPS_PER_ROUTE = 20       # need enough trips to estimate a route's CV

JOURNEY_KEY = ["service_date", "trip_id", "vehicle_ref", "origin_aimed_departure"]


def service_reliability(df: DataFrame) -> dict:
    total = df.count()
    on_time = df.filter(F.abs(F.col("delay_min")) <= ON_TIME_TOL_MIN).count()
    pct = round(100 * on_time / total, 1)
    return {"events": total, "on_time_pct": pct, "target_pct": SERVICE_RELIABILITY_TARGET,
            "meets_target": pct >= SERVICE_RELIABILITY_TARGET}


def service_reliability_by_operator(df: DataFrame) -> DataFrame:
    return (
        df.groupBy("operator")
        .agg(
            F.count("*").alias("events"),
            F.round(100 * F.mean((F.abs(F.col("delay_min")) <= ON_TIME_TOL_MIN).cast("int")), 1)
            .alias("on_time_pct"),
        )
        .filter(F.col("events") >= 500)
        .orderBy(F.desc("on_time_pct"))
    )


def travel_time_variability(df: DataFrame) -> dict:
    """CV of observed trip duration per (line, direction), summarised across routes."""
    # Observed journey duration = span of actual times across a journey's matched stops.
    journeys = (
        df.groupBy(*JOURNEY_KEY, "line", "direction_id")
        .agg(
            (F.max("ping_sec") - F.min("ping_sec")).alias("obs_duration_s"),
            F.count("*").alias("n_stops"),
        )
        .filter((F.col("n_stops") >= MIN_STOPS_PER_TRIP) & (F.col("obs_duration_s") > 0))
    )
    route_cv = (
        journeys.groupBy("line", "direction_id")
        .agg(
            F.count("*").alias("n_trips"),
            F.mean("obs_duration_s").alias("mean_dur"),
            F.stddev("obs_duration_s").alias("sd_dur"),
        )
        .filter(F.col("n_trips") >= MIN_TRIPS_PER_ROUTE)
        .withColumn("cv", F.col("sd_dur") / F.col("mean_dur"))
    )
    n_routes = route_cv.count()
    median_cv = route_cv.approxQuantile("cv", [0.5], 0.01)[0] if n_routes else None
    meets = route_cv.filter(F.col("cv") <= TTV_CV_TARGET).count()
    return {
        "routes_assessed": n_routes,
        "median_cv": round(median_cv, 3) if median_cv is not None else None,
        "target_cv": TTV_CV_TARGET,
        "pct_routes_meeting_target": round(100 * meets / n_routes, 1) if n_routes else None,
    }


def run(spark: SparkSession) -> dict:
    df = spark.read.parquet(str(DELAY_EVENTS)).cache()
    sr = service_reliability(df)
    ttv = travel_time_variability(df)
    by_op = [r.asDict() for r in service_reliability_by_operator(df).collect()]
    return {"service_reliability": sr, "travel_time_variability": ttv, "by_operator": by_op}
