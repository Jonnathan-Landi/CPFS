from pathlib import Path
import xarray as xr
import cfgrib


def open_ecmwf_dataset(grib_path: str | Path) -> xr.Dataset:
    grib_path = Path(grib_path)

    if not grib_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {grib_path}")

    datasets = cfgrib.open_datasets(
        grib_path,
        indexpath=""
    )

    if not datasets:
        raise ValueError(f"No se pudo abrir ningún dataset GRIB: {grib_path}")

    ds = xr.merge(
        datasets,
        compat="override",
        combine_attrs="drop_conflicts"
    )

    return ds