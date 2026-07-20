"""Shared geographic scoping for Greater Manchester.

Used to filter both GTFS stops and SIRI-VM vehicle positions consistently, since agency/operator codes
alone aren't a reliable filter (some operators run services both inside and outside the area).
"""

GM_LAT_MIN, GM_LAT_MAX = 53.30, 53.65
GM_LON_MIN, GM_LON_MAX = -2.75, -1.90


def in_greater_manchester(lat: float, lon: float) -> bool:
    return GM_LAT_MIN <= lat <= GM_LAT_MAX and GM_LON_MIN <= lon <= GM_LON_MAX
