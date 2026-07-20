"""Derives observed bus delay by matching AVL positions to the scheduled timetable.

The SIRI-VM feed carries no delay field, so delay is reconstructed in three stages:

1. Resolve which GTFS services (and therefore trips) actually run on the service date, using calendar.txt
   day-of-week flags plus calendar_dates.txt exceptions.
2. Pin each observed vehicle-journey to a specific GTFS trip via the scheduled *origin departure time*
   (SIRI `origin_aimed_departure` == the trip's first-stop departure), keyed by operator + line. This is
   robust to lateness: a bus 30 minutes behind is still matched to its correct trip, because the match
   uses the *scheduled* origin time, not the live position.
3. For each ping of a pinned journey, snap to the nearest stop *on that trip* (haversine, within a
   threshold) and take delay = actual local time at the ping minus the stop's scheduled time.

Timezone: SIRI `recorded_at`/`origin_aimed_departure` are UTC; GTFS times are Europe/London local. All
comparisons are done in local seconds-since-midnight via from_utc_timestamp, so BST is handled correctly.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

BASE = Path(__file__).resolve().parent.parent.parent
SILVER = BASE / "data" / "processed" / "silver"
GTFS_RAW = BASE / "data" / "raw" / "timetables" / "north_west_gtfs"
OUT_DIR = SILVER / "delay_events"

# Service days to process. Each is (YYYYMMDD, gtfs_weekday_column). The GTFS timetable snapshot
# (calendar valid 2026-06-30 onward) covers both days, so it is reused across them.
SERVICE_DAYS = [
    ("20260701", "wednesday"),
    ("20260630", "tuesday"),
]
LOCAL_TZ = "Europe/London"

# Match tolerances.
ORIGIN_MATCH_TOL_SEC = 120  # journey<->trip origin-departure alignment
STOP_SNAP_MAX_M = 120.0  # a ping counts as "at" a stop within this distance
DELAY_MIN_CLAMP, DELAY_MAX_CLAMP = -15.0, 90.0  # minutes; drop implausible matches
MAX_JOURNEY_DELAY_STD = 6.0  # minutes; a journey whose per-stop delays scatter more than this is a match failure


def _gtfs_time_to_seconds(col):
    """Parses a GTFS 'HH:MM:SS' string (hours may exceed 24) into seconds since local midnight."""
    parts = F.split(col, ":")
    return (
        parts.getItem(0).cast("int") * 3600
        + parts.getItem(1).cast("int") * 60
        + parts.getItem(2).cast("int")
    )


def _local_seconds_of_day(utc_ts_col):
    """UTC ISO timestamp string -> seconds since local (Europe/London) midnight."""
    local = F.from_utc_timestamp(F.to_timestamp(utc_ts_col), LOCAL_TZ)
    return F.hour(local) * 3600 + F.minute(local) * 60 + F.second(local)


def _haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    dlat = F.radians(lat2 - lat1)
    dlon = F.radians(lon2 - lon1)
    a = F.sin(dlat / 2) ** 2 + F.cos(F.radians(lat1)) * F.cos(F.radians(lat2)) * F.sin(dlon / 2) ** 2
    return r * 2 * F.asin(F.sqrt(a))


def resolve_active_services(spark: SparkSession, service_date: str, weekday_col: str) -> DataFrame:
    """Returns a single-column DataFrame of service_id values running on service_date.

    weekday_col is the GTFS calendar day-of-week column for that date (e.g. 'wednesday').
    """
    calendar = spark.read.csv(str(GTFS_RAW / "calendar.txt"), header=True)
    cal_dates = spark.read.csv(str(GTFS_RAW / "calendar_dates.txt"), header=True)

    base = calendar.filter(
        (F.col(weekday_col) == "1")
        & (F.col("start_date") <= service_date)
        & (F.col("end_date") >= service_date)
    ).select("service_id")

    added = cal_dates.filter((F.col("date") == service_date) & (F.col("exception_type") == "1")).select("service_id")
    removed = cal_dates.filter((F.col("date") == service_date) & (F.col("exception_type") == "2")).select("service_id")

    return base.union(added).distinct().join(removed, on="service_id", how="left_anti")


def build_trip_schedule(spark: SparkSession, active_services: DataFrame) -> DataFrame:
    """Scheduled stop events for trips running on the service date, with operator/line and local seconds."""
    stops = spark.read.parquet(str(SILVER / "gtfs_gm" / "stops")).select("stop_id", "stop_lat", "stop_lon")
    trips = spark.read.parquet(str(SILVER / "gtfs_gm" / "trips")).select(
        "trip_id", "route_id", "service_id", "direction_id"
    )
    routes = spark.read.parquet(str(SILVER / "gtfs_gm" / "routes")).select(
        "route_id", "route_short_name", "agency_id"
    )
    stop_times = spark.read.parquet(str(SILVER / "gtfs_gm" / "stop_times")).select(
        "trip_id", "stop_id", "arrival_time", "stop_sequence"
    )
    agency = spark.read.csv(str(GTFS_RAW / "agency.txt"), header=True).select(
        "agency_id", F.col("agency_noc").alias("operator")
    )

    active_trips = trips.join(F.broadcast(active_services), on="service_id", how="inner")
    trip_meta = (
        active_trips.join(F.broadcast(routes), on="route_id", how="inner")
        .join(F.broadcast(agency), on="agency_id", how="left")
        .select("trip_id", "direction_id", F.col("route_short_name").alias("line"), "operator")
    )

    return (
        stop_times.join(trip_meta, on="trip_id", how="inner")
        .join(F.broadcast(stops), on="stop_id", how="inner")
        .withColumn("sched_sec", _gtfs_time_to_seconds(F.col("arrival_time")))
        .filter(F.col("sched_sec").isNotNull())
    )


def map_journeys_to_trips(spark: SparkSession, trip_schedule: DataFrame, positions: DataFrame) -> DataFrame:
    """Pins each SIRI journey (operator, line, origin_aimed_departure) to a GTFS trip via origin departure."""
    # Origin (first-stop) scheduled departure per trip.
    w = Window.partitionBy("trip_id").orderBy(F.col("stop_sequence").asc())
    trip_origins = (
        trip_schedule.withColumn("rn", F.row_number().over(w))
        .filter(F.col("rn") == 1)
        .select("trip_id", "operator", "line", F.col("sched_sec").alias("origin_sec"))
    )

    journeys = (
        positions.select("operator_ref", "line_ref", "origin_aimed_departure")
        .distinct()
        .withColumnRenamed("operator_ref", "operator")
        .withColumnRenamed("line_ref", "line")
        .withColumn("journey_origin_sec", _local_seconds_of_day(F.col("origin_aimed_departure")))
        .filter(F.col("journey_origin_sec").isNotNull())
    )

    matched = journeys.join(trip_origins, on=["operator", "line"], how="inner").filter(
        F.abs(F.col("journey_origin_sec") - F.col("origin_sec")) <= ORIGIN_MATCH_TOL_SEC
    )
    # If a journey aligns with several trips, keep the closest origin time.
    jw = Window.partitionBy("operator", "line", "origin_aimed_departure").orderBy(
        F.abs(F.col("journey_origin_sec") - F.col("origin_sec")).asc()
    )
    return (
        matched.withColumn("rn", F.row_number().over(jw))
        .filter(F.col("rn") == 1)
        .select("operator", "line", "origin_aimed_departure", "trip_id")
    )


def compute_delay_events_for_day(spark: SparkSession, service_date: str, weekday_col: str) -> DataFrame:
    """Delay events for a single service day (source_date partition + matching active services)."""
    positions = (
        spark.read.parquet(str(SILVER / "sirivm_gm"))
        .filter(F.col("source_date") == service_date)
        .filter(
            F.to_date(F.from_utc_timestamp(F.to_timestamp("recorded_at"), LOCAL_TZ))
            == F.to_date(F.lit(service_date), "yyyyMMdd")
        )
        .select(
            "operator_ref", "line_ref", "origin_aimed_departure", "vehicle_ref",
            "recorded_at", "latitude", "longitude",
        )
        .distinct()
    )

    active = resolve_active_services(spark, service_date, weekday_col)
    trip_schedule = build_trip_schedule(spark, active).cache()
    journey_trip = map_journeys_to_trips(spark, trip_schedule, positions)

    # Attach trip_id to each ping via the journey key. Rename the journey side first so the shared column
    # names (operator/line/origin_aimed_departure) don't become ambiguous after the join.
    journey_keyed = (
        journey_trip.withColumnRenamed("operator", "j_operator")
        .withColumnRenamed("line", "j_line")
        .withColumnRenamed("origin_aimed_departure", "j_origin")
    )
    pinned = positions.join(
        journey_keyed,
        (positions.operator_ref == journey_keyed.j_operator)
        & (positions.line_ref == journey_keyed.j_line)
        & (positions.origin_aimed_departure == journey_keyed.j_origin),
        how="inner",
    ).select(
        positions.operator_ref.alias("operator"), positions.line_ref.alias("line"),
        positions.origin_aimed_departure.alias("origin_aimed_departure"),
        "vehicle_ref", "recorded_at", "latitude", "longitude", "trip_id",
    )

    trip_stops = trip_schedule.select(
        "trip_id", "stop_id", "stop_sequence", "direction_id",
        F.col("stop_lat"), F.col("stop_lon"), "sched_sec",
    )

    candidates = (
        pinned.join(trip_stops, on="trip_id", how="inner")
        .withColumn("dist_m", _haversine_m(F.col("latitude"), F.col("longitude"), F.col("stop_lat"), F.col("stop_lon")))
        .filter(F.col("dist_m") <= STOP_SNAP_MAX_M)
        .withColumn("ping_sec", _local_seconds_of_day(F.col("recorded_at")))
    )

    # One delay observation per (journey, stop): the ping physically closest to that stop.
    ev = Window.partitionBy("trip_id", "vehicle_ref", "origin_aimed_departure", "stop_id").orderBy(
        F.col("dist_m").asc()
    )
    raw_events = (
        candidates.withColumn("rn", F.row_number().over(ev))
        .filter(F.col("rn") == 1)
        .withColumn("delay_min", (F.col("ping_sec") - F.col("sched_sec")) / 60.0)
        .filter((F.col("delay_min") >= DELAY_MIN_CLAMP) & (F.col("delay_min") <= DELAY_MAX_CLAMP))
        .withColumn("service_date", F.lit(service_date))
        .select(
            "service_date", "operator", "line", "direction_id", "trip_id", "vehicle_ref",
            "origin_aimed_departure", "stop_id", "stop_sequence", "stop_lat", "stop_lon",
            "sched_sec", "ping_sec", "dist_m", "delay_min",
        )
    )

    return _drop_incoherent_journeys(raw_events)


def compute_delay_events(spark: SparkSession, service_days=SERVICE_DAYS) -> DataFrame:
    """Delay events across all configured service days, unioned into one table."""
    per_day = [compute_delay_events_for_day(spark, date, weekday) for date, weekday in service_days]
    result = per_day[0]
    for df in per_day[1:]:
        result = result.unionByName(df)
    return result


def _drop_incoherent_journeys(events: DataFrame) -> DataFrame:
    """Removes journeys whose per-stop delays are physically inconsistent (failed AVL->schedule matches).

    A correctly matched bus journey shows delays that vary smoothly along its route - it can't be 30 min
    late at one stop and on time at the next. Diagnostics on the unfiltered output showed ~49% of matched
    journeys have a per-journey delay standard deviation above MAX_JOURNEY_DELAY_STD, driving an
    implausible 20-90 min tail; these are matching failures (wrong-trip pinning / non-serving fly-bys),
    not late buses. Dropping them cleans the target without biasing its level: journeys that stay
    genuinely, consistently late are retained. Journeys with <3 matched stops are kept as-is (too few
    points to assess consistency).
    """
    key = ["service_date", "trip_id", "vehicle_ref", "origin_aimed_departure"]
    journey_stats = events.groupBy(*key).agg(
        F.count("*").alias("journey_n_stops"),
        F.stddev("delay_min").alias("journey_delay_std"),
    )
    keep = journey_stats.filter(
        (F.col("journey_n_stops") < 3) | (F.col("journey_delay_std") <= MAX_JOURNEY_DELAY_STD)
    ).select(*key)
    return events.join(keep, on=key, how="inner")


def write_delay_events(events: DataFrame) -> None:
    events.write.mode("overwrite").parquet(str(OUT_DIR))


def write_delay_events(events: DataFrame) -> None:
    events.write.mode("overwrite").parquet(str(OUT_DIR))
