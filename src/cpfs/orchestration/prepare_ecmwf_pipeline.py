from pathlib import Path
import os
from datetime import datetime, timezone

from cpfs.ingest.ecmwf.download import download_ecmwf_forecast
from cpfs.utils.time import (
    CUENCA_TIMEZONE,
    EcmwfRunSelection,
    get_latest_ecmwf_run,
)
from cpfs.standardize.ecmwf import standardize_ecmwf_file


def get_availability_lag_hours(default: int = 4) -> int:
    raw_value = os.getenv("CPFS_ECMWF_AVAILABILITY_LAG_HOURS")
    if raw_value is None:
        return default

    try:
        parsed_value = int(raw_value)
    except ValueError:
        print(
            "[WARN] CPFS_ECMWF_AVAILABILITY_LAG_HOURS inválido. "
            f"Usando valor por defecto: {default}"
        )
        return default

    if parsed_value < 0:
        print(
            "[WARN] CPFS_ECMWF_AVAILABILITY_LAG_HOURS no puede ser negativo. "
            f"Usando valor por defecto: {default}"
        )
        return default

    return parsed_value


def resolve_requested_run(
    date: str | None,
    time: str | None,
    availability_lag_hours: int,
) -> EcmwfRunSelection:
    if date is None and time is None:
        return get_latest_ecmwf_run(
            latency_hours=availability_lag_hours
        )

    current_time_utc = datetime.now(timezone.utc)
    current_time_local = current_time_utc.astimezone(CUENCA_TIMEZONE)

    def build_run_selection(run_date: str, run_time: str) -> EcmwfRunSelection:
        run_datetime_utc = datetime.strptime(
            f"{run_date}{run_time}",
            "%Y%m%d%H",
        ).replace(tzinfo=timezone.utc)
        return EcmwfRunSelection(
            run_date=run_date,
            run_time=run_time,
            run_datetime_utc=run_datetime_utc,
            run_datetime_local=run_datetime_utc.astimezone(CUENCA_TIMEZONE),
            current_time_utc=current_time_utc,
            current_time_local=current_time_local,
        )

    if date is not None and time is None:
        return build_run_selection(date, "18")

    if date is None and time is not None:
        today_utc = datetime.now(timezone.utc).strftime("%Y%m%d")
        return build_run_selection(today_utc, time)

    return build_run_selection(date, time)


def build_interim_path(raw_path: str | Path) -> Path:
    raw_path = Path(raw_path)
    date_folder = raw_path.parent.name
    filename = raw_path.stem + "_roi.nc"
    return Path("data/interim/ecmwf") / date_folder / filename


def run_prepare_ecmwf(
    date: str | None = None,
    time: str | None = None,
    steps: list[int] | None = None,
    variables: list[str] | None = None,
    roi_path: str = "assets/roi/cuenca_forecast_roi/cuenca_forecast_roi.shp",
    roi_layer: str | None = "cuenca_forecast_roi",
    availability_lag_hours: int = 4,
) -> Path:
    availability_lag_hours = get_availability_lag_hours(availability_lag_hours)

    run_info = resolve_requested_run(
        date=date,
        time=time,
        availability_lag_hours=availability_lag_hours,
    )

    print(
        "[INFO] Tiempo actual: "
        f"{run_info.current_time_utc.strftime('%Y-%m-%d %H:%M %Z')} "
        f"({run_info.current_time_local.strftime('%Y-%m-%d %H:%M %Z')})"
    )
    print(
        "[INFO] Corrida ECMWF seleccionada: "
        f"{run_info.run_date} {run_info.run_time} UTC "
        f"({run_info.run_datetime_local.strftime('%Y-%m-%d %H:%M %Z')})"
    )

    raw_path = download_ecmwf_forecast(
        date=run_info.run_date,
        time=run_info.run_time,
        steps=steps,
        variables=variables,
        base_dir="data/raw/ecmwf",
    )

    interim_path = build_interim_path(raw_path)

    standardize_ecmwf_file(
        raw_path=raw_path,
        out_path=interim_path,
        roi_path=roi_path,
        roi_layer=roi_layer,
    )

    return interim_path