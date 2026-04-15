from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .data_sources import read_latest_observations, read_zones
from .features import build_predictors
from .inference import run_inference
from .products import write_outputs
from .quality import basic_quality_check
from .types import RunResult
from .visualization import generate_visual_products


def execute_nowcast(config: Dict, force: bool = False) -> RunResult:
    warnings: List[str] = []
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    paths = config["paths"]
    zones_path = paths["zones_geojson"]
    observations_path = paths["latest_observations"]
    outputs_dir = paths["outputs_dir"]
    boundary_path = config.get("domain", {}).get("boundary_path")
    zones_input_crs = config.get("spatial", {}).get("zones_input_crs")

    _validate_critical_inputs(config, paths)

    zone_ids, zone_warnings = read_zones(
        zones_geojson_path=zones_path,
        ecuador_boundary_path=boundary_path,
        zones_input_crs=zones_input_crs,
    )
    warnings.extend(zone_warnings)
    source_ts, observations, ingest_warnings = read_latest_observations(observations_path, zone_ids)
    warnings.extend(ingest_warnings)

    if _should_skip_due_to_same_source(outputs_dir, source_ts) and not force:
        warnings.append("No new source data; run skipped")
        result = RunResult(run_id=run_id, status="Parcial", warnings=warnings, rows=[])
        write_outputs(outputs_dir, result, source_ts)
        return result

    cleaned_observations, qc_warnings = basic_quality_check(observations)
    warnings.extend(qc_warnings)

    predictors = build_predictors(cleaned_observations)
    rows = run_inference(
        predictors=predictors,
        horizons=config["horizons_hours"],
        weak_max_mm=float(config["event_thresholds_mm"]["weak_max"]),
        moderate_max_mm=float(config["event_thresholds_mm"]["moderate_max"]),
        convective_threshold=float(config["convective_threshold"]),
    )

    visual_artifacts, visual_warnings = generate_visual_products(
        rows=rows,
        config=config,
        run_id=run_id,
        source_timestamp=source_ts,
    )
    warnings.extend(visual_warnings)

    status = "Exitosa" if not warnings else "Exitosa con advertencias"
    result = RunResult(run_id=run_id, status=status, warnings=warnings, rows=rows)
    write_outputs(outputs_dir, result, source_ts, visual_products=visual_artifacts)
    return result


def _validate_critical_inputs(config: Dict, paths: Dict[str, str]) -> None:
    missing_critical: List[str] = []
    domain = config.get("domain", {})
    for critical_key in config.get("critical_inputs", []):
        path_value = paths.get(critical_key)
        if path_value is None:
            path_value = domain.get(critical_key)
        if path_value is None or not Path(path_value).exists():
            missing_critical.append(critical_key)

    if missing_critical:
        missing = ", ".join(missing_critical)
        raise RuntimeError(f"Critical inputs missing: {missing}")


def _should_skip_due_to_same_source(outputs_dir: str, source_ts: str) -> bool:
    latest_file = Path(outputs_dir) / "latest_run.json"
    if not latest_file.exists() or source_ts in {"unknown", "missing-input"}:
        return False

    import json

    previous = json.loads(latest_file.read_text(encoding="utf-8"))
    return previous.get("source_timestamp_utc") == source_ts
