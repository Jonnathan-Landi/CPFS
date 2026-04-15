import json
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import box

repo = Path(r"d:/Windows/GitHub/CPFS")
ecuador_path = repo / "assets" / "Ec" / "ecuador.shp"
zones_path = repo / "zones" / "zones.geojson"
obs_path = repo / "inputs" / "latest_observations.json"

# Build a national fishnet in Ecuador CRS (EPSG:32717) and clip to boundary.
ecuador = gpd.read_file(ecuador_path).to_crs("EPSG:32717")
union = ecuador.geometry.union_all()

minx, miny, maxx, maxy = ecuador.total_bounds
cell_size_m = 50000  # 50 km grid for national coverage

xs = np.arange(minx, maxx + cell_size_m, cell_size_m)
ys = np.arange(miny, maxy + cell_size_m, cell_size_m)

cells = []
zone_ids = []
idx = 1
for i in range(len(xs) - 1):
    for j in range(len(ys) - 1):
        geom = box(xs[i], ys[j], xs[i + 1], ys[j + 1])
        if not geom.intersects(union):
            continue
        clipped = geom.intersection(union)
        if clipped.is_empty:
            continue
        cells.append(clipped)
        zone_ids.append(f"EC_{idx:04d}")
        idx += 1

zones_utm = gpd.GeoDataFrame({"zone_id": zone_ids, "name": zone_ids}, geometry=cells, crs="EPSG:32717")
zones = zones_utm.to_crs("EPSG:4326")
zones.to_file(zones_path, driver="GeoJSON")

# Create synthetic satellite observations for all zones so every polygon gets values.
centroids_utm = zones_utm.geometry.centroid
centroids = gpd.GeoSeries(centroids_utm, crs="EPSG:32717").to_crs("EPSG:4326")
xmin, ymin, xmax, ymax = zones.total_bounds

obs = []
for zid, c in zip(zones["zone_id"].tolist(), centroids.tolist()):
    lon_n = (c.x - xmin) / max(1e-9, (xmax - xmin))
    lat_n = (c.y - ymin) / max(1e-9, (ymax - ymin))

    moisture = float(np.clip(0.35 + 0.45 * lat_n + 0.15 * np.sin(6 * lon_n), 0.05, 0.98))
    cloud = float(np.clip(0.30 + 0.55 * lon_n + 0.10 * np.cos(5 * lat_n), 0.05, 0.98))
    cold_cloud = float(np.clip(0.25 + 0.60 * (0.5 * lon_n + 0.5 * lat_n), 0.05, 0.98))
    recent_rain = float(np.clip((moisture + cold_cloud - 0.7) * 8.0, 0.0, 12.0))

    obs.append(
        {
            "zone_id": zid,
            "cloud_index": round(cloud, 3),
            "moisture_index": round(moisture, 3),
            "satellite_cold_cloud": round(cold_cloud, 3),
            "satellite_recent_rain_mm": round(recent_rain, 2),
        }
    )

payload = {
    "timestamp_utc": "2026-04-14T12:00:00Z",
    "zones": obs,
}
obs_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print(f"Generated zones: {len(zones)}")
print(f"Wrote: {zones_path}")
print(f"Wrote: {obs_path}")
