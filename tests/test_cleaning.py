"""Tests for the data-cleaning behaviour the pipeline depends on.

Required by PROJECT_RULES section 6. These cover the geographic scoping used to filter both feeds and
the SIRI-VM parser's tolerance of unusable snapshots, which is what stopped a corrupt archive entry from
aborting a full-day run. All tests are pure Python so they run without a SparkSession.
"""

import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.geography import (  # noqa: E402
    GM_LAT_MAX,
    GM_LAT_MIN,
    GM_LON_MAX,
    GM_LON_MIN,
    in_greater_manchester,
)
from ingestion.load_sirivm import parse_snapshot  # noqa: E402

SIRI_NS = "http://www.siri.org.uk/siri"


# --------------------------------------------------------------------- geography
def test_manchester_city_centre_is_inside():
    # Manchester Piccadilly, comfortably inside the study area.
    assert in_greater_manchester(53.477, -2.230)


@pytest.mark.parametrize("lat, lon, place", [
    (51.507, -0.128, "London"),
    (53.408, -2.991, "Liverpool"),
    (53.796, -1.548, "Leeds"),
])
def test_cities_outside_greater_manchester_are_excluded(lat, lon, place):
    assert not in_greater_manchester(lat, lon), f"{place} should be outside the study area"


def test_bounding_box_edges_are_inclusive():
    assert in_greater_manchester(GM_LAT_MIN, GM_LON_MIN)
    assert in_greater_manchester(GM_LAT_MAX, GM_LON_MAX)


def test_just_outside_bounding_box_is_excluded():
    assert not in_greater_manchester(GM_LAT_MIN - 0.01, GM_LON_MIN)
    assert not in_greater_manchester(GM_LAT_MAX, GM_LON_MAX + 0.01)


# --------------------------------------------------------------------- SIRI-VM parsing
def _siri_xml(lat: float, lon: float) -> bytes:
    return (
        f'<Siri xmlns="{SIRI_NS}"><ServiceDelivery><VehicleMonitoringDelivery>'
        "<VehicleActivity><RecordedAtTime>2026-07-01T09:00:00+00:00</RecordedAtTime>"
        "<MonitoredVehicleJourney><LineRef>42</LineRef><DirectionRef>inbound</DirectionRef>"
        "<OperatorRef>TEST</OperatorRef>"
        "<FramedVehicleJourneyRef><DataFrameRef>2026-07-01</DataFrameRef>"
        "<DatedVehicleJourneyRef>VJ_1</DatedVehicleJourneyRef></FramedVehicleJourneyRef>"
        "<OriginAimedDepartureTime>2026-07-01T08:30:00+00:00</OriginAimedDepartureTime>"
        f"<VehicleLocation><Longitude>{lon}</Longitude><Latitude>{lat}</Latitude></VehicleLocation>"
        "<VehicleRef>BUS1</VehicleRef></MonitoredVehicleJourney></VehicleActivity>"
        "</VehicleMonitoringDelivery></ServiceDelivery></Siri>"
    ).encode()


def _archive(tmp_path: Path, inner_name: str, payload: bytes) -> str:
    """Builds the zip-of-zips layout the real archive uses."""
    inner = io.BytesIO()
    if payload:
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("siri.xml", payload)
    outer_path = tmp_path / "archive.zip"
    with zipfile.ZipFile(outer_path, "w") as z:
        z.writestr(inner_name, inner.getvalue() if payload else b"")
    return str(outer_path)


def test_position_inside_study_area_is_parsed(tmp_path):
    archive = _archive(tmp_path, "snap.zip", _siri_xml(53.477, -2.230))
    rows = parse_snapshot(archive, "snap.zip", "20260701")
    assert len(rows) == 1
    assert rows[0]["line_ref"] == "42"
    assert rows[0]["operator_ref"] == "TEST"
    assert rows[0]["source_date"] == "20260701"


def test_position_outside_study_area_is_filtered_out(tmp_path):
    archive = _archive(tmp_path, "snap.zip", _siri_xml(51.507, -0.128))  # London
    assert parse_snapshot(archive, "snap.zip", "20260701") == []


def test_empty_snapshot_is_skipped_not_fatal(tmp_path):
    """A zero-byte entry must not abort the run - two such entries exist in the real archives."""
    archive = _archive(tmp_path, "snap.zip", b"")
    assert parse_snapshot(archive, "snap.zip", "20260701") == []


def test_corrupt_snapshot_is_skipped_not_fatal(tmp_path):
    outer_path = tmp_path / "archive.zip"
    with zipfile.ZipFile(outer_path, "w") as z:
        z.writestr("snap.zip", b"this is not a zip file")
    assert parse_snapshot(str(outer_path), "snap.zip", "20260701") == []


def test_activity_without_location_is_skipped(tmp_path):
    xml = (
        f'<Siri xmlns="{SIRI_NS}"><ServiceDelivery><VehicleMonitoringDelivery><VehicleActivity>'
        "<RecordedAtTime>2026-07-01T09:00:00+00:00</RecordedAtTime>"
        "<MonitoredVehicleJourney><LineRef>42</LineRef></MonitoredVehicleJourney>"
        "</VehicleActivity></VehicleMonitoringDelivery></ServiceDelivery></Siri>"
    ).encode()
    archive = _archive(tmp_path, "snap.zip", xml)
    assert parse_snapshot(archive, "snap.zip", "20260701") == []
