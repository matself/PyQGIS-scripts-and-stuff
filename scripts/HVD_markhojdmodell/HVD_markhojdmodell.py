# ---------------------------------------------------------
# MARKHÖJDMODELL 1m – STAC EXTRACTOR (POLYGON TILES)
# ---------------------------------------------------------
# This script queries Lantmäteriet’s STAC API for the
# Markhöjdmodell 1m dataset and extracts all tiles whose
# footprints intersect a user-defined bounding box.
#
# Key features:
#   • User inputs bbox in EPSG:3006 (SWEREF 99 TM)
#   • STAC search is automatically transformed to EPSG:4326
#   • Returned tile bboxes (EPSG:4326) are reprojected to EPSG:3006
#   • Output is a GeoPackage with polygon footprints
#   • Rate-limit protection and collection-prefiltering included
#   • Robust, fast and stable for large queries
#
# Collaboration and credits:
#   Developed jointly by Mats Elfström and ChatGPT (GPT-5),
#   through an iterative process aimed at producing a
#   reusable, transparent and publication-ready tool for the
#   Swedish GIS community.
#
# License:
#   This example script is provided openly for educational,
#   analytical and practical use. Data retrieved from
#   Lantmäteriet is governed by its respective license terms.
#
# Version:
#   2025-11-10
# ---------------------------------------------------------

import requests, time
from qgis.core import (
    QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY,
    QgsFields, QgsCoordinateReferenceSystem, QgsVectorFileWriter,
    QgsWkbTypes, QgsProject, QgsCoordinateTransform
)
from PyQt5.QtCore import QVariant

# ---------------------------------------------------------
# 1. AUTH SETTINGS
# ---------------------------------------------------------
consumer_key = "REPLACE_ME"
consumer_secret = "REPLACE_ME"

# ---------------------------------------------------------
# 2. USER INPUT BBOX (EPSG:3006 – SWEREF 99 TM)
# ---------------------------------------------------------
bbox_3006 = [380000, 6120000, 420000, 6180000]   # Example: part of Skåne

# ---------------------------------------------------------
# 3. OUTPUT SETTINGS
# ---------------------------------------------------------
output_gpkg = "C:/temp/mhm_req_footprints.gpkg"
layer_name = "mhm_footprints"
crs_3006 = QgsCoordinateReferenceSystem("EPSG:3006")

# ---------------------------------------------------------
# 4. CRS DEFINITIONS & TRANSFORMS
# ---------------------------------------------------------
crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")
transform_context = QgsProject.instance().transformContext()

t_3006_to_4326 = QgsCoordinateTransform(crs_3006, crs_4326, transform_context)
t_4326_to_3006 = QgsCoordinateTransform(crs_4326, crs_3006, transform_context)

# ---------------------------------------------------------
# 5. TRANSFORM INPUT BBOX → EPSG:4326 FOR STAC SEARCH
# ---------------------------------------------------------
minx, miny, maxx, maxy = bbox_3006

sw = t_3006_to_4326.transform(minx, miny)
ne = t_3006_to_4326.transform(maxx, maxy)

bbox_stac = [sw.x(), sw.y(), ne.x(), ne.y()]

print("STAC bbox (EPSG:4326):", bbox_stac)

# ---------------------------------------------------------
# 6. REQUEST ACCESS TOKEN
# ---------------------------------------------------------
print("Requesting access token ...")
auth = requests.post(
    "https://api.lantmateriet.se/token",
    data={"grant_type": "client_credentials"},
    auth=(consumer_key, consumer_secret)
)
auth.raise_for_status()
headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
print("✅ Access token obtained")

# ---------------------------------------------------------
# 7. FETCH COLLECTION LIST
# ---------------------------------------------------------
print("Fetching collections ...")
coll_resp = requests.get(
    "https://api.lantmateriet.se/stac-hojd/v1/collections",
    headers=headers
)
coll_resp.raise_for_status()

collections_full = coll_resp.json()["collections"]
print(f"✅ {len(collections_full)} collections available")

# ---------------------------------------------------------
# 8. PREFILTER COLLECTIONS BY SPATIAL EXTENT (EPSG:4326)
# ---------------------------------------------------------
def intersects(cbox, bbox):
    cmx1, cmy1, cmx2, cmy2 = cbox
    bx1, by1, bx2, by2 = bbox
    return not (cmx2 < bx1 or cmx1 > bx2 or cmy2 < by1 or cmy1 > by2)

relevant_collections = []

for c in collections_full:
    cid = c["id"]
    cbox = c["extent"]["spatial"]["bbox"][0]  # EPSG:4326
    if intersects(cbox, bbox_stac):
        relevant_collections.append(cid)

print(f"✅ {len(relevant_collections)} collections intersect bbox")

# ---------------------------------------------------------
# 9. STAC SEARCH FUNCTION (WITH RATE-LIMIT PROTECTION)
# ---------------------------------------------------------
def fetch_items(collection_id):
    url = "https://api.lantmateriet.se/stac-hojd/v1/search"

    payload = {
        "bbox": bbox_stac,
        "collections": [collection_id],
        "limit": 5000
    }

    items = []
    while True:
        r = requests.post(url, headers=headers, json=payload)

        # Handle rate-limiting gracefully
        if r.status_code == 429:
            print("⚠️ 429 Too Many Requests – sleeping 1 second ...")
            time.sleep(1)
            continue

        if not r.ok:
            print(f"⚠️ Error {r.status_code} for {collection_id}")
            return items

        data = r.json()
        items.extend(data.get("features", []))

        # Pagination handling
        next_url = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                next_url = link["href"]
                break

        if not next_url:
            break

        url = next_url
        payload = None

        # Delay to avoid hitting rate limits
        time.sleep(0.3)

    return items

# ---------------------------------------------------------
# 10. PREPARE OUTPUT GPKG
# ---------------------------------------------------------
fields = QgsFields()
fields.append(QgsField("id", QVariant.String))
fields.append(QgsField("collection", QVariant.String))
fields.append(QgsField("datetime", QVariant.String))
fields.append(QgsField("href", QVariant.String))

writer = QgsVectorFileWriter(
