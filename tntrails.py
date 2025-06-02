import os
import math
import requests
from PIL import Image, ImageDraw
import geopandas as gpd
import mercantile
from pyproj import Transformer

# ---------------------------
# CONFIGURATION
# ---------------------------
STADIA_API_KEY = os.environ.get('STADIA_API_KEY')
ZOOM = 14
TILE_SIZE = 256
OUTPUT_WIDTH, OUTPUT_HEIGHT = 10800, 7200
TRAILS_FILE = "data/TSP-0252.geojson"

# 3:2 landscape bounding box (centered around Savage Gulf)
min_lon, min_lat = -85.7007558896214, 35.3872
max_lon, max_lat = -85.5392225741364, 35.4948

# ---------------------------
# TILE STITCHING
# ---------------------------
tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, ZOOM))
tile_xs = sorted(set(t.x for t in tiles))
tile_ys = sorted(set(t.y for t in tiles))

img_width = len(tile_xs) * TILE_SIZE
img_height = len(tile_ys) * TILE_SIZE
base_img = Image.new("RGB", (img_width, img_height))

print(f"Downloading {len(tiles)} tiles...")

for tile in tiles:
    url = f"https://tiles.stadiamaps.com/tiles/stamen_terrain/{ZOOM}/{tile.x}/{tile.y}.jpg?api_key={STADIA_API_KEY}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        tile_img = Image.open(r.raw)
        x_offset = tile_xs.index(tile.x) * TILE_SIZE
        y_offset = tile_ys.index(tile.y) * TILE_SIZE
        base_img.paste(tile_img, (x_offset, y_offset))
    else:
        print(f"Tile {tile.x},{tile.y} failed to load")

# ---------------------------
# TRAIL OVERLAY
# ---------------------------
print("Overlaying trails...")

# Convert bounds to Web Mercator
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
minx, miny = transformer.transform(min_lon, min_lat)
maxx, maxy = transformer.transform(max_lon, max_lat)

# Load and reproject GeoJSON
gdf = gpd.read_file(TRAILS_FILE).to_crs("EPSG:3857")

# Calculate pixel scale
scale_x = img_width / (maxx - minx)
scale_y = img_height / (maxy - miny)

draw = ImageDraw.Draw(base_img)

for geom in gdf.geometry:
    if geom is None:
        continue
    if geom.geom_type == "LineString":
        coords = list(geom.coords)
    elif geom.geom_type == "MultiLineString":
        coords = [pt for line in geom for pt in line.coords]
    else:
        continue
    points = [((x - minx) * scale_x, img_height - (y - miny) * scale_y) for x, y in coords]
    if points:
        draw.line(points, fill=(255, 102, 0), width=3)

# ---------------------------
# FINAL RESIZE
# ---------------------------
print("Resizing to final print resolution...")
final_img = base_img.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.LANCZOS)
final_img.save("trail_map_landscape.png")
print("✅ Done! Saved to trail_map_landscape.png")
