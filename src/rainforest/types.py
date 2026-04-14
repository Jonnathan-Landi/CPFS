from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ZoneObservation:
    zone_id: str
    cloud_index: float
    humidity_index: float
    satellite_cold_cloud: float
    recent_rain_mm: float


@dataclass
class ForecastRow:
    zone_id: str
    horizon_h: int
    rain_probability: float
    expected_intensity_mm: float
    event_type: str


@dataclass
class RunResult:
    run_id: str
    status: str
    warnings: List[str]
    rows: List[ForecastRow]
