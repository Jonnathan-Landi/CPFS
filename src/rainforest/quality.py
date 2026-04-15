from __future__ import annotations

from typing import List, Tuple

from .types import ZoneObservation


def basic_quality_check(observations: List[ZoneObservation]) -> Tuple[List[ZoneObservation], List[str]]:
    warnings: List[str] = []
    cleaned: List[ZoneObservation] = []

    for item in observations:
        cloud = _clip01(item.cloud_index, item.zone_id, "cloud_index", warnings)
        moisture = _clip01(item.moisture_index, item.zone_id, "moisture_index", warnings)
        cold_cloud = _clip01(item.satellite_cold_cloud, item.zone_id, "satellite_cold_cloud", warnings)
        recent_rain = max(0.0, item.satellite_recent_rain_mm)
        if recent_rain != item.satellite_recent_rain_mm:
            warnings.append(f"zone {item.zone_id}: satellite_recent_rain_mm < 0 adjusted to 0")

        cleaned.append(
            ZoneObservation(
                zone_id=item.zone_id,
                cloud_index=cloud,
                moisture_index=moisture,
                satellite_cold_cloud=cold_cloud,
                satellite_recent_rain_mm=recent_rain,
            )
        )

    return cleaned, warnings


def _clip01(value: float, zone_id: str, field: str, warnings: List[str]) -> float:
    clipped = min(1.0, max(0.0, value))
    if clipped != value:
        warnings.append(f"zone {zone_id}: {field} out of [0,1], clipped")
    return clipped
