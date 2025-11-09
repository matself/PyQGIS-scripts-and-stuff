# ---------------------------------------------------------
# LANTMÄTERIET STAC API EXAMPLE SCRIPT
# ---------------------------------------------------------
# Purpose:
#   Example of how to query Lantmäteriet’s STAC APIs for imagery (“bild”)
#   and produce a GeoPackage with footprints or centroids of available tiles.
#
# Collaboration:
#   Developed jointly through discussion between Mats Elfström and ChatGPT (GPT-5)
#   as a reproducible example for use in QGIS / Python environments.
#
# License:
#   © Lantmäteriet – Data used under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
#   Derived example © 2025 Mats Elfström & contributors.
#
# Disclaimer:
#   The resulting GeoPackages contain open metadata, not imagery itself.
#   Redistribution of image data requires valid credentials and compliance
#   with Lantmäteriet’s open-data license conditions.
#
# Authentication:
#   Obtain your own API credentials from https://api.lantmateriet.se
#   Replace the placeholders below with your personal keys:
#
#     consumer_key    = "YOUR_CONSUMER_KEY_HERE"
#     consumer_secret = "YOUR_CONSUMER_SECRET_HERE"
#
#   Never share your personal keys publicly.
#
# Geographic constraint:
#   Update the variable “bbox_3006” (in SWEREF 99 TM, EPSG:3006)
#   to match your own area of interest:
#
#     bbox_3006 = (minE, minN, maxE, maxN)
#
# References:
#   STAC Bild (orthophotos):   https://api.lantmateriet.se/stac-bild/v1
#   STAC Höjd (elevation):     https://api.lantmateriet.se/stac-hojd/v1
#   STAC Laser:                https://api.lantmateriet.se/stac-laser/v1
#
# Tested Environment:
#   QGIS 3.44.x / Python 3.12
# ---------------------------------------------------------

import re
import requests
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject,
    QgsGeometry, QgsPointXY, QgsVectorLayer, QgsField, QgsFields,
    QgsFeature, QgsWkbTypes, QgsVectorFileWriter
)
from PyQt5.QtCore import QVariant

# ---------- 1) USER SETTINGS ----------
consumer_key    = "YOUR_CONSUMER_KEY_HERE"
consumer_secret = "YOUR_CONSUMER_SECRET_HERE"

# Geographic extent (SWEREF 99 TM, EPSG:3006)
bbox_epsg = 3006
bbox_3006 = (337500, 6127500, 487500, 6265000)   # Example: Skåne

# Output file
gpkg_path  = "C:/temp/ortofoto_footprints_example.gpkg"
layer_name = "ortofoto_footprints"

# ---------- 2) CONSTANTS ----------
STAC_BASE = "https://api.lantmateriet.se/stac-bild/v1"
TOKEN_URL = "https://api.lantmateriet.se/token"

# ---------- 3) HELPER FUNCTIONS ----------
def sweref3006_to_wgs84_bbox(b):
    crs_src = QgsCoordinateReferenceSystem("EPSG:3006")
    crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
    tr = QgsCoordinateTransform(crs_src, crs_dst, QgsProject.instance())
    (minE, minN, maxE, maxN) = b
    ll = tr.transform(minE, minN)
    ur = tr.transform(maxE, maxN)
    return (min(ll.x(), ur.x()), min(ll.y(), ur.y()), max(ll.x(), ur.x()), max(ll.y(), ur.y()))

def parse_ortofoto_id(tile_id):
    """Extract year, resolution (m), and campaign code from filename."""
    m = re.match(r'^o\d+_\d+_(\d+)_([a-z]{2})(\d{2})$', tile_id)
    if not m:
        return (None, None, None)
    res_cm = int(m.group(1))
    res_m = res_cm / 100.0
    camp_code = m.group(2)
    yy = int(m.group(3))
    year = 2000 + yy if yy <= 79 else 1900 + yy
    return (year, res_m, camp_code)

def get_token(key, secret):
    """Authenticate with Lantmäteriet’s API."""
    r = requests.post(TOKEN_URL, data={"grant_type": "client_credentials"}, auth=(key, secret))
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_items_for_ortofoto(bbox_wgs84, headers):
    """Fetch all ortofoto tiles within bbox using STAC /search."""
    items = []
    url = f"{STAC_BASE}/search"
    params = {"bbox": ",".join(map(str, bbox_wgs84)), "limit": 10000}
    while url:
        r = requests.get(url, headers=headers, params=params)
        if not r.ok:
            print(f"⚠️ HTTP {r.status_code}: {r.text[:200]}")
            break
        js = r.json()
        feats = js.get("features", [])
        items.extend(feats)
        next_url = None
        for link in js.get("links", []):
            if link.get("rel") == "next":
                next_url = link["href"]
                break
        url = next_url
        params = {}
        print(f"→ {len(items)} items so far …")
    print(f"✅ Done: {len(items)} items total")
    return items

