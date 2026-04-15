import re

filepath = r"d:\Windows\GitHub\CPFS\src\rainforest\visualization.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace edgecolor to remove grid
content = re.sub(r'edgecolor="#f5f5f5"', 'edgecolor="none"', content)
content = re.sub(r'edgecolor="#f8f8f8"', 'edgecolor="none"', content)

# 2. Remove linewidth that shows grid
content = re.sub(r'linewidth=1\.1', 'linewidth=0.0', content)

# 3. Replace annotation calls with wind field
content = re.sub(
    r'_annotate_zone_labels\(ax=ax, gdf=merged\)',
    '_add_wind_field(ax=ax, gdf=merged)',
    content
)

# 4. Update base layers function
old_base = """def _draw_base_layers(ax, base_map, zones, canton) -> None:
	if base_map is not None and not base_map.empty:
		base_map.plot(ax=ax, facecolor="#efefef", edgecolor="#7a7a7a", linewidth=0.8, alpha=1.0)
	else:
		zones.boundary.plot(ax=ax, color="#888888", linewidth=0.8)

	zones.boundary.plot(ax=ax, color="#d7d7d7", linewidth=0.6, alpha=0.7)

	if canton is not None and not canton.empty:
		canton.plot(ax=ax, facecolor="none", edgecolor="#111111", linewidth=1.5, alpha=1.0)"""

new_base = """def _draw_base_layers(ax, base_map, zones, canton) -> None:
	if base_map is not None and not base_map.empty:
		base_map.plot(ax=ax, facecolor="#e8e8e8", edgecolor="#999999", linewidth=0.5, alpha=0.8)

	if canton is not None and not canton.empty:
		canton.plot(ax=ax, facecolor="none", edgecolor="#111111", linewidth=2.0, alpha=0.9)"""

content = content.replace(old_base, new_base)

# 5. Add wind field function
wind_func = """

def _add_wind_field(ax, gdf) -> None:
	\"\"\"Add synthetic wind arrows to the map for visual dynamics.\"\"\"
	import numpy as np

	points = gdf.representative_point()
	grid_sample = min(20, len(gdf) // 4)
	if grid_sample < 1:
		grid_sample = 1

	for idx in range(0, len(points), grid_sample):
		point = points.iloc[idx]
		u_wind = np.sin(float(point.x) / 5000) * 3
		v_wind = np.cos(float(point.y) / 5000) * 3
		ax.arrow(
			point.x, point.y, u_wind, v_wind,
			head_width=0.02, head_length=0.02,
			fc="#555555", ec="#555555", alpha=0.4, linewidth=0.7,
			length_includes_head=True
		)

"""

if "_add_wind_field" not in content:
    idx = content.find("def _annotate_zone_labels")
    if idx > 0:
        content = content[:idx] + wind_func + content[idx:]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Updated visualization.py: removed grids, labels, added wind field")
