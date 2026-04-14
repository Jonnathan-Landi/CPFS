from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .types import ForecastRow, RunResult


def write_outputs(outputs_dir: str, result: RunResult, source_timestamp: str) -> None:
    out_dir = Path(outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / f"nowcast_{result.run_id}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["zone_id", "horizon_h", "rain_probability", "expected_intensity_mm", "event_type"],
        )
        writer.writeheader()
        for row in result.rows:
            writer.writerow(asdict(row))

    json_path = out_dir / f"run_{result.run_id}.json"
    payload = {
        "run_id": result.run_id,
        "status": result.status,
        "source_timestamp_utc": source_timestamp,
        "warnings": result.warnings,
        "rows": [asdict(r) for r in result.rows],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    latest_path = out_dir / "latest_run.json"
    latest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def summarize_rows(rows: List[ForecastRow]) -> str:
    if not rows:
        return "No rows generated"
    zone_count = len({r.zone_id for r in rows})
    return f"Generated {len(rows)} rows for {zone_count} zones"
