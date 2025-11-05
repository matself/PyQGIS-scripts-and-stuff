from qgis.core import (
    QgsProject,
    QgsProcessingFeatureSourceDefinition,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
    QgsProperty,
    QgsField,
    QgsMarkerSymbol,
    QgsSymbol,
    QgsWkbTypes,
    QgsFeature,
    QgsVectorLayer
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QVariant
import processing
import math

# Define the target layer name as a constant for easy management
TARGET_LAYER_NAME = "ContourLabelPoints"


def generate_slope_aligned_labels(contour_layer_name, slope_line_layer_name):
    """
    Purpose: Creates high-quality, slope-aligned contour labels for cartographic layout.
    
    This function iteratively intersects contour lines with a single, selected 2-vertex
    "placement line" to generate label points. It appends all resulting points to a
    single, persistent memory layer ('ContourLabelPoints'). The layer is initialized 
    with a calculated rotation attribute and initial styling (data-defined rotation
    and collar symbol), ready for final manual refinement in QGIS.
    
    Credits:
        Ideas, Requirements, and Testing: Mats Elfström
        PyQGIS Implementation and Debugging: Gemini
    
    Includes: 
        - Iterative feature appending.
        - Robust geometry checks (supports 2D and 3D lines).
        - Label rotation perpendicular to the slope line (uphill).
        - Initial styling for collars and data-defined rotation.
    """

    # --- 1. Get layers and initial checks ---
    try:
        contours = QgsProject.instance().mapLayersByName(contour_layer_name)[0]
        slopes   = QgsProject.instance().mapLayersByName(slope_line_layer_name)[0]
    except IndexError:
        print("Error: Could not find one or both layers by name.")
        return

    if "z" not in contours.fields().names():
        print("Error: contour layer must have a 'z' field.")
        return
    print("Using field 'z' for elevation.")

    # --- 2. Check and Require ONE Selected 2-point line (WKBZ FIX) ---
    sel = slopes.selectedFeatures()
    if len(sel) != 1:
        print("Error: Select EXACTLY one placement line.")
        return
    
    selected_line = sel[0]
    g = selected_line.geometry().constGet()

    wkb_type = g.wkbType()
    n_coords = g.nCoordinates()
    
    # Accept standard LineString (2) or 3D LineStringZ (1002)
    is_valid_type = (wkb_type == QgsWkbTypes.LineString or 
                     wkb_type == QgsWkbTypes.LineStringZ)
    
    if not is_valid_type or n_coords != 2:
        print("Error: Selected line must be a 2-vertex LineString (2D or 3D).")
        return

    # --- 3. Compute perpendicular rotation ---
    p1, p2 = g.pointN(0), g.pointN(1)
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    
    angle_deg = math.degrees(math.atan2(dy, dx))
    
    # Calculate the perpendicular rotation (azimuth - 90 degrees).
    # The QGIS 'Show upside-down labels' setting controls the final 180-degree flip.
    uphill_perp_deg = (angle_deg + 270) % 360

    print(f"Rotation calculated: {uphill_perp_deg:.2f}° (Orientation controlled by QGIS setting)")

    # --- 4. Create intersection points ---
    slope_src = QgsProcessingFeatureSourceDefinition(
        slopes.source(), selectedFeaturesOnly=True
    )
    
    params = {
        "INPUT": contours,
        "INPUT_FIELDS": ["z"],
        "INTERSECT": slope_src,
        "INTERSECT_FIELDS": [],
        "OUTPUT": "memory:new_intersection_points",
    }
    result = processing.run("native:lineintersections", params)
    new_points_temp_layer = result["OUTPUT"] 
    print("Intersection successful.")


    # --- 5. Find or Create the Target Layer ---
    points_list = QgsProject.instance().mapLayersByName(TARGET_LAYER_NAME)
    needs_setup = False
    
    if points_list:
        points = points_list[0]
        print(f"Target layer found: {TARGET_LAYER_NAME}")
        # Ensure 'rotation' field exists
        if "rotation" not in points.fields().names():
            points.dataProvider().addAttributes([QgsField("rotation", QVariant.Double)])
            points.updateFields()
    else:
        # Create a blank memory layer with the correct schema
        points = QgsVectorLayer("Point?crs={}".format(contours.crs().authid()), 
                                TARGET_LAYER_NAME, "memory")
        points_dp = points.dataProvider()
        points_dp.addAttributes([QgsField("z", QVariant.Double), 
                                 QgsField("rotation", QVariant.Double)])
        points.updateFields()
        
        QgsProject.instance().addMapLayer(points)
        print(f"Created new layer: {TARGET_LAYER_NAME}")
        needs_setup = True
        
    # --- 6. Prepare and Append New Features ---
    points_dp = points.dataProvider()
    new_features_to_add = []
    
    for f_temp in new_points_temp_layer.getFeatures():
        f_new = QgsFeature(points.fields())
        f_new.setGeometry(f_temp.geometry())
        
        f_new.setAttribute("z", f_temp["z"])
        f_new.setAttribute("rotation", uphill_perp_deg)
        
        new_features_to_add.append(f_new)

    points_dp.addFeatures(new_features_to_add)
    print(f"Successfully appended {len(new_features_to_add)} points.")

    # --- 7. Initial Layer Setup (Symbology & Labeling - ONLY runs on creation) ---
    if needs_setup:
        # Label Setup: Text Format and Placement
        pal = QgsPalLayerSettings()
        pal.enabled = True
        pal.fieldName = "z"
        pal.placement = QgsPalLayerSettings.Placement.OverPoint

        # Default text format and buffer (can be manually adjusted later)
        fmt = QgsTextFormat()
        fmt.setSize(9)
        fmt.setColor(QColor(0, 0, 0))
        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(1)
        buf.setColor(QColor(255, 255, 255))
        fmt.setBuffer(buf)
        pal.setFormat(fmt)

        # Label Rotation: Data-defined from the 'rotation' field
        props = pal.dataDefinedProperties()
        props.setProperty(QgsPalLayerSettings.Rotation,
                          QgsProperty.fromField("rotation"))
        
        pal.setDataDefinedProperties(props)
        points.setLabeling(QgsVectorLayerSimpleLabeling(pal))
        points.setLabelsEnabled(True)

        # Symbology Setup: White Collar Marker
        symbol = QgsMarkerSymbol()
        symbol.deleteSymbolLayer(0) 

        # Collar Marker (white circle)
        marker_layer = QgsMarkerSymbol.createSimple({'name': 'circle', 
                                                     'color': '255,255,255,255', 
                                                     'size': '4', 
                                                     'size_unit': 'MM',
                                                     'outline_width': '0',
                                                     'outline_color': '0,0,0,0'})
        symbol.appendSymbolLayer(marker_layer.symbolLayer(0)) 
        
        # Symbol Rotation: Data-defined from the 'rotation' field
        data_defined_symb = symbol.dataDefinedProperties()
        data_defined_symb.setProperty(QgsSymbol.PropertyRotation,
                                      QgsProperty.fromField("rotation"))
        
        symbol.setDataDefinedProperties(data_defined_symb)
        
        renderer = points.renderer().clone()
        renderer.setSymbol(symbol)
        points.setRenderer(renderer)
        
        print("✨ Layer setup complete (Symbology/Labeling enabled).")
        
    points.triggerRepaint()


# --- USAGE COMMAND ---
# Select exactly ONE 2-vertex placement line in your 'placelines' layer, then run:
# generate_slope_aligned_labels("5m_cont", "placelines")
