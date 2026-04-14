from __future__ import annotations

from typing import Dict, List

from .types import ZoneObservation


def build_predictors(observations: List[ZoneObservation]) -> Dict[str, Dict[str, float]]:
    predictors: Dict[str, Dict[str, float]] = {}

    for obs in observations:
        moisture_signal = (0.55 * obs.humidity_index) + (0.45 * obs.cloud_index)
        convective_signal = (0.65 * obs.satellite_cold_cloud) + (0.35 * obs.cloud_index)

        predictors[obs.zone_id] = {
            "moisture_signal": moisture_signal,
            "convective_signal": convective_signal,
            "persistence_rain": min(1.0, obs.recent_rain_mm / 10.0),
        }

    return predictors
