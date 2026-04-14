from __future__ import annotations

from typing import Dict, List

from .types import ForecastRow


def run_inference(
    predictors: Dict[str, Dict[str, float]],
    horizons: List[int],
    weak_max_mm: float,
    moderate_max_mm: float,
    convective_threshold: float,
) -> List[ForecastRow]:
    rows: List[ForecastRow] = []

    for zone_id, feats in predictors.items():
        base_probability = _clip01(
            0.50 * feats["moisture_signal"]
            + 0.35 * feats["convective_signal"]
            + 0.15 * feats["persistence_rain"]
        )

        for horizon_h in horizons:
            horizon_factor = 1.0 - (0.05 * (horizon_h - 1))
            probability = _clip01(base_probability * horizon_factor)

            intensity = max(
                0.0,
                (1.4 * feats["moisture_signal"] + 2.2 * feats["convective_signal"]) * horizon_h,
            )

            event_type = classify_event(
                probability=probability,
                intensity_mm=intensity,
                convective_signal=feats["convective_signal"],
                weak_max_mm=weak_max_mm,
                moderate_max_mm=moderate_max_mm,
                convective_threshold=convective_threshold,
            )

            rows.append(
                ForecastRow(
                    zone_id=zone_id,
                    horizon_h=horizon_h,
                    rain_probability=round(probability, 3),
                    expected_intensity_mm=round(intensity, 2),
                    event_type=event_type,
                )
            )

    return rows


def classify_event(
    probability: float,
    intensity_mm: float,
    convective_signal: float,
    weak_max_mm: float,
    moderate_max_mm: float,
    convective_threshold: float,
) -> str:
    if probability < 0.20 or intensity_mm < 0.2:
        return "Sin lluvia"
    if intensity_mm <= weak_max_mm:
        return "Lluvia debil"
    if intensity_mm <= moderate_max_mm:
        return "Lluvia moderada"
    if convective_signal >= convective_threshold and probability >= 0.55:
        return "Convectivo intenso"
    return "Lluvia moderada"


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
