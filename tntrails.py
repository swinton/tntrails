import os
import math
import mercantile
import geopandas as gpd
from PIL import Image, ImageDraw
import requests

# --- CONFIG ---
STADIA_API_KEY = os.environ.get('STADIA_API_KEY')
ZOOM = 14  # Adjust for detail
TILE_SIZE = 256
OUTPUT_WIDTH, OUTPUT_HEIGHT = 7200, 10800
TRAILS_FILE = 'data/TSP-0252.geojson'

# Bounding box (Savage Gulf example)
# Note, modified to fit 3:2 aspect ratio with landscape orientation
min_lon = -85.7007558896214
max_lon = -85.5392225741364
min_lat = 35.3872
max_lat = 35.4948
# min_lon, min_lat = -85.7007558896214, 35.403643645658
# max_lon, max_lat = -85.5392225741364, 35.4783543541948
# min_lon, min_lat = -85.8, 35.4
# max_lon, max_lat = -85.7, 35.46

# Tile range
tiles = list(mercantile.tiles(min_lon, min_lat, max_lon, max_lat, ZOOM))
tile_xs = sorted(set(t.x for t in tiles))
tile_ys = sorted(set(t.y for t in tiles))

width = len(tile_xs) * TILE_SIZE
height = len(tile_ys) * TILE_SIZE

print(f"Creating base map of size {width}x{height} pixels from {len(tiles)} tiles")

# Create blank image
base_img = Image.new("RGB", (width, height))

# Download and stitch tiles
for tile in tiles:
    # url = f"https://tiles.stadiamaps.com/tiles/stamen_watercolor/{ZOOM}/{tile.x}/{tile.y}.jpg?api_key={STADIA_API_KEY}"
    url = f"https://tiles.stadiamaps.com/tiles/stamen_terrain/{ZOOM}/{tile.x}/{tile.y}.jpg?api_key={STADIA_API_KEY}"
    print(url)
    tile_img = Image.open(requests.get(url, stream=True).raw)

    x_index = tile_xs.index(tile.x)
    y_index = tile_ys.index(tile.y)
    base_img.paste(tile_img, (x_index * TILE_SIZE, y_index * TILE_SIZE))

# --- Overlay trails ---
print("Overlaying trails...")
gdf = gpd.read_file(TRAILS_FILE).to_crs("EPSG:3857")  # Web mercator

# Convert lat/lon bounds to mercator
from pyproj import Transformer
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
minx, miny = transformer.transform(min_lon, min_lat)
maxx, maxy = transformer.transform(max_lon, max_lat)

scale_x = width / (maxx - minx)
scale_y = height / (maxy - miny)

draw = ImageDraw.Draw(base_img)

for geom in gdf.geometry:
    if geom is None:
        continue
    coords = list(geom.coords) if geom.geom_type == "LineString" else []
    points = [((x - minx) * scale_x, height - (y - miny) * scale_y) for x, y in coords]
    if points:
        draw.line(points, fill=(255, 102, 0), width=3)

# --- Resize to 7200x10800 ---
print("Resizing and saving...")
resized = base_img.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.LANCZOS)
resized.save("trail_map_highres.png")
