from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .types import ZoneObservation


def read_zones(
    zones_geojson_path: str,
    ecuador_boundary_path: str | None = None,
    zones_input_crs: str | None = None,
) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    path = Path(zones_geojson_path)
    if not path.exists():
        raise FileNotFoundError(f"Zones file not found: {zones_geojson_path}")

    try:
        import geopandas as gpd
    except ModuleNotFoundError:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        zone_ids = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            zone_id = props.get("zone_id")
            if zone_id:
                zone_ids.append(str(zone_id))

        if ecuador_boundary_path:
            warnings.append(
                "geopandas not available; Ecuador boundary clipping skipped (install geopandas to enable)"
            )
    else:
        zones_gdf = gpd.read_file(path)
        if zones_gdf.empty:
            raise ValueError("Zones file has no features.")

        if "zone_id" not in zones_gdf.columns:
            raise ValueError("No zone_id found in zones file.")

        if zones_gdf.crs is None:
            assumed_crs = zones_input_crs or "EPSG:4326"
            zones_gdf = zones_gdf.set_crs(assumed_crs)
            warnings.append(f"zones CRS missing; assuming {assumed_crs}")

        if ecuador_boundary_path:
            boundary_path = Path(ecuador_boundary_path)
            if not boundary_path.exists():
                raise FileNotFoundError(f"Ecuador boundary not found: {ecuador_boundary_path}")

            boundary_gdf = gpd.read_file(boundary_path)
            if boundary_gdf.empty:
                raise ValueError("Ecuador boundary is empty.")
            if boundary_gdf.crs is None:
                raise ValueError("Ecuador boundary CRS is undefined.")

            zones_in_boundary_crs = zones_gdf.to_crs(boundary_gdf.crs)
            boundary_union = boundary_gdf.geometry.unary_union
            mask = zones_in_boundary_crs.geometry.intersects(boundary_union)
            outside = zones_in_boundary_crs.loc[~mask, "zone_id"].dropna().astype(str).tolist()
            if outside:
                warnings.append(
                    "zones outside Ecuador boundary were excluded: " + ", ".join(sorted(set(outside)))
                )

            zones_gdf = zones_gdf.loc[mask.values].copy()

        zone_ids = [str(zid) for zid in zones_gdf["zone_id"].dropna().tolist()]

    if not zone_ids:
        raise ValueError("No valid zones remain after spatial validation.")

    return zone_ids, warnings


def read_latest_observations(observations_path: str, zone_ids: List[str]) -> Tuple[str, List[ZoneObservation], List[str]]:
    warnings: List[str] = []
    path = Path(observations_path)

    if not path.exists():
        warnings.append("latest_observations file missing; using fallback synthetic satellite observations")
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

        if "humidity_index" in source and "moisture_index" not in source:
            warnings.append(
                f"zone {zone_id}: humidity_index is deprecated, use moisture_index for satellite-only mode"
            )
        if "recent_rain_mm" in source and "satellite_recent_rain_mm" not in source:
            warnings.append(
                f"zone {zone_id}: recent_rain_mm is deprecated, use satellite_recent_rain_mm"
            )

        observations.append(
            ZoneObservation(
                zone_id=zone_id,
                cloud_index=float(source.get("cloud_index", 0.5)),
                moisture_index=float(source.get("moisture_index", source.get("humidity_index", 0.5))),
                satellite_cold_cloud=float(source.get("satellite_cold_cloud", 0.5)),
                satellite_recent_rain_mm=float(
                    source.get("satellite_recent_rain_mm", source.get("recent_rain_mm", 0.0))
                ),
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
        moisture_index=0.55,
        satellite_cold_cloud=0.45,
        satellite_recent_rain_mm=0.0,
    )
