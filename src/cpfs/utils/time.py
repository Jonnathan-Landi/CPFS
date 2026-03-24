from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


CUENCA_TIMEZONE = ZoneInfo("America/Guayaquil")
ECMWF_RUN_HOURS = (0, 6, 12, 18)


@dataclass(frozen=True)
class EcmwfRunSelection:
    run_date: str
    run_time: str
    run_datetime_utc: datetime
    run_datetime_local: datetime
    current_time_utc: datetime
    current_time_local: datetime


@dataclass(frozen=True)
class ForecastValidTime:
    valid_time_utc: datetime
    valid_time_local: datetime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _latest_run_datetime_utc(reference_utc: datetime) -> datetime:
    selected_hour = max(hour for hour in ECMWF_RUN_HOURS if hour <= reference_utc.hour)
    return reference_utc.replace(
        hour=selected_hour,
        minute=0,
        second=0,
        microsecond=0,
    )


def get_latest_ecmwf_run(
    latency_hours: int = 4,
    now_utc: datetime | None = None,
) -> EcmwfRunSelection:
    """
    Return the latest ECMWF run expected to be available for Open Data.

    The function uses current UTC time minus a latency buffer to avoid selecting
    a run that is likely still unavailable.

    Parameters
    ----------
    latency_hours:
        Availability latency in hours (default 4).
    now_utc:
        Optional UTC timestamp for deterministic testing.
    """
    if latency_hours < 0:
        raise ValueError("latency_hours must be >= 0")

    if now_utc is None:
        current_time_utc = datetime.now(timezone.utc)
    else:
        current_time_utc = _ensure_utc(now_utc)

    reference_utc = current_time_utc - timedelta(hours=latency_hours)
    run_datetime_utc = _latest_run_datetime_utc(reference_utc)

    current_time_local = current_time_utc.astimezone(CUENCA_TIMEZONE)
    run_datetime_local = run_datetime_utc.astimezone(CUENCA_TIMEZONE)

    return EcmwfRunSelection(
        run_date=run_datetime_utc.strftime("%Y%m%d"),
        run_time=run_datetime_utc.strftime("%H"),
        run_datetime_utc=run_datetime_utc,
        run_datetime_local=run_datetime_local,
        current_time_utc=current_time_utc,
        current_time_local=current_time_local,
    )


def compute_valid_time(
    run_datetime: datetime,
    step_hours: int,
) -> ForecastValidTime:
    """
    Compute forecast valid time in UTC and Cuenca local time.

    Parameters
    ----------
    run_datetime:
        Run datetime in UTC (aware preferred; naive treated as UTC).
    step_hours:
        Forecast lead time in hours.
    """
    if step_hours < 0:
        raise ValueError("step_hours must be >= 0")

    run_datetime_utc = _ensure_utc(run_datetime)
    valid_time_utc = run_datetime_utc + timedelta(hours=step_hours)
    valid_time_local = valid_time_utc.astimezone(CUENCA_TIMEZONE)

    return ForecastValidTime(
        valid_time_utc=valid_time_utc,
        valid_time_local=valid_time_local,
    )


if __name__ == "__main__":
    run = get_latest_ecmwf_run()
    print(run)
