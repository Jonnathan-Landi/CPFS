from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from .types import ForecastRow


def generate_visual_products(
	rows: List[ForecastRow],
	config: Dict,
	run_id: str,
	source_timestamp: str,
) -> Tuple[Dict[str, object], List[str]]:
	warnings: List[str] = []
	artifacts: Dict[str, object] = {}

	vis_cfg = config.get("visualization", {})
	if not vis_cfg.get("enabled", True):
		return artifacts, warnings

	if not rows:
		warnings.append("visualization skipped: no forecast rows available")
		return artifacts, warnings

	try:
		import geopandas as gpd
		import pandas as pd
		import matplotlib.pyplot as plt
		import matplotlib.patches as mpatches
		from matplotlib.colors import Normalize
	except ModuleNotFoundError as exc:
		warnings.append(f"visualization skipped: missing dependency ({exc.name})")
		return artifacts, warnings

	try:
		from PIL import Image
	except ModuleNotFoundError:
		Image = None
		warnings.append("Pillow not available; GIF animations will be skipped")

	paths = config.get("paths", {})
	outputs_dir = Path(paths.get("outputs_dir", "outputs"))
	zones_path = Path(paths.get("zones_geojson", "zones/zones.geojson"))
	boundary_path = Path(config.get("domain", {}).get("boundary_path", ""))
	canton_path = Path(vis_cfg.get("overlay_canton_path", ""))

	if not zones_path.exists():
		warnings.append("visualization skipped: zones file missing")
		return artifacts, warnings

	visuals_dir = outputs_dir / "visuals" / run_id
	visuals_dir.mkdir(parents=True, exist_ok=True)

	zones = gpd.read_file(zones_path)
	if zones.empty or "zone_id" not in zones.columns:
		warnings.append("visualization skipped: zones file has no valid zone_id geometries")
		return artifacts, warnings

	if zones.crs is None:
		zones_crs = config.get("spatial", {}).get("zones_input_crs", "EPSG:4326")
		zones = zones.set_crs(zones_crs)
		warnings.append(f"visualization: zones CRS missing, assumed {zones_crs}")

	base_map = None
	if boundary_path.exists():
		base_map = gpd.read_file(boundary_path)
		if base_map.empty:
			base_map = None
			warnings.append("visualization: Ecuador boundary layer is empty")
	else:
		warnings.append("visualization: Ecuador boundary not found, using zones extent as base")

	canton = None
	if canton_path.exists():
		canton = gpd.read_file(canton_path)
		if canton.empty:
			canton = None
			warnings.append("visualization: Cuenca canton layer is empty")
	else:
		warnings.append("visualization: Cuenca canton overlay not found")

	map_crs = None
	if base_map is not None and base_map.crs is not None:
		map_crs = base_map.crs
	elif zones.crs is not None:
		map_crs = zones.crs

	if map_crs is None:
		warnings.append("visualization skipped: unable to determine map CRS")
		return artifacts, warnings

	zones = zones.to_crs(map_crs)
	if base_map is not None and base_map.crs is not None:
		base_map = base_map.to_crs(map_crs)
	if canton is not None and canton.crs is not None:
		canton = canton.to_crs(map_crs)

	frame_df = pd.DataFrame([asdict(row) for row in rows])
	if frame_df.empty:
		warnings.append("visualization skipped: forecast dataframe is empty")
		return artifacts, warnings

	horizons = sorted(frame_df["horizon_h"].unique().tolist())
	figure_size = tuple(vis_cfg.get("figure_size", [8, 8]))
	dpi = int(vis_cfg.get("dpi", 170))

	artifacts["maps"] = {}

	prob_paths = _render_continuous_maps(
		frame_df=frame_df,
		zones=zones,
		base_map=base_map,
		canton=canton,
		horizons=horizons,
		value_col="rain_probability",
		title_label="Probabilidad de lluvia",
		colorbar_label="Probabilidad [0-1]",
		cmap="cool",
		norm=Normalize(vmin=0.0, vmax=1.0),
		prefix="probability",
		source_timestamp=source_timestamp,
		out_dir=visuals_dir,
		figure_size=figure_size,
		dpi=dpi,
		plt=plt,
	)
	artifacts["maps"]["probability"] = [p.as_posix() for p in prob_paths]

	max_intensity = max(1.0, float(frame_df["expected_intensity_mm"].max()))
	intensity_paths = _render_continuous_maps(
		frame_df=frame_df,
		zones=zones,
		base_map=base_map,
		canton=canton,
		horizons=horizons,
		value_col="expected_intensity_mm",
		title_label="Intensidad esperada",
		colorbar_label="Intensidad [mm]",
		cmap="Blues_r",
		norm=Normalize(vmin=0.0, vmax=max_intensity),
		prefix="intensity",
		source_timestamp=source_timestamp,
		out_dir=visuals_dir,
		figure_size=figure_size,
		dpi=dpi,
		plt=plt,
	)
	artifacts["maps"]["intensity"] = [p.as_posix() for p in intensity_paths]

	event_palette = {
		"Sin lluvia": "#f2f2f2",
		"Lluvia debil": "#8fd3ff",
		"Lluvia moderada": "#2d8bd3",
		"Convectivo intenso": "#f28e2b",
	}
	event_paths = _render_event_maps(
		frame_df=frame_df,
		zones=zones,
		base_map=base_map,
		canton=canton,
		horizons=horizons,
		palette=event_palette,
		source_timestamp=source_timestamp,
		out_dir=visuals_dir,
		figure_size=figure_size,
		dpi=dpi,
		plt=plt,
		mpatches=mpatches,
	)
	artifacts["maps"]["event_type"] = [p.as_posix() for p in event_paths]

	if vis_cfg.get("generate_animation", True):
		artifacts["animations"] = {}
		if Image is None:
			warnings.append("animations skipped: Pillow dependency missing")
		else:
			prob_gif = _build_gif(prob_paths, visuals_dir / "animation_probability.gif", Image)
			intensity_gif = _build_gif(intensity_paths, visuals_dir / "animation_intensity.gif", Image)
			event_gif = _build_gif(event_paths, visuals_dir / "animation_event_type.gif", Image)
			if prob_gif is not None:
				artifacts["animations"]["probability"] = prob_gif.as_posix()
			if intensity_gif is not None:
				artifacts["animations"]["intensity"] = intensity_gif.as_posix()
			if event_gif is not None:
				artifacts["animations"]["event_type"] = event_gif.as_posix()

	if vis_cfg.get("generate_video", True):
		artifacts["videos"] = {}
		try:
			import cv2
		except ModuleNotFoundError:
			warnings.append("videos skipped: opencv-python dependency missing")
		else:
			video_fps = int(vis_cfg.get("video_fps", 2))
			prob_mp4 = _build_video(prob_paths, visuals_dir / "video_probability.mp4", cv2, video_fps)
			intensity_mp4 = _build_video(intensity_paths, visuals_dir / "video_intensity.mp4", cv2, video_fps)
			event_mp4 = _build_video(event_paths, visuals_dir / "video_event_type.mp4", cv2, video_fps)
			if prob_mp4 is not None:
				artifacts["videos"]["probability"] = prob_mp4.as_posix()
			if intensity_mp4 is not None:
				artifacts["videos"]["intensity"] = intensity_mp4.as_posix()
			if event_mp4 is not None:
				artifacts["videos"]["event_type"] = event_mp4.as_posix()

	return artifacts, warnings


