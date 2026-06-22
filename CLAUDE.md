# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A personal collection of two things:

1. **PyQGIS scripts** (`scripts/`) — Python scripts run inside the QGIS Desktop Python Console to automate geospatial tasks against Swedish open data.
2. **A GitHub Pages site** (`docs/`) — Static, self-contained HTML files hosting interactive botanical species maps, published at the repo's custom domain.

There is no build system, no package manager, and no test suite. Scripts are executed directly in QGIS or from the command line with plain Python.

## Running the PyQGIS scripts

Scripts are designed to run inside **QGIS 3.44+ Python Console** (Plugins → Python Console, or `Ctrl+Alt+P`). Open the script editor, load the `.py` file, and press Run.

Scripts in `scripts/publik_botanik/` that generate HTML maps (`artportal_lokalisera_kluster_100.py`, `kluster_200.py`, `CB_kluster_200.py`) can also be run standalone from the command line:

```
python artportal_lokalisera_kluster_100.py <input.geojson>
```

## Credentials

Several scripts require Lantmäteriet credentials and contain placeholder strings. Before running, edit these in the script:

- **HVD scripts**: `LM_USER = "DIN_ANVÄNDARE_HÄR"` / `LM_PASS = "DITT_LÖSENORD_HÄR"`
- **NGP scripts**: A Bearer token / API key from apimanager.lantmateriet.se
- **HVD_ortofoton**: `consumer_key` / `consumer_secret`

The NGP Detaljplan WMS layer (`detaljplan_template.qlr`) also needs a UUID token inserted directly into the datasource URL.

## Architecture: publik_botanik pipeline

This is the most active part of the repo. The flow is:

1. **Source data** — GeoJSON exported from Artportalen (Swedish species observation database). Each feature is a point with `time`, `notRedisc`, and `removed` properties. Source JSONs live in `scripts/publik_botanik/`.
2. **Processing script** — Reads the GeoJSON, clusters observations onto a fixed 100 m or 200 m grid using approximate meter projection, then classifies each grid cell into one of: `Stark aktuell lokal`, `Sporadisk aktuell lokal`, `Historisk lokal (inga sentida fynd)`, `Ej återfunnen`, `Avlägsnad lokal`, or `Osäker`.
3. **Output** — A self-contained `.html` file written next to the input JSON in `scripts/publik_botanik/`, with the clustered data embedded as a JavaScript variable, rendered via Leaflet.js with OSM tiles. No external data dependencies at runtime.
4. **Publishing** — The generated HTML is manually moved to `docs/` and `docs/list.json` is updated. The source JSON files stay in `scripts/publik_botanik/` and are not copied to `docs/`.

### Variant scripts

| Script | Grid | Notes |
|--------|------|-------|
| `artportal_lokalisera_kluster_100.py` | 100 m | Standard variant |
| `kluster_200.py` | 200 m | Standard variant |
| `CB_kluster_200.py` | 200 m | Colour-blind friendly palette |

The scripts are nearly identical — the grid cell size and legend colours differ. The classification logic is shared verbatim.

## Architecture: HVD scripts

Scripts that query **Lantmäteriet's STAC API** to build GeoPackage index layers in QGIS:

- `HVD_belagenhetsadresser.py` — Municipality centroids with download links for address data ZIPs.
- `HVD_markhojdmodell.py` — Elevation model metadata.
- `HVD_ortnamn.py` — Place name data.
- `HVD_ortofoton.py` — Orthophoto footprints/centroids for a bbox in EPSG:3006.

All outputs are GeoPackages written to `C:/temp/` and auto-loaded into the QGIS project.

## Architecture: NGP detaljplaner

Two-step workflow for Sweden's National Geodata Platform detailed development plans:

1. `NGP_detaljplanekommuner.py` — Fetches all municipalities from NGP OGC API Features, writes bounding boxes as `NGP_detaljplanekommuner.gpkg` in EPSG:3006.
2. `NGP_planbestammelser.py` — Reads selected features from the above layer, downloads plan regulations per municipality into `NGP_plans/planbestammelser_<id>.gpkg`. Defaults to Skåne (IDs starting with `12`) if nothing is selected.

## Architecture: contour_labeler

A QGIS Python Console script for cartographic contour label placement. Define the function once by loading the script, then call it repeatedly per placement line:

```python
generate_slope_aligned_labels("5m_cont", "placelines")
```

**Requirements:** A contour vector layer with an elevation field named exactly `z` (case-sensitive), and a placement layer of 2-vertex lines drawn uphill. Output is appended to a memory layer named `ContourLabelPoints`. Set "Show upside-down labels" → "when rotation defined" in the Layer Styling Panel for correct orientation.

## Architecture: map_sheets_along_route

A QGIS Python Console script that generates evenly spaced rectangular map sheets along a selected route polyline, suitable for QGIS Atlas export. Sheets are 280 × 180 m (1:1000 scale) oriented perpendicular to the route. After running, use the output `map_sheets` memory layer as the Atlas coverage layer and set the map rotation expression to `(180 - "azi") % 360`.

## GitHub Pages site

The `docs/` folder is published as GitHub Pages with a custom domain (CNAME file present). Key files:

- `docs/index.html` — Loads `docs/list.json` via `fetch()` and renders a linked list of available maps.
- `docs/list.json` — Catalog of maps: `[{ "file": "...", "swedish": "...", "latin": "..." }]`. **Must be updated when adding or renaming map files.**
- `docs/*.html` — Generated map files. Named `<species>_skane.html` by convention.

## Coordinate systems

- Most scripts assume **SWEREF 99 TM (EPSG:3006)** for spatial operations and output.
- The botanik scripts use an approximate equirectangular projection in pure Python (no QGIS dependency) to assign observations to grid cells; final coordinates in output HTML are WGS 84.
- Leaflet maps default to a view centred on Skåne: `[55.9, 14.0]`, zoom 8.
