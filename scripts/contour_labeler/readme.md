# Slope-Aligned Contour Label Generator (PyQGIS Script)

**Tool Name:** `generate_slope_aligned_labels`

A PyQGIS script designed for professional cartography to quickly and iteratively generate slope-aligned elevation labels along custom placement lines. This method produces highly readable, aesthetically pleasing labels ready for final map layout.

Prepare the placement lines by creating 2-vertex lines UPHILL where it suits your cartographic needs. These can be in a scratch layer or any geodata format.

Output labels are created in a virtual layer. **Remember** to save it to a persistent format. 

**Credits:**
* **Ideas, Requirements, and Testing:** Mats Elfström
* **PyQGIS Implementation and Debugging:** Gemini

---

## Requirements

* **Software:** QGIS (Version 3.10+ recommended, but compatible with older versions due to fixed API inconsistencies).
* **Contour Layer:** Must be a vector polyline layer containing an elevation field named **'z'** (case-sensitive).
* **Placement Layer:** A separate vector polyline layer (e.g., named 'placelines') used for drawing the label placement vectors.

---

## Usage Manual

The core function, `generate_slope_aligned_labels`, is designed to be run repeatedly for multiple placement lines, appending all generated points to a single output layer.

### Step 1: Prepare the Layers

1.  Ensure both your **Contour Layer** (e.g., `5m_cont`) and your **Placement Layer** (e.g., `placelines`) are loaded in the QGIS project.
2.  The Placement Layer should contain lines that are exactly **two vertices** long (simple straight lines).

### Step 2: Define the Function

Copy and paste the entire Python script into the **QGIS Python Console** (or load it as a startup script).

### Step 3: Run Iteratively

For each area where you want labels:

1.  Click on the **Placement Layer** (`placelines`) to make it active.
2.  Use the **Select Features** tool to select **EXACTLY ONE** 2-vertex line.
3.  Run the function in the Python Console, replacing the layer names with your actual layer names if different:

    ```python
    generate_slope_aligned_labels("5m_cont", "placelines")
    ```

4.  Repeat steps 1-3 for every placement line you wish to use. The points will be appended to the single output layer, **'ContourLabelPoints'**.

### Output Layer Details

The script creates (or appends to) a new memory point layer named **`ContourLabelPoints`**. This layer automatically includes:

* **Attribute `z`:** The elevation value copied from the intersecting contour line.
* **Attribute `rotation`:** The calculated rotation angle (perpendicular to the placement line).
* **Initial Styling:** The layer is configured to use the `z` field for labels and the `rotation` field for orientation, applying basic text formatting and a white collar marker.

***Note on Orientation:*** The script calculates the raw perpendicular angle. For final orientation (i.e., making sure text is always right-side up), you must set the **"Show upside-down labels"** option in the QGIS Layer Styling Panel to **"when rotation defined"**.
