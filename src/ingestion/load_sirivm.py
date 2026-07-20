"""Parses raw SIRI-VM XML snapshots and filters vehicle positions to Greater Manchester.

The national archive is a zip of zips: `sirivm-20260701.zip` contains one nested zip per ~30-second BODS
poll, each holding a single `siri.xml` covering every monitored bus in Great Britain. This feed carries
no per-stop delay field (no MonitoredCall/expected-arrival) - only a live vehicle position - so this
module only extracts positions. Matching them to scheduled stop times to derive observed delay is a
separate step (src/processing/compute_delay.py), since the AVL and GTFS feeds use different journey
identifiers and can't be joined on trip_id directly.
"""

import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from config.geography import in_greater_manchester

SIRIVM_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "sirivm"
SIRI_NS = "{http://www.siri.org.uk/siri}"


def archive_path(date_str: str) -> str:
    """Path to the daily SIRI-VM archive for date_str (YYYYMMDD)."""
    return str(SIRIVM_DIR / f"sirivm-{date_str}.zip")

VEHICLE_ACTIVITY_SCHEMA = StructType(
    [
        StructField("recorded_at", StringType(), False),
        StructField("line_ref", StringType(), True),
        StructField("direction_ref", StringType(), True),
        StructField("operator_ref", StringType(), True),
        StructField("origin_ref", StringType(), True),
        StructField("destination_ref", StringType(), True),
        StructField("origin_aimed_departure", StringType(), True),
        StructField("dated_vehicle_journey_ref", StringType(), True),
        StructField("data_frame_ref", StringType(), True),
        StructField("vehicle_ref", StringType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("snapshot_file", StringType(), False),
        StructField("source_date", StringType(), False),
    ]
)


def list_snapshot_names(archive: str) -> list[str]:
    with zipfile.ZipFile(archive) as outer:
        return [n for n in outer.namelist() if n.endswith(".zip")]


def _text(elem, tag) -> str | None:
    if elem is None:
        return None
    child = elem.find(f"{SIRI_NS}{tag}")
    return child.text if child is not None else None


def parse_snapshot(archive: str, inner_name: str, source_date: str) -> list[dict]:
    """Parses one nested snapshot zip and returns Greater Manchester vehicle activity rows only.

    A small number of nested snapshots in the archive are empty (0 bytes) or otherwise corrupt (observed:
    2 of 2,761 for 2026-07-01). These are skipped rather than aborting the whole run - a dropped ~30s
    snapshot is a negligible loss against a full day of position data.
    """
    with zipfile.ZipFile(archive) as outer:
        inner_bytes = outer.read(inner_name)

    if not inner_bytes:
        return []
    try:
        with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
            xml_bytes = inner.read("siri.xml")
        root = ET.fromstring(xml_bytes)
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        return []

    rows = []
    for activity in root.iter(f"{SIRI_NS}VehicleActivity"):
        mvj = activity.find(f"{SIRI_NS}MonitoredVehicleJourney")
        loc = mvj.find(f"{SIRI_NS}VehicleLocation") if mvj is not None else None
        if loc is None:
            continue

        lon_text, lat_text = _text(loc, "Longitude"), _text(loc, "Latitude")
        if lon_text is None or lat_text is None:
            continue
        lon, lat = float(lon_text), float(lat_text)
        if not in_greater_manchester(lat, lon):
            continue

        fvjr = mvj.find(f"{SIRI_NS}FramedVehicleJourneyRef")
        rows.append(
            {
                "recorded_at": _text(activity, "RecordedAtTime"),
                "line_ref": _text(mvj, "LineRef"),
                "direction_ref": _text(mvj, "DirectionRef"),
                "operator_ref": _text(mvj, "OperatorRef"),
                "origin_ref": _text(mvj, "OriginRef"),
                "destination_ref": _text(mvj, "DestinationRef"),
                "origin_aimed_departure": _text(mvj, "OriginAimedDepartureTime"),
                "dated_vehicle_journey_ref": _text(fvjr, "DatedVehicleJourneyRef"),
                "data_frame_ref": _text(fvjr, "DataFrameRef"),
                "vehicle_ref": _text(mvj, "VehicleRef"),
                "longitude": lon,
                "latitude": lat,
                "snapshot_file": inner_name,
                "source_date": source_date,
            }
        )
    return rows


def load_greater_manchester_sirivm(
    spark: SparkSession, date_str: str, sample_every_nth: int = 1
) -> DataFrame:
    archive = archive_path(date_str)
    names = list_snapshot_names(archive)
    if sample_every_nth > 1:
        names = names[::sample_every_nth]

    tasks = [(archive, name, date_str) for name in names]
    rdd = spark.sparkContext.parallelize(tasks, numSlices=8)
    rows_rdd = rdd.flatMap(lambda t: parse_snapshot(t[0], t[1], t[2]))
    return spark.createDataFrame(rows_rdd, schema=VEHICLE_ACTIVITY_SCHEMA)
