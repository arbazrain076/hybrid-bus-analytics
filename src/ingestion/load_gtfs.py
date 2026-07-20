"""Loads the North West GTFS feed and filters it down to Greater Manchester.

The BODS-ARCHIVE timetables export bundles GTFS by DfT region, not by transport authority, so the North
West file also covers Merseyside, Lancashire and Cumbria. We scope to Greater Manchester using a lat/lon
bounding box against stops.txt (~53.30-53.65 N, ~-2.75--1.90 E) rather than agency/operator codes, since
several operators (e.g. Stagecoach) run services both inside and outside Greater Manchester under the
same agency_id.
"""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import broadcast
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

GTFS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "timetables" / "north_west_gtfs"
SILVER_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "silver" / "gtfs_gm"

# Greater Manchester Combined Authority area, approximated as a bounding box.
GM_LAT_MIN, GM_LAT_MAX = 53.30, 53.65
GM_LON_MIN, GM_LON_MAX = -2.75, -1.90

STOPS_SCHEMA = StructType(
    [
        StructField("stop_id", StringType(), False),
        StructField("stop_code", StringType(), True),
        StructField("stop_name", StringType(), True),
        StructField("stop_lat", DoubleType(), True),
        StructField("stop_lon", DoubleType(), True),
        StructField("wheelchair_boarding", IntegerType(), True),
        StructField("location_type", IntegerType(), True),
        StructField("parent_station", StringType(), True),
        StructField("platform_code", StringType(), True),
    ]
)

ROUTES_SCHEMA = StructType(
    [
        StructField("route_id", StringType(), False),
        StructField("agency_id", StringType(), True),
        StructField("route_short_name", StringType(), True),
        StructField("route_long_name", StringType(), True),
        StructField("route_type", IntegerType(), True),
    ]
)

TRIPS_SCHEMA = StructType(
    [
        StructField("route_id", StringType(), False),
        StructField("service_id", StringType(), True),
        StructField("trip_id", StringType(), False),
        StructField("trip_headsign", StringType(), True),
        StructField("direction_id", IntegerType(), True),
        StructField("block_id", StringType(), True),
        StructField("shape_id", StringType(), True),
        StructField("wheelchair_accessible", IntegerType(), True),
        StructField("vehicle_journey_code", StringType(), True),
    ]
)

STOP_TIMES_SCHEMA = StructType(
    [
        StructField("trip_id", StringType(), False),
        StructField("arrival_time", StringType(), True),
        StructField("departure_time", StringType(), True),
        StructField("stop_id", StringType(), False),
        StructField("stop_sequence", IntegerType(), True),
        StructField("stop_headsign", StringType(), True),
        StructField("pickup_type", IntegerType(), True),
        StructField("drop_off_type", IntegerType(), True),
        StructField("shape_dist_traveled", DoubleType(), True),
        StructField("timepoint", IntegerType(), True),
    ]
)


def _read_csv(spark: SparkSession, filename: str, schema: StructType) -> DataFrame:
    return spark.read.csv(str(GTFS_DIR / filename), header=True, schema=schema)


def load_greater_manchester_gtfs(spark: SparkSession) -> dict[str, DataFrame]:
    stops = _read_csv(spark, "stops.txt", STOPS_SCHEMA)
    routes = _read_csv(spark, "routes.txt", ROUTES_SCHEMA)
    trips = _read_csv(spark, "trips.txt", TRIPS_SCHEMA)
    stop_times = _read_csv(spark, "stop_times.txt", STOP_TIMES_SCHEMA).repartition(8, "trip_id")

    raw_counts = {
        "stops": stops.count(),
        "routes": routes.count(),
        "trips": trips.count(),
        "stop_times": stop_times.count(),
    }

    gm_stops = stops.filter(
        (stops.stop_lat >= GM_LAT_MIN)
        & (stops.stop_lat <= GM_LAT_MAX)
        & (stops.stop_lon >= GM_LON_MIN)
        & (stops.stop_lon <= GM_LON_MAX)
    ).cache()

    # gm_stops (~15k rows) is far smaller than stop_times (~5M rows) - broadcast the small side.
    gm_stop_times = stop_times.join(broadcast(gm_stops.select("stop_id")), on="stop_id", how="inner")

    gm_trip_ids = gm_stop_times.select("trip_id").distinct().cache()
    gm_trips = trips.join(broadcast(gm_trip_ids), on="trip_id", how="inner").cache()
    gm_routes = routes.join(
        broadcast(gm_trips.select("route_id").distinct()), on="route_id", how="inner"
    ).cache()

    filtered_counts = {
        "stops": gm_stops.count(),
        "routes": gm_routes.count(),
        "trips": gm_trips.count(),
        "stop_times": gm_stop_times.count(),
    }

    print("Raw (North West region) row counts:", raw_counts)
    print("Filtered (Greater Manchester) row counts:", filtered_counts)

    gm_stops.unpersist()
    gm_trip_ids.unpersist()
    gm_trips.unpersist()
    gm_routes.unpersist()

    return {
        "stops": gm_stops,
        "routes": gm_routes,
        "trips": gm_trips,
        "stop_times": gm_stop_times,
    }


def write_silver(tables: dict[str, DataFrame]) -> None:
    # Plain intermediate Parquet write, not .checkpoint() - this is bronze->silver persistence for reuse
    # by later pipeline stages, not lineage truncation of a long transformation chain.
    for name, df in tables.items():
        df.write.mode("overwrite").parquet(str(SILVER_DIR / name))
