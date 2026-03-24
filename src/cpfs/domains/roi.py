from pathlib import Path
import geopandas as gpd


def read_roi(roi_path: str, layer: str | None = None) -> gpd.GeoDataFrame:
    roi_path = Path(roi_path)

    if not roi_path.exists():
        raise FileNotFoundError(f"ROI no encontrado: {roi_path}")

    if roi_path.suffix.lower() == ".gpkg":
        gdf = gpd.read_file(roi_path, layer=layer)
    else:
        gdf = gpd.read_file(roi_path)

    if gdf.empty:
        raise ValueError(f"El ROI está vacío: {roi_path}")

    if gdf.crs is None:
        raise ValueError(f"El ROI no tiene CRS definido: {roi_path}")

    return gdf