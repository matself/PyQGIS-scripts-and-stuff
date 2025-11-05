"""
=====================================================================
NGP Detaljplaner — Planbestämmelser Downloader (Final Stable Version)
---------------------------------------------------------------------
Author: Mats Elfström & ChatGPT (OpenAI)
Date: 2025-11-03

Purpose:
    Downloads all planbestämmelser (spatial regulation features)
    from Lantmäteriet’s Nationella Geodataplattform (NGP)
    for one or several municipalities.

    Each feature corresponds to a bestämmelse within a Detaljplan.
    Geometries are rebuilt manually from coordinate arrays to ensure
    reliability in QGIS on Windows.

Output:
    • One GeoPackage per municipality (EPSG:3006)
    • Geometry type: Polygon (mixed geometries tolerated)
    • Attributes: typ, kategori, beteckning, namn, status, datum, URL

Usage:
    1. Load “NGP_detaljplanekommuner.gpkg” in QGIS.
    2. Select one or more kommuner (or none → all Skåne 12xx).
    3. Run this script in the QGIS Python console.
=====================================================================
"""

# === IMPORTS =======================================================
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsField, QgsFields, QgsCoordinateReferenceSystem, QgsVectorFileWriter
)
from PyQt5.QtCore import QVariant
import requests, os, json

# === CONFIGURATION =================================================
TOKEN = "PASTE_YOUR_LONG_LM_DATA_TOKEN_HERE"
BASE_URL = "https://api.lantmateriet.se/distribution/geodatakatalog/sokning/v1/detaljplan/v2/collections"

# Output directory — safe and user-visible
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "NGP_plans")
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"📂 Output directory: {OUTPUT_DIR}")

CRS = QgsCoordinateReferenceSystem("EPSG:3006")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# === GET SELECTION OF KOMMUNER =====================================
kommun_layer = QgsProject.instance().mapLayersByName("NGP_detaljplanekommuner")[0]
selected = kommun_layer.selectedFeatures()

if selected:
    kommuner = [f["id"] for f in selected]
    print(f"📍 Selected kommuner: {kommuner}")
else:
    kommuner = [f["id"] for f in kommun_layer.getFeatures() if str(f["id"]).startswith("12")]
    print(f"📍 No selection → defaulting to Skåne ({len(kommuner)} kommuner)")

# === GEOMETRY BUILDER ==============================================
def build_geometry(geom_obj):
    """Builds a QgsGeometry manually from coordinate arrays."""
    if not geom_obj or "type" not in geom_obj:
        return None
    gtype = geom_obj["type"]
    coords = geom_obj.get("coordinates")
    try:
        if gtype == "Point":
            return QgsGeometry.fromPointXY(QgsPointXY(*coords))
        elif gtype == "LineString":
            pts = [QgsPointXY(x, y) for x, y in coords]
            return QgsGeometry.fromPolylineXY(pts)
        elif gtype == "Polygon":
            rings = []
            for ring in coords:
                pts = [QgsPointXY(x, y) for x, y in ring]
                rings.append(pts)
            return QgsGeometry.fromPolygonXY(rings)
        elif gtype == "MultiPolygon":
            multi = []
            for poly in coords:
                rings = []
                for ring in poly:
                    pts = [QgsPointXY(x, y) for x, y in ring]
                    rings.append(pts)
                multi.append(rings)
            return QgsGeometry.fromMultiPolygonXY(multi)
    except Exception:
        return None
    return None

# === MAIN FUNCTION =================================================
def fetch_planbestammelser(kommun_id: str):
    print(f"\n📡 Fetching planbestämmelser for kommun {kommun_id} …")
    url = f"{BASE_URL}/{kommun_id}/items"
    features = []
    total = 0

    while url:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"⚠️  Failed for {kommun_id}: {r.status_code}")
            break

        data = r.json()
        batch = data.get("features", [])
        features.extend(batch)
        total += len(batch)

        # Pagination
        next_link = next((l.get("href") for l in data.get("links", []) if l.get("rel") == "next"), None)
        url = next_link
        print(f"  → fetched {len(batch)} features (total {total})")

    if not features:
        print(f"⚠️  No data for {kommun_id}")
        return

    # === PREPARE OUTPUT LAYER ======================================
    fields = QgsFields()
    for name in [
        "id", "title", "typ", "kategori", "beteckning", "namn",
        "status", "lagakraft", "plan_url", "geomtyp"
    ]:
        fields.append(QgsField(name, QVariant.String))

    layer = QgsVectorLayer("Polygon?crs=EPSG:3006", f"Planbest_{kommun_id}", "memory")
    pr = layer.dataProvider()
    pr.addAttributes(fields)
    layer.updateFields()

    added = 0
    for feat in features:
        geom = build_geometry(feat.get("geometry"))
        if not geom:
            continue

        props = feat.get("properties", {})
        det = props.get("detaljplan", {})
        plan_url = ""
        for a in feat.get("assets", {}).values():
            if a.get("roles") and "detaljplan" in a["roles"]:
                plan_url = a.get("href", "")
                break

        f = QgsFeature()
        f.setGeometry(geom)
        f.setAttributes([
            feat.get("id"),
            props.get("title"),
            props.get("feature", {}).get("typ"),
            props.get("planbestammelse", {}).get("kategori"),
            det.get("beteckning"),
            det.get("namn"),
            det.get("status"),
            det.get("datumLagakraft"),
            plan_url,
            feat.get("geometry", {}).get("type")
        ])
        pr.addFeature(f)
        added += 1

    # === SAVE TO GPKG (robust cross-version method) ================
    output_path = os.path.join(OUTPUT_DIR, f"planbestammelser_{kommun_id}.gpkg")

    if layer.isEditable():
        layer.commitChanges()

    ok, err_message = QgsVectorFileWriter.writeAsVectorFormat(
        layer,
        output_path,
        "UTF-8",
        CRS,
        "GPKG"
    )

    if ok == QgsVectorFileWriter.NoError:
        print(f"💾  Saved {added} features to {output_path}")
    else:
        print(f"⚠️  Write error for {kommun_id}: {ok} — {err_message}")

# === RUN ===========================================================
for kid in kommuner:
    fetch_planbestammelser(kid)

print("\n🏁 All done — planbestämmelser downloaded for all selected kommuner.")

