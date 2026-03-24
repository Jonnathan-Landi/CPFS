from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from cpfs.utils.time import (
    CUENCA_TIMEZONE,
    compute_valid_time,
    get_latest_ecmwf_run,
)

ECMWF_CYCLE_HOURS = (0, 6, 12, 18)


@dataclass(frozen=True)
class CurrentTimeContext:
    now_utc: datetime
    now_local: datetime


@dataclass(frozen=True)
class EcmwfRunInfo:
    run_date: str
    run_time: str
    run_datetime_utc: datetime
    run_datetime_local: datetime


@dataclass(frozen=True)
class ForecastValidTime:
    step_hours: int
    valid_time_utc: datetime
    valid_time_local: datetime


def get_current_time_context() -> CurrentTimeContext:
    """Return current time in UTC and Cuenca local timezone."""
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(CUENCA_TIMEZONE)
    return CurrentTimeContext(now_utc=now_utc, now_local=now_local)


def select_latest_available_run(
    now_utc: datetime | None = None,
    availability_delay_hours: int = 4,
) -> EcmwfRunInfo:
    """
    Select latest valid ECMWF run for operation automation.

    Parameters
    ----------
    now_utc:
        Current UTC time. If omitted, current system UTC is used.
    availability_delay_hours:
        Delay buffer to avoid selecting a cycle that may still be unavailable.
        The selection uses (now_utc - delay) as reference.
    """
    run_info = get_latest_ecmwf_run(
        latency_hours=availability_delay_hours,
        now_utc=now_utc,
    )

    return EcmwfRunInfo(
        run_date=run_info.run_date,
        run_time=run_info.run_time,
        run_datetime_utc=run_info.run_datetime_utc,
        run_datetime_local=run_info.run_datetime_local,
    )


def build_run_info_from_date_time(run_date: str, run_time: str) -> EcmwfRunInfo:
    """Build run metadata from explicit date/time strings (YYYYMMDD, HH)."""
    run_datetime_utc = datetime.strptime(
        f"{run_date}{run_time}",
        "%Y%m%d%H",
    ).replace(tzinfo=timezone.utc)
    run_datetime_local = run_datetime_utc.astimezone(CUENCA_TIMEZONE)

    return EcmwfRunInfo(
        run_date=run_date,
        run_time=run_time,
        run_datetime_utc=run_datetime_utc,
        run_datetime_local=run_datetime_local,
    )


def calculate_forecast_valid_time(
    run_info: EcmwfRunInfo,
    step_hours: int,
) -> ForecastValidTime:
    """Calculate valid time in UTC and Cuenca local timezone for a forecast step."""
    valid_time = compute_valid_time(run_info.run_datetime_utc, step_hours)

    return ForecastValidTime(
        step_hours=step_hours,
        valid_time_utc=valid_time.valid_time_utc,
        valid_time_local=valid_time.valid_time_local,
    )