# ---------- 4) PREPARE BBOX ----------
if bbox_epsg == 3006:
    bbox_wgs84 = sweref3006_to_wgs84_bbox(bbox_3006)
elif bbox_epsg == 4326:
    bbox_wgs84 = bbox_4326
else:
    raise Exception("bbox_epsg must be 3006 or 4326")

print("Requesting access token …")
token = get_token(consumer_key, consumer_secret)
headers = {"Authorization": f"Bearer {token}"}
print("✅ Token OK")

# ---------- 5) FETCH ITEMS ----------
print("Fetching ortofoto items via /search …")
feats = fetch_items_for_ortofoto(bbox_wgs84, headers)

# ---------- 6) CREATE MEMORY LAYER ----------
fields = QgsFields()
fields.append(QgsField("id", QVariant.String))
fields.append(QgsField("datetime", QVariant.String))
fields.append(QgsField("href", QVariant.String))
fields.append(QgsField("year", QVariant.Int))
fields.append(QgsField("res_m", QVariant.Double))
fields.append(QgsField("campaign", QVariant.String))

vl = QgsVectorLayer("Polygon?crs=EPSG:4326", layer_name, "memory")
dp = vl.dataProvider()
dp.addAttributes(fields)
vl.updateFields()

# ---------- 7) POPULATE POLYGONS ----------
total = 0
for f in feats:
    tid = f.get("id")
    href = None
    assets = f.get("assets", {})
    if assets:
        href = assets.get("data", {}).get("href")
        if not href:
            try:
                href = next(iter(assets.values()))["href"]
            except Exception:
                href = None

    dt = f.get("properties", {}).get("datetime", "")
    bb = f.get("bbox")
    if not bb:
        continue

    minx, miny, maxx, maxy = bb
    ring = [
        QgsPointXY(minx, miny),
        QgsPointXY(maxx, miny),
        QgsPointXY(maxx, maxy),
        QgsPointXY(minx, maxy),
        QgsPointXY(minx, miny)
    ]
    geom = QgsGeometry.fromPolygonXY([ring])

    year, res_m, camp = parse_ortofoto_id(tid) if tid else (None, None, None)

    feat = QgsFeature()
    feat.setFields(fields)
    feat.setGeometry(geom)
    feat.setAttribute("id", tid)
    feat.setAttribute("datetime", dt)
    feat.setAttribute("href", href)
    if year is not None: feat.setAttribute("year", year)
    if res_m is not None: feat.setAttribute("res_m", float(res_m))
    if camp is not None: feat.setAttribute("campaign", camp)
    dp.addFeature(feat)
    total += 1

print(f"Total features: {total}")

# ---------- 8) WRITE TO GPKG ----------
writer = QgsVectorFileWriter(
    gpkg_path,
    "UTF-8",
    vl.fields(),
    QgsWkbTypes.Polygon,
    vl.crs(),
    "GPKG"
)
for f in vl.getFeatures():
    writer.addFeature(f)
del writer

# --- safer layer load ---
layer_uri = f"{gpkg_path}|layername={layer_name}"
final_layer = QgsVectorLayer(layer_uri, layer_name, "ogr")

if final_layer.isValid():
    QgsProject.instance().addMapLayer(final_layer)
    print(f"✅ Layer loaded from {layer_uri}")
else:
    print(f"⚠️ Could not auto-load layer from {layer_uri}. Load manually if needed.")

# ---------------------------------------------------------
# EXAMPLES – Adjust bbox for other regions in Sweden
# ---------------------------------------------------------
# Stockholm area:
# bbox_3006 = (650000, 6570000, 680000, 6600000)
#
# Göteborg area:
# bbox_3006 = (310000, 6380000, 340000, 6400000)
#
# Norrbotten area:
# bbox_3006 = (730000, 7280000, 820000, 7400000)
#
# Smaller test (Ystad region):
# bbox_3006 = (420000, 6155000, 455000, 6180000)
#
# Replace and re-run.
# ---------------------------------------------------------
