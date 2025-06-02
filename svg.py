import geopandas as gpd
import matplotlib.pyplot as plt

# Load trail GeoJSON
trails = gpd.read_file("data/TSP-0252.geojson").to_crs(epsg=3857)

# Create figure in landscape aspect (3:2)
fig, ax = plt.subplots(figsize=(36, 24), dpi=100)

# Plot trails
trails.plot(ax=ax, color='orangered', linewidth=1.5)

# Optional: clean style
ax.set_axis_off()
# ax.set_title("Public Trails", fontsize=24, weight='bold')

# Save as SVG
fig.savefig("trail_map.svg", format="svg", bbox_inches="tight")
print("✅ Saved to trail_map.svg")
