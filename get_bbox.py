import geopandas as gpd
import sys

if len(sys.argv) != 2:
    print("Usage: poetry run python get_bbox.py <path_to_geojson>")
    sys.exit(1)

file_path = sys.argv[1]
gdf = gpd.read_file(file_path)
minx, miny, maxx, maxy = gdf.total_bounds

print(f"BBOX: ({miny}, {minx}, {maxy}, {maxx})")  # (south, west, north, east)
