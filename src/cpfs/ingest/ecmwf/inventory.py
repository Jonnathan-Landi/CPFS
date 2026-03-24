from pathlib import Path

def list_downloaded_files(base_dir="data/raw/ecmwf"):
    path = Path(base_dir)

    if not path.exists():
        return []

    return list(path.rglob("*.grib2"))