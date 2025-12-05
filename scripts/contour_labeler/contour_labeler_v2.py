"""
tool_name: Contour Label Ladders (PyQGIS)
author: Mats Elfström (Concept, Requirements, Testing)
co_author: Gemini (AI Implementation, Debugging)
date: 2025-03-16
version: 1.0

DESCRIPTION:
This tool generates cartographically strictly aligned "Label Ladders" for contour lines.
Unlike standard automatic labeling, this allows the cartographer to draw a "Guide Line"
(placeline) uphill. The script then intersects this guide with the contours to place labels.

KEY FEATURES:
1. Contour Alignment: Labels follow the immediate tangent of the contour line (curved text).
2. Uphill Orientation: The "Top" of the text always points uphill, defined by the guide line.
3. Vector Robustness: Uses Dot Product math to ignore contour digitization direction (works
   regardless of whether lines were drawn Left-to-Right or Right-to-Left).
4. Persistent Layer: Appends points to a single layer ('ContourLabelPoints') to allow
   continuous work without losing styling.
5. Multi-node Support: The guide line can be a complex polyline; labels align to the 
   specific segment they intersect.

USAGE:
1. Load your contour layer and a line layer for guides.
2. Select exactly one guide line feature.
3. Run: create_labels("Your_Contour_Layer_Name", "Your_Guide_Layer_Name")
"""

