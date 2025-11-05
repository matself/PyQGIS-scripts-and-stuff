# -*- coding: utf-8 -*-
"""
Belägenhetsadresser Index Builder (Centroids Only)
==================================================

Creates a GeoPackage containing one feature per Swedish municipality (centroid),
with clickable download links to Lantmäteriet’s “Belägenhetsadresser”
datasets.

Author: Mats Elfström & Gemini (Google 2025)
-----------------------------------------------------
Context:
  • Built for QGIS 3.44 (PyQGIS)
  • Focuses on the reliable creation of the Point layer only.

Usage:
  1. **EDIT LM_USER and LM_PASS** below with your credentials.
  2. Run in the QGIS Python Console.
  3. Resulting GeoPackage: C:/temp/belagenhetsadresser_index.gpkg
"""

# --------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------
import os
import time
import requests
import sys 
from qgis.core import (
    QgsVectorLayer, QgsProject, QgsField, QgsFields, QgsFeature,
    QgsGeometry, QgsRectangle, QgsVectorFileWriter,
    QgsCoordinateReferenceSystem, QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant

# --------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------
# Use os.path.join for better cross-platform compatibility
OUT_DIR = "C:/temp"
OUT_FILE = "belagenhetsadresser_index.gpkg"
OUT_PATH = os.path.join(OUT_DIR, OUT_FILE)

API_URL = "https://api.lantmateriet.se/stac-vektor/v1/collections/belagenhetsadresser/items"
CRS = QgsCoordinateReferenceSystem("EPSG:3006")

# Polite fetch timing (avoid HTTP 429)
SLEEP_SECONDS = 1.5
RETRY_WAIT = 10

# --------------------------------------------------------------------
# AUTHENTICATION (MUST BE EDITED BEFORE USE)
# --------------------------------------------------------------------
# !!! WARNING: Replace the placeholders below with your actual authorized account credentials.
LM_USER = "YOUR_LANTMÄTERIET_USERNAME_HERE"
LM_PASS = "YOUR_LANTMÄTERIET_PASSWORD_HERE"

# Guardrail: Check if credentials are still placeholders for a graceful failure
if LM_USER == "YOUR_LANTMÄTERIET_USERNAME_HERE" or LM_PASS == "YOUR_LANTMÄTERIET_PASSWORD_HERE":
    error_msg = ("\n🚨 SCRIPT HALTED: Please replace LM_USER and LM_PASS with "
                 "your actual credentials in the script before running.")
    print(error_msg)
    # Raising a standard Exception halts the script without killing the QGIS Python Console.
    raise Exception("Authentication required.") 
    
# --------------------------------------------------------------------
# FETCH ALL FEATURES WITH PAGING + RATE-LIMIT HANDLING
# --------------------------------------------------------------------
print("📡 Fetching STAC features from Lantmäteriet...")
features = []
url = API_URL
page = 1

while url:
    print(f"→ Page {page}")
    # Pass authentication tuple for robustness
    r = requests.get(url, auth=(LM_USER, LM_PASS)) 
    
    if r.status_code == 429:
        print(f"⚠️ Too many requests – waiting {RETRY_WAIT}s...")
        time.sleep(RETRY_WAIT)
        continue
    
    if r.status_code == 401:
        print("❌ Unauthorized – Check LM_USER and LM_PASS credentials.")
        raise Exception("STAC API Authentication failed.")
        
    r.raise_for_status()
    data = r.json()
    features.extend(data.get("features", []))
    next_link = next((l["href"] for l in data.get("links", []) if l["rel"] == "next"), None)
    url = next_link
    page += 1
    time.sleep(SLEEP_SECONDS)

print(f"✅ Retrieved {len(features)} kommuner")

# --------------------------------------------------------------------
# DEFINE ATTRIBUTE STRUCTURE
# --------------------------------------------------------------------
fields = QgsFields()
fields.append(QgsField("id", QVariant.String))
fields.append(QgsField("kommun", QVariant.String))
fields.append(QgsField("lanskod", QVariant.String))
fields.append(QgsField("size_mb", QVariant.Double))
fields.append(QgsField("created", QVariant.String))
fields.append(QgsField("updated", QVariant.String))
fields.append(QgsField("download", QVariant.String))

# --------------------------------------------------------------------
# CREATE MEMORY LAYER (Centroid only)
# --------------------------------------------------------------------
vl_point = QgsVectorLayer("Point?crs=EPSG:3006", "belagenhetsadresser_centroid", "memory")

dp = vl_point.dataProvider()
dp.addAttributes(fields)
vl_point.updateFields()

# --------------------------------------------------------------------
# ADD FEATURES TO MEMORY LAYER (Centroid only)
# --------------------------------------------------------------------
point_features_to_add = []

for f in features:
    props = f["properties"]
    bbox_3006 = props.get("proj:bbox", None)
    href = f["assets"]["data"]["href"]
    size = f["assets"]["data"].get("file:size", 0) / 1024 / 1024

    if not bbox_3006:
        continue

    # Create Centroid Geometry
    xmin, ymin, xmax, ymax = bbox_3006
    rect = QgsRectangle(xmin, ymin, xmax, ymax)
    centroid_geom = QgsGeometry.fromRect(rect).centroid()

    attrs = [
        f.get("id"),
        props.get("title"),
        props.get("lanskod"),
        round(size, 1),
        props.get("created"),
        props.get("updated"),
        href
    ]

    # Point Feature
    feat_point = QgsFeature(fields)
    feat_point.setGeometry(centroid_geom)
    feat_point.setAttributes(attrs)
    point_features_to_add.append(feat_point)

# BULK ADDITION: Faster than individual additions
vl_point.dataProvider().addFeatures(point_features_to_add)

vl_point.updateExtents()

# --------------------------------------------------------------------
# SAVE LAYER TO GPKG (Single layer write - reliable)
# --------------------------------------------------------------------
os.makedirs(OUT_DIR, exist_ok=True)
if os.path.exists(OUT_PATH):
    os.remove(OUT_PATH)

transform_context = QgsProject.instance().transformContext()

options_point = QgsVectorFileWriter.SaveVectorOptions()
options_point.driverName = "GPKG"
options_point.fileEncoding = "utf-8"
options_point.layerName = "kommun_centroid"
# Action is omitted: Default behavior creates the file and layer.

res_point, error_point = QgsVectorFileWriter.writeAsVectorFormatV2(
    vl_point, OUT_PATH, transform_context, options_point
)

if res_point != QgsVectorFileWriter.NoError:
    print(f"❌ ERROR writing Point layer: {error_point}")
else:
    print(f"✅ Point layer (kommun_centroid) successfully written.")

print(f"✅ Saved to {OUT_PATH}")

# --------------------------------------------------------------------
# ADD TO PROJECT
# --------------------------------------------------------------------
layer = QgsVectorLayer(f"{OUT_PATH}|layername=kommun_centroid", "kommun_centroid", "ogr")
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
    print(f"✅ Successfully loaded layer: kommun_centroid")
else:
    print(f"❌ Failed to load layer: kommun_centroid. Check GPKG path and file permissions.")

print("🎉 Layer added to QGIS. Each feature has a 'download' field with a direct ZIP link.")

# --------------------------------------------------------------------
# OPTIONAL DOWNLOAD EXAMPLE
# --------------------------------------------------------------------
def download_kommun(kommun_title, target_folder=os.path.join(OUT_DIR, "lantmateriet_downloads")):
    """
    Download the ZIP package for a selected municipality.
    Requires valid LM_USER / LM_PASS credentials.
    """
    os.makedirs(target_folder, exist_ok=True)
    # Note: 'features' is defined globally
    for feature in features:
        title = feature["properties"]["title"]
        if kommun_title.lower() in title.lower():
            href = feature["assets"]["data"]["href"]
            filename = os.path.join(target_folder, os.path.basename(href))
            print(f"⬇️  Downloading {title} ...")
            try:
                with requests.get(href, auth=(LM_USER, LM_PASS), stream=True) as r:
                    if r.status_code == 401:
                        print("❌ Unauthorized - check username/password.")
                        return
                    r.raise_for_status()
                    with open(filename, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"✅ Saved to {filename}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Download failed for {title}: {e}")
            return
    print(f"Kommun '{kommun_title}' not found.")

# Example usage:
# download_kommun("Luleå")