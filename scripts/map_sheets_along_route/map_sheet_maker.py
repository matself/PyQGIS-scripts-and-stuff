# ===============================================================
# MAP-SHEET GENERATOR FOR QGIS ATLAS
# ---------------------------------------------------------------
# Purpose:
#   Generate evenly spaced, rectangular map sheets along a route.
#   Each sheet is 280 x 180 meters (corresponding to 280x180 mm
#   at map scale 1:1000). Rectangles are oriented perpendicular
#   to the route for optimal atlas readability.
#
# Workflow:
#   1. Select a single polyline (the route).
#   2. Run this script in the QGIS Python Console.
#   3. A new memory layer "map_sheets" is created.
#   4. Use this layer as Atlas coverage layer.
#   5. In the Layout, set map rotation expression to:
#         (180 - "azi") % 360
#
# Collaboration:
#   Developed jointly through discussion between
#   Mats Elfström & ChatGPT (GPT-5), 2025.
#
# License:
#   Free to use and modify. Attribution appreciated.
# ===============================================================

from qgis.core import *
import math

# ---------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------
MAP_WIDTH  = 280.0     # meters (landscape width)
MAP_HEIGHT = 180.0     # meters (height)
STEP       = MAP_WIDTH * 0.9   # 10% overlap. Use MAP_WIDTH for no overlap.

# ---------------------------------------------------------------
# INPUT LAYER
# ---------------------------------------------------------------
layer = iface.activeLayer()
if not layer:
    raise Exception("No active layer selected.")

selected = layer.selectedFeatures()
if not selected:
    raise Exception("Select one (1) polyline before running.")

route = selected[0].geometry()
route_length = route.length()

# ---------------------------------------------------------------
# OUTPUT MEMORY LAYER
# ---------------------------------------------------------------
crs = layer.crs().authid()
out = QgsVectorLayer(f"Polygon?crs={crs}", "map_sheets", "memory")
prov = out.dataProvider()

prov.addAttributes([
    QgsField("id",  QVariant.Int),
    QgsField("x",   QVariant.Double),
    QgsField("y",   QVariant.Double),
    QgsField("azi", QVariant.Double)   # raw math azimuth (atan2 system)
])
out.updateFields()

# ---------------------------------------------------------------
# RECTANGLE GENERATOR
# ---------------------------------------------------------------
def make_rect(center, azimuth_deg, width, height):
    """
    Creates a rectangle centered on 'center', rotated 'azimuth_deg'
    degrees, with real-world 'width' and 'height'.
    Azimuth is mathematical (0° = east, CCW positive).
    """
    ang = math.radians(azimuth_deg)

    # Unit vectors
    dx = math.sin(ang)       # along-line X
    dy = math.cos(ang)       # along-line Y
    px = dy                  # perpendicular X
    py = -dx                 # perpendicular Y

    hw = width / 2
    hh = height / 2

    # Four corners
    p1 = QgsPointXY(center.x() + px*hw + dx*hh, center.y() + py*hw + dy*hh)
    p2 = QgsPointXY(center.x() - px*hw + dx*hh, center.y() - py*hw + dy*hh)
    p3 = QgsPointXY(center.x() - px*hw - dx*hh, center.y() - py*hw - dy*hh)
    p4 = QgsPointXY(center.x() + px*hw - dx*hh, center.y() + py*hw - dy*hh)

    return QgsGeometry.fromPolygonXY([[p1, p2, p3, p4]])

# ---------------------------------------------------------------
# MAIN LOOP: GENERATE SHEETS ALONG THE ROUTE
# ---------------------------------------------------------------
distance = 0
sheet_id = 1

while distance < route_length:

    # Center point
    pt  = route.interpolate(distance).asPoint()
    pt2 = route.interpolate(min(distance + 1, route_length)).asPoint()

    # Raw mathematical azimuth (east = 0°, CCW)
    azi_math = math.degrees(math.atan2(pt2.x() - pt.x(),
                                       pt2.y() - pt.y()))

    # Create rectangle perpendicular to the route
    # (rotation adjustment is done later in atlas expression)
    rect = make_rect(QgsPointXY(pt), azi_math + 90,
                     MAP_WIDTH, MAP_HEIGHT)

    # Store feature
    feat = QgsFeature(out.fields())
    feat["id"]  = sheet_id
    feat["x"]   = pt.x()
    feat["y"]   = pt.y()
    feat["azi"] = azi_math
    feat.setGeometry(rect)
    prov.addFeature(feat)

    sheet_id += 1
    distance += STEP

# ---------------------------------------------------------------
# FINISH
# ---------------------------------------------------------------
out.updateExtents()
QgsProject.instance().addMapLayer(out)

print(f"✅ Created {sheet_id-1} map sheets successfully.")
print("Use rotation expression in layout:   (180 - \"azi\") % 360")