from qgis.core import (
    QgsProject,
    QgsGeometry,
    QgsPointXY,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsSpatialIndex,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsProperty,
    QgsMarkerSymbol
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QVariant
import math

# --- CONFIGURATION ---
TARGET_LAYER_NAME = "ContourLabelPoints"
ELEVATION_FIELD = "ELEV"  # Name of the field containing elevation integers
LOOK_AHEAD_DIST = 5.0     # Distance (meters) to average contour tangent

def calculate_final_rotation(contour_geom, guide_geom, intersection_point):
    """
    Calculates rotation using Vector Math (CCW), then converts to QGIS (CW).
    Immune to contour digitization direction.
    """
    # 1. Get Contour Vector (C) - The Baseline
    # Clip contour with buffer to get local tangent (avoids single-pixel noise)
    clipper = QgsGeometry.fromPointXY(intersection_point).buffer(LOOK_AHEAD_DIST, 8)
    clipped = contour_geom.intersection(clipper)
    
    seg_pts = []
    if clipped.isMultipart():
        lines = clipped.asMultiPolyline()
        if lines: seg_pts = max(lines, key=len)
    else:
        seg_pts = clipped.asPolyline()
        
    if len(seg_pts) < 2: return 0 
    
    # Vector C (Tangent)
    cx = seg_pts[-1].x() - seg_pts[0].x()
    cy = seg_pts[-1].y() - seg_pts[0].y()
    
    # 2. Get Guide Vector (G) - The Uphill Direction
    dist = guide_geom.lineLocatePoint(QgsGeometry.fromPointXY(intersection_point))
    p_g1 = guide_geom.interpolate(dist).asPoint()
    
    # Look slightly ahead/behind to get tangent of the guide line
    if dist + 0.1 < guide_geom.length():
        p_g2 = guide_geom.interpolate(dist + 0.1).asPoint()
        gx = p_g2.x() - p_g1.x()
        gy = p_g2.y() - p_g1.y()
    else:
        p_g2 = guide_geom.interpolate(dist - 0.1).asPoint()
        gx = p_g1.x() - p_g2.x()
        gy = p_g1.y() - p_g2.y()

    # 3. Vector Math (All in CCW space)
    # The "Normal" vector to the contour (rotated 90 deg CCW) is (-cy, cx).
    # This represents the "Top" of the text if rotation was 0.
    nx = -cy
    ny = cx
    
    # Dot Product: Does Normal point same way as Guide?
    dot_prod = (nx * gx) + (ny * gy)
    
    # Calculate Math Angle (CCW from East)
    math_angle = math.degrees(math.atan2(cy, cx))
    
    final_math_angle = math_angle
    if dot_prod < 0:
        # Normal points downhill, so flip text 180 to point 'Top' uphill
        final_math_angle += 180
        
    # 4. Conversion: Math (CCW) to QGIS (CW)
    # QGIS Rotation = -Math Rotation
    qgis_rotation = -final_math_angle
    
    return qgis_rotation % 360

def create_labels(contour_layer_name, guide_layer_name):
    # 1. Get Layers
    c_list = QgsProject.instance().mapLayersByName(contour_layer_name)
    g_list = QgsProject.instance().mapLayersByName(guide_layer_name)
    
    if not c_list or not g_list:
        print(f"Error: Layers '{contour_layer_name}' or '{guide_layer_name}' not found.")
        return
    c_layer = c_list[0]
    g_layer = g_list[0]
    
    # 2. Get Selected Guide Line
    if g_layer.selectedFeatureCount() != 1:
        print("Error: Select exactly one guide line.")
        return
    guide_feat = g_layer.selectedFeatures()[0]
    guide_geom = guide_feat.geometry()

    # 3. Output Layer (Persistent)
    out_layer_list = QgsProject.instance().mapLayersByName(TARGET_LAYER_NAME)
    if out_layer_list:
        out_layer = out_layer_list[0]
    else:
        crs = c_layer.crs().authid()
        out_layer = QgsVectorLayer(f"Point?crs={crs}", TARGET_LAYER_NAME, "memory")
        pr = out_layer.dataProvider()
        pr.addAttributes([
            QgsField(ELEVATION_FIELD, QVariant.Double), 
            QgsField("rotation", QVariant.Double)
        ])
        out_layer.updateFields()
        QgsProject.instance().addMapLayer(out_layer)
        apply_styling(out_layer)

    # 4. Process Intersections
    c_index = QgsSpatialIndex(c_layer.getFeatures(guide_geom.boundingBox()))
    candidate_ids = c_index.intersects(guide_geom.boundingBox())
    
    new_features = []
    
    for cid in candidate_ids:
        c_feat = c_layer.getFeature(cid)
        c_geom = c_feat.geometry()
        
        if not guide_geom.intersects(c_geom): continue
            
        intersection = guide_geom.intersection(c_geom)
        points = intersection.asMultiPoint() if intersection.isMultipart() else [intersection.asPoint()]
            
        for pt in points:
            center = QgsPointXY(pt)
            rot = calculate_final_rotation(c_geom, guide_geom, center)
            
            feat = QgsFeature(out_layer.fields())
            feat.setGeometry(QgsGeometry.fromPointXY(center))
            
            z_val = c_feat[ELEVATION_FIELD] if ELEVATION_FIELD in c_feat.fields().names() else 0
            feat.setAttribute(ELEVATION_FIELD, z_val)
            feat.setAttribute("rotation", rot)
            new_features.append(feat)

    if new_features:
        out_layer.startEditing()
        out_layer.dataProvider().addFeatures(new_features)
        out_layer.commitChanges()
        out_layer.triggerRepaint()
        print(f"Success: Added {len(new_features)} labels.")
    else:
        print("No intersections found.")

def apply_styling(layer):
    pal = QgsPalLayerSettings()
    pal.enabled = True
    pal.fieldName = ELEVATION_FIELD
    pal.placement = QgsPalLayerSettings.Placement.OverPoint
    fmt = QgsTextFormat()
    fmt.setColor(QColor("black"))
    fmt.setSize(9)
    pal.setFormat(fmt)
    
    props = pal.dataDefinedProperties()
    props.setProperty(QgsPalLayerSettings.Rotation, QgsProperty.fromField("rotation"))
    pal.setDataDefinedProperties(props)
    
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)
    
    symbol = QgsMarkerSymbol.createSimple({
        'name': 'circle', 'color': 'white', 'size': '5', 'outline_style': 'no'
    })
    
    # Rotate symbol for consistency, even if circle is symmetric
    sym_props = symbol.dataDefinedProperties()
    sym_props.setProperty(QgsProperty.PropertyRotation, QgsProperty.fromField("rotation"))
    symbol.setDataDefinedProperties(sym_props)

    layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()
