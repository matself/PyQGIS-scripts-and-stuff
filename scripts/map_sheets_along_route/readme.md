Step-by-step: QGIS Atlas along a route
0) Prereqs

Your sheet polygons layer exists (from the script), with fields:

id (sheet number)

azi (raw azimuth from the script)

CRS is projected in meters (e.g. EPSG:3006).

1) Create the layout

Project → Layout Manager → New… give it a name.

In the layout, set the page size:

Either set Custom page to 280 × 180 mm (Landscape) to make each PDF page exactly that size,

or keep A4 and just use a 280×180 map frame (next step).

2) Add the map frame (the thing that will rotate)

Click Add Map and draw a map frame.

Select the map frame → Item Properties:

Size → set Width = 280 mm, Height = 180 mm (if you didn’t make the whole page 280×180).

Scale → set to 1:1000 (and leave it fixed).

3) Enable Atlas

Open the Atlas panel (right side). Tick Generate an atlas.

Coverage layer → choose your rectangle layer.

Sort by → id (ascending).

Optional: tick Hide coverage layer if you don’t want the rectangles drawn on top.

4) Make the map follow each sheet polygon

With the map frame selected:

In Item Properties → Controlled by atlas → ON.

Margin = 0% (this makes the map extent match the polygon tightly).

Click Set to current atlas feature (target icon) once to confirm behavior (optional).

5) Rotate each page from the azi field

Still with the map frame selected:

Item Properties → Rotation → click the data-defined button → Edit Expression…

Paste this (fixes azimuth system and makes the sheets perpendicular to the route):

(180 - "azi") % 360


If rotation appears mirrored, try:

(180 + "azi") % 360

6) Dynamic texts (optional but useful)

Add a Label item, and set Text to something like:

'Sheet ' || to_string("id")


For a file name per page: Atlas → Output → Filename expression:

'sheet_' || lpad(to_string("id"), 3, '0')

7) Preview and export

In the Atlas panel, click Preview Atlas and step through pages.

Atlas → Export Atlas → PDF, pick an output folder.
You’ll get one multi-page PDF or one file per page (depending on your choice).

Quick troubleshooting

Extent doesn’t fit the polygon: Map frame not set to Controlled by atlas or Margin ≠ 0%.

Scale changes unexpectedly: Re-select the map frame and ensure Scale = 1:1000 (fixed).

Rotation is off by 180°: swap to (180 + "azi") % 360.

Wrong CRS sizing: Ensure the project and layer CRS are metric (not WGS84 degrees).