def _render_continuous_maps(
	frame_df,
	zones,
	base_map,
	canton,
	horizons,
	value_col: str,
	title_label: str,
	colorbar_label: str,
	cmap: str,
	norm,
	prefix: str,
	source_timestamp: str,
	out_dir: Path,
	figure_size,
	dpi: int,
	plt,
) -> List[Path]:
	output_paths: List[Path] = []
	for horizon in horizons:
		subset = frame_df[frame_df["horizon_h"] == horizon]
		merged = zones.merge(subset[["zone_id", value_col]], on="zone_id", how="left")

		fig, ax = plt.subplots(figsize=figure_size, dpi=dpi)
		_draw_base_layers(ax=ax, base_map=base_map, zones=zones, canton=canton)

		merged.plot(
			ax=ax,
			column=value_col,
			cmap=cmap,
			norm=norm,
			edgecolor="none",
			linewidth=0.0,
			alpha=0.95,
			legend=True,
			legend_kwds={"label": colorbar_label, "shrink": 0.72},
		)

		_add_wind_field(ax=ax, gdf=merged, horizon_h=horizon)
		ax.set_title(_build_map_title(title_label=title_label, source_timestamp=source_timestamp, horizon_h=horizon), fontsize=10)
		ax.set_axis_off()
		fig.tight_layout()

		out_path = out_dir / f"{prefix}_{horizon:02d}h.png"
		fig.savefig(out_path, bbox_inches="tight")
		plt.close(fig)
		output_paths.append(out_path)

	return output_paths


def _render_event_maps(
	frame_df,
	zones,
	base_map,
	canton,
	horizons,
	palette: Dict[str, str],
	source_timestamp: str,
	out_dir: Path,
	figure_size,
	dpi: int,
	plt,
	mpatches,
) -> List[Path]:
	output_paths: List[Path] = []
	for horizon in horizons:
		subset = frame_df[frame_df["horizon_h"] == horizon]
		merged = zones.merge(subset[["zone_id", "event_type"]], on="zone_id", how="left")
		merged["_event_color"] = merged["event_type"].map(palette).fillna("#cccccc")

		fig, ax = plt.subplots(figsize=figure_size, dpi=dpi)
		_draw_base_layers(ax=ax, base_map=base_map, zones=zones, canton=canton)

		merged.plot(
			ax=ax,
			color=merged["_event_color"],
			edgecolor="none",
			linewidth=0.0,
			alpha=0.95,
		)

		_add_wind_field(ax=ax, gdf=merged, horizon_h=horizon)
		handles = [mpatches.Patch(color=color, label=label) for label, color in palette.items()]
		ax.legend(handles=handles, title="Tipo de evento", loc="lower left", frameon=True)

		ax.set_title(_build_map_title(title_label="Tipo de evento esperado", source_timestamp=source_timestamp, horizon_h=horizon), fontsize=10)
		ax.set_axis_off()
		fig.tight_layout()

		out_path = out_dir / f"event_type_{horizon:02d}h.png"
		fig.savefig(out_path, bbox_inches="tight")
		plt.close(fig)
		output_paths.append(out_path)

	return output_paths


