from pathlib import Path
import xarray as xr
import rioxarray  # activa el accessor .rio
from cpfs.domains.roi import read_roi


def normalize_ecmwf_coords(ds: xr.Dataset) -> xr.Dataset:
    rename_map = {}

    if "longitude" in ds.dims:
        rename_map["longitude"] = "x"
    elif "lon" in ds.dims:
        rename_map["lon"] = "x"

    if "latitude" in ds.dims:
        rename_map["latitude"] = "y"
    elif "lat" in ds.dims:
        rename_map["lat"] = "y"

    ds = ds.rename(rename_map)

    return ds


def assign_wgs84(ds: xr.Dataset) -> xr.Dataset:
    return ds.rio.write_crs("EPSG:4326", inplace=False)


def clip_with_roi(
    ds: xr.Dataset,
    roi_path: str,
    roi_layer: str | None = None
) -> xr.Dataset:
    roi = read_roi(roi_path, layer=roi_layer)

    # Reproyectar dataset al CRS del ROI
    ds_proj = ds.rio.reproject(roi.crs)

    # Recorte exacto por geometría
    ds_clip = ds_proj.rio.clip(
        roi.geometry,
        roi.crs,
        drop=True,
        all_touched=True
    )

    return ds_clip


def save_dataset(ds: xr.Dataset, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(out_path)
    return out_path


def standardize_ecmwf_file(
    raw_path: str | Path,
    out_path: str | Path,
    roi_path: str,
    roi_layer: str | None = None
) -> Path:
    from cpfs.ingest.ecmwf.parse_grib import open_ecmwf_dataset

    out_path = Path(out_path)
    raw_path = Path(raw_path)
    if out_path.exists():
        raw_mtime = raw_path.stat().st_mtime
        out_mtime = out_path.stat().st_mtime
        if out_mtime >= raw_mtime:
            print(f"[INFO] Archivo interim ya existe: {out_path}")
            return out_path
        print(f"[INFO] Regenerando interim porque raw es más reciente: {out_path}")

    ds = open_ecmwf_dataset(raw_path)
    ds = normalize_ecmwf_coords(ds)
    ds = assign_wgs84(ds)
    ds = clip_with_roi(ds, roi_path=roi_path, roi_layer=roi_layer)

    save_dataset(ds, out_path)
    print(f"[OK] Archivo estandarizado guardado en: {out_path}")

    return out_path