from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .types import ZoneObservation


def read_zones(zones_geojson_path: str) -> List[str]:
    path = Path(zones_geojson_path)
    if not path.exists():
        raise FileNotFoundError(f"Zones file not found: {zones_geojson_path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    zone_ids: List[str] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        zone_id = props.get("zone_id")
        if zone_id:
            zone_ids.append(zone_id)

    if not zone_ids:
        raise ValueError("No zone_id found in zones file.")

    return zone_ids


def read_latest_observations(observations_path: str, zone_ids: List[str]) -> Tuple[str, List[ZoneObservation], List[str]]:
    warnings: List[str] = []
    path = Path(observations_path)

    if not path.exists():
        warnings.append("latest_observations file missing; using fallback synthetic observations")
        return "missing-input", _synthetic_observations(zone_ids), warnings

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    timestamp = payload.get("timestamp_utc", "unknown")
    by_zone: Dict[str, Dict[str, float]] = {item.get("zone_id", ""): item for item in payload.get("zones", [])}

    observations: List[ZoneObservation] = []
    for zone_id in zone_ids:
        source = by_zone.get(zone_id)
        if source is None:
            warnings.append(f"zone {zone_id} missing in latest observations; using fallback values")
            observations.append(_fallback_zone(zone_id))
            continue

        observations.append(
            ZoneObservation(
                zone_id=zone_id,
                cloud_index=float(source.get("cloud_index", 0.5)),
                humidity_index=float(source.get("humidity_index", 0.5)),
                satellite_cold_cloud=float(source.get("satellite_cold_cloud", 0.5)),
                recent_rain_mm=float(source.get("recent_rain_mm", 0.0)),
            )
        )

    return timestamp, observations, warnings


def _synthetic_observations(zone_ids: List[str]) -> List[ZoneObservation]:
    return [_fallback_zone(zone_id) for zone_id in zone_ids]


def _fallback_zone(zone_id: str) -> ZoneObservation:
    # Neutral fallback keeps the pipeline running without extreme outputs.
    return ZoneObservation(
        zone_id=zone_id,
        cloud_index=0.5,
        humidity_index=0.55,
        satellite_cold_cloud=0.45,
        recent_rain_mm=0.0,
    )