def _draw_base_layers(ax, base_map, zones, canton) -> None:
	if base_map is not None and not base_map.empty:
		base_map.plot(ax=ax, facecolor="#e8e8e8", edgecolor="#999999", linewidth=0.5, alpha=0.8)

	if canton is not None and not canton.empty:
		canton.plot(ax=ax, facecolor="none", edgecolor="#111111", linewidth=2.0, alpha=0.9)


def _add_wind_field(ax, gdf, horizon_h: int) -> None:
	"""Draw wind as motion lines instead of arrows, with phase shift per horizon."""
	import numpy as np

	if gdf.empty:
		return

	x_min, x_max = ax.get_xlim()
	y_min, y_max = ax.get_ylim()
	x_span = max(1.0, x_max - x_min)
	y_span = max(1.0, y_max - y_min)

	nx = 12
	ny = 9
	x_grid = np.linspace(x_min + 0.08 * x_span, x_max - 0.08 * x_span, nx)
	y_grid = np.linspace(y_min + 0.08 * y_span, y_max - 0.08 * y_span, ny)

	phase = horizon_h * 0.55
	line_len = 0.022 * x_span

	for y in y_grid:
		for x in x_grid:
			u = np.sin((x / (0.19 * x_span)) + phase) * 0.8 + np.cos((y / (0.21 * y_span)) - phase) * 0.6
			v = np.cos((x / (0.25 * x_span)) - phase) * 0.5 + np.sin((y / (0.17 * y_span)) + phase) * 0.9

			mag = np.hypot(u, v)
			if mag < 0.08:
				continue

			dx = (u / mag) * line_len
			dy = (v / mag) * line_len * (y_span / x_span)

			x0 = x - dx * 0.65
			y0 = y - dy * 0.65
			x1 = x + dx * 0.65
			y1 = y + dy * 0.65

			ax.plot([x0, x1], [y0, y1], color="#4f5964", linewidth=1.1, alpha=0.34, solid_capstyle="round", zorder=2)
			ax.plot([x1], [y1], marker=".", color="#4f5964", markersize=1.5, alpha=0.45, zorder=2)


def _build_map_title(title_label: str, source_timestamp: str, horizon_h: int) -> str:
	base_dt = _parse_source_timestamp(source_timestamp)
	if base_dt is None:
		return f"{title_label} | Horizonte +{horizon_h}h\\nFuente: {source_timestamp}"

	valid_dt = base_dt + timedelta(hours=horizon_h)
	base_txt = base_dt.strftime("%Y-%m-%d %H:%M UTC")
	valid_txt = valid_dt.strftime("%Y-%m-%d %H:%M UTC")
	return f"{title_label} | +{horizon_h}h\\nEmision: {base_txt} | Valido: {valid_txt}"


def _parse_source_timestamp(source_timestamp: str):
	text = source_timestamp.strip()
	if text.endswith("Z"):
		text = text[:-1] + "+00:00"
	try:
		dt = datetime.fromisoformat(text)
	except ValueError:
		return None
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	return dt.astimezone(timezone.utc)



def _annotate_zone_labels(ax, gdf) -> None:
	points = gdf.representative_point()
	for idx, point in enumerate(points.tolist()):
		zone_id = str(gdf.iloc[idx]["zone_id"])
		ax.annotate(
			zone_id,
			xy=(point.x, point.y),
			xytext=(3, 3),
			textcoords="offset points",
			fontsize=7,
			color="#1f1f1f",
			bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.6},
		)


def _build_gif(frame_paths: List[Path], target_path: Path, Image):
	if len(frame_paths) < 2:
		return None

	images = [Image.open(path).convert("P", palette=Image.ADAPTIVE) for path in frame_paths]
	images[0].save(
		target_path,
		save_all=True,
		append_images=images[1:],
		optimize=False,
		duration=1000,
		loop=0,
	)
	for img in images:
		img.close()
	return target_path


def _build_video(frame_paths: List[Path], target_path: Path, cv2, fps: int):
	if len(frame_paths) < 2:
		return None

	frames = [cv2.imread(str(p)) for p in frame_paths]
	if not frames or frames[0] is None:
		return None

	height, width = frames[0].shape[:2]
	fourcc = cv2.VideoWriter_fourcc(*"mp4v")
	writer = cv2.VideoWriter(str(target_path), fourcc, fps, (width, height))

	for frame in frames:
		writer.write(frame)

	writer.release()
	return target_path if target_path.exists() else None
