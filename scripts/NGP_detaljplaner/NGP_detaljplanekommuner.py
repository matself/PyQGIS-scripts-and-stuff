"""
=====================================================================
NGP Detaljplanekommuner — Bounding Box Layer Generator
---------------------------------------------------------------------
Author: Mats Elfström & ChatGPT (OpenAI)
Date: 2025-11-03

Purpose:
    Fetches the list of municipalities (“kommuner”) from
    Lantmäteriet’s Nationella Geodataplattform (NGP)
    for the dataset Detaljplan (v2).

    Each kommun is represented by a bounding box polygon
    in SWEREF 99 TM (EPSG:3006) with attributes:
        id — the kommun code (e.g. "1281")

    The result is saved as a GeoPackage that can be used
    as input to the detaljplan download script.

Usage:
    Run this script from the QGIS Python console or as a standalone
    script inside QGIS (it requires the QGIS Python environment).
=====================================================================
"""

# ==========================================================
# IMPORTS
# ==========================================================
import os
import requests
from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorFileWriter,
)
from PyQt5.QtCore import QVariant

# ==========================================================
# CONFIGURATION
# ==========================================================

# Insert your valid Lantmäteriet API token below
TOKEN = "PASTE_YOUR_LONG_LM_DATA_TOKEN_HERE"
# API endpoint for kommun collections in NGP Detaljplan (v2)
API_URL = "https://api.lantmateriet.se/distribution/geodatakatalog/sokning/v1/detaljplan/v2/collections"

# Output path (change freely)
# Example: r"D:\Geodata\NGP_detaljplanekommuner.gpkg"
OUTPUT_FILE = os.path.join(os.path.expanduser("~"), "Downloads", "NGP_detaljplanekommuner.gpkg")

# ==========================================================
# FETCH DATA FROM API
# ==========================================================
print("📡 Fetching kommun collections from Lantmäteriet…")

headers = {"Authorization": f"Bearer {TOKEN}"}
resp = requests.get(API_URL, headers=headers)

if resp.status_code != 200:
    raise Exception(f"❌ API error {resp.status_code}: {resp.text}")

data = resp.json()
collections = data.get("collections", [])
print(f"✅ Retrieved {len(collections)} kommuner from API.")

# ==========================================================
# CREATE MEMORY LAYER
# ==========================================================
layer = QgsVectorLayer("Polygon?crs=EPSG:3006", "NGP_detaljplanekommuner", "memory")
pr = layer.dataProvider()
pr.addAttributes([QgsField("id", QVariant.String)])
layer.updateFields()

# ==========================================================
# CONVERT API RESPONSE TO FEATURES
# ==========================================================
count = 0
for coll in collections:
    try:
        fid = str(coll.get("id", "")).strip()
        bbox = coll.get("extent", {}).get("spatial", {}).get("bbox", [])
        if not bbox:
            continue

        xmin, ymin, xmax, ymax = bbox[0]
        ring = [
            QgsPointXY(xmin, ymin),
            QgsPointXY(xmin, ymax),
            QgsPointXY(xmax, ymax),
            QgsPointXY(xmax, ymin),
            QgsPointXY(xmin, ymin),
        ]
        geom = QgsGeometry.fromPolygonXY([ring])

        f = QgsFeature()
        f.setGeometry(geom)
        f.setAttributes([fid])
        pr.addFeature(f)

        count += 1
        print(f"  • Added kommun {fid}")

    except Exception as e:
        print(f"⚠️ Skipped entry: {e}")

layer.updateExtents()
print(f"🧩 Added {count} kommuner to memory layer.")

# ==========================================================
# SAVE TO GPKG
# ==========================================================
options = QgsVectorFileWriter.SaveVectorOptions()
options.driverName = "GPKG"
options.fileEncoding = "utf-8"
options.layerName = "NGP_detaljplanekommuner"

QgsVectorFileWriter.writeAsVectorFormatV3(
    layer, OUTPUT_FILE, QgsProject.instance().transformContext(), options
)

print(f"💾 Saved kommun extents to: {OUTPUT_FILE}")
print("🏁 Done — the layer is ready to use in QGIS.")
