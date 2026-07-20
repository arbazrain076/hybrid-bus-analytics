"""Profiles the silver-layer datasets and validates the AVL-to-timetable join keys.

The SIRI-VM (AVL) and GTFS (timetable) feeds use different journey identifiers, so observed delay can't be
derived from a direct trip_id join. This module quantifies how the two feeds line up on the keys the delay
computation relies on: operator (SIRI `operator_ref` vs GTFS `agency_noc`) and line (SIRI `line_ref` vs
GTFS `route_short_name`). It reports feed volumes, deduplication headroom, and operator/line match rates.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

BASE = Path(__file__).resolve().parent.parent.parent
SILVER = BASE / "data" / "processed" / "silver"
AGENCY_CSV = BASE / "data" / "raw" / "timetables" / "north_west_gtfs" / "agency.txt"


def profile_sirivm(siri: DataFrame) -> dict:
    return {
        "total_pings": siri.count(),
        "distinct_positions": siri.select(
            "vehicle_ref", "recorded_at", "line_ref", "latitude", "longitude"
        ).distinct().count(),
        "distinct_journeys": siri.select(
            "vehicle_ref", "line_ref", "origin_aimed_departure"
        ).distinct().count(),
        "distinct_operators": siri.select("operator_ref").distinct().count(),
        "distinct_lines": siri.select("line_ref").distinct().count(),
    }


def profile_join_keys(spark: SparkSession, siri: DataFrame) -> dict:
    routes = spark.read.parquet(str(SILVER / "gtfs_gm" / "routes"))
    agency = spark.read.csv(str(AGENCY_CSV), header=True).select("agency_id", "agency_noc")

    siri_ops = {r.operator_ref for r in siri.select("operator_ref").distinct().collect()}
    gtfs_nocs = {r.agency_noc for r in agency.select("agency_noc").distinct().collect()}

    routes_noc = routes.join(agency, on="agency_id", how="left").select(
        F.col("agency_noc").alias("operator_ref"),
        F.col("route_short_name").alias("line_ref"),
    ).distinct()

    siri_pairs = siri.select("operator_ref", "line_ref").distinct()
    total_pairs = siri_pairs.count()
    matched_pairs = siri_pairs.join(routes_noc, on=["operator_ref", "line_ref"], how="inner").count()

    return {
        "siri_operators": len(siri_ops),
        "gtfs_nocs": len(gtfs_nocs),
        "operator_overlap": len(siri_ops & gtfs_nocs),
        "siri_only_operators": sorted(siri_ops - gtfs_nocs),
        "siri_op_line_pairs": total_pairs,
        "matched_op_line_pairs": matched_pairs,
        "match_rate_pct": round(100 * matched_pairs / total_pairs, 1) if total_pairs else 0.0,
    }


def run(spark: SparkSession) -> dict:
    siri = spark.read.parquet(str(SILVER / "sirivm_gm"))
    profile = profile_sirivm(siri)
    keys = profile_join_keys(spark, siri)
    return {"sirivm": profile, "join_keys": keys}
