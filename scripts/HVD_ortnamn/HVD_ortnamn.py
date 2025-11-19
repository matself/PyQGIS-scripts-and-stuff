# -*- coding: utf-8 -*-
"""
===============================================================
Lantmäteriet Ortnamn – Nedladdning och länsvis uppdelning
===============================================================

1. Hämtar STAC-metadata för Lantmäteriets ortnamnsdata
2. Laddar ner nationell ZIP (GPKG)
3. Packar upp lokalt
4. Läser lagret i QGIS
5. Delar upp features i minnet per 'lanskod'
6. Skapar ett GPKG per län:

   ortnamn_lan_<lanskod>_<lansnamn>.gpkg

Allt sker lokalt på användarens dator.
===============================================================
"""

import os
import zipfile
import requests

from qgis.core import (
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsProject
)

# ------------------------------------------------------------
# KONFIGURATION
# ------------------------------------------------------------

USERNAME = "DIN_ANVANDARE"
PASSWORD = "DITT_LOSEN"

OUT_ROOT = r"C:\temp\ortnamn_lan"

KEEP_ZIP = True
KEEP_FULL_GPKG = True

ITEMS_URL = "https://api.lantmateriet.se/stac-vektor/v1/collections/ortnamn/items"

LAN_FILNAMN = {
    "01": "stockholms_lan",
    "03": "uppsala_lan",
    "04": "sodermanlands_lan",
    "05": "ostergotlands_lan",
    "06": "jonkopings_lan",
    "07": "kronobergs_lan",
    "08": "kalmar_lan",
    "09": "gotlands_lan",
    "10": "blekinge_lan",
    "12": "skane_lan",
    "13": "hallands_lan",
    "14": "vastra_gotalands_lan",
    "17": "varmlands_lan",
    "18": "orebro_lan",
    "19": "vastmanlands_lan",
    "20": "dalarnas_lan",
    "21": "gavleborgs_lan",
    "22": "vasternorrlands_lan",
    "23": "jamtlands_lan",
    "24": "vasterbottens_lan",
    "25": "norrbottens_lan",
}

# ------------------------------------------------------------
# HJÄLPFUNKTIONER
# ------------------------------------------------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def download_stac_items():
    print("Hämtar STAC metadata…")
    r = requests.get(ITEMS_URL, auth=(USERNAME, PASSWORD))
    if r.status_code != 200:
        raise Exception(f"Metadatafel: HTTP {r.status_code}")
    return r.json()

def extract_download_url(stac_json):
    features = stac_json.get("features", [])
    if not features:
        raise Exception("STAC-svaret saknar features")
    assets = features[0].get("assets", {})
    data_asset = assets.get("data")
    if not data_asset:
        raise Exception("Ingen 'data'-asset i STAC-svaret")
    href = data_asset.get("href")
    if not href:
        raise Exception("Ingen href i 'data'-asset")
    return href

def download_zip(url, out_zip_path):
    print(f"Laddar ner ZIP från: {url}")
    r = requests.get(url, auth=(USERNAME, PASSWORD), stream=True)
    if r.status_code != 200:
        raise Exception(f"Nedladdning misslyckades: HTTP {r.status_code}")
    with open(out_zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Sparad ZIP: {out_zip_path}")

def unzip_first_gpkg(zip_path, target_folder):
    print("Packar upp ZIP…")
    ensure_dir(target_folder)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target_folder)
    for name in os.listdir(target_folder):
        if name.lower().endswith(".gpkg"):
            gpkg_path = os.path.join(target_folder, name)
            print(f"Hittade GPKG: {gpkg_path}")
            return gpkg_path
    raise Exception("Ingen .gpkg hittades i ZIP-filen")

def load_ortnamn_layer(gpkg_path):
    print("Laddar ortnamnlagret i QGIS…")
    vl = QgsVectorLayer(gpkg_path, "ortnamn_full", "ogr")
    if not vl.isValid():
        raise Exception("Kunde inte läsa GPKG via QGIS")
    return vl

def group_features_by_lanskod(vl):
    """
    Läser alla features en gång och grupperar dem i ett dict:
       { '01': [feat1, feat2, ...], '03': [...], ... }
    """
    groups = {}
    idx = vl.fields().indexFromName("lanskod")
    if idx < 0:
        raise Exception("Fältet 'lanskod' saknas i lagret")

    print("Grupperar features per lanskod…")
    for feat in vl.getFeatures():
        val = feat["lanskod"]
        if val is None:
            continue
        code = str(val)      # exakt som i GPKG (ingen zfill här)
        if code not in groups:
            groups[code] = []
        groups[code].append(feat)

    # sortera nycklarna bara för snygg loggning
    for code in sorted(groups.keys()):
        print(f"  lanskod {code}: {len(groups[code])} namn")

    return groups

def export_lan_packages(vl, groups):
    """
    Skriver ett GPKG per lanskod.
    Vi använder QgsVectorFileWriter.create och matar in
    de features som hör till respektive län.
    """
    print("Exporterar länsvisa paket…")

    transform_context = QgsProject.instance().transformContext()

    for code, feats in sorted(groups.items()):
        # vi använder tvåsiffrig kod i filnamnet
        code2 = code.zfill(2)
        safe_name = LAN_FILNAMN.get(code2, f"lan_{code2}")
        filename = f"ortnamn_lan_{code2}_{safe_name}.gpkg"
        out_path = os.path.join(OUT_ROOT, filename)

        print(f"  Skapar {filename} ({len(feats)} features)")

        opts = QgsVectorFileWriter.SaveVectorOptions()
        opts.driverName = "GPKG"
        opts.layerName = f"ortnamn_lan_{code2}"
        opts.fileEncoding = "UTF-8"
        opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

        writer = QgsVectorFileWriter.create(
            out_path,
            vl.fields(),
            vl.wkbType(),
            vl.sourceCrs(),
            transform_context,
            opts
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print(f"    FEL vid skapande: {writer.errorMessage()}")
            del writer
            continue

        for feat in feats:
            writer.addFeature(feat)

        del writer
        print(f"    OK: {out_path}")

# ------------------------------------------------------------
# HUVUDPROGRAM
# ------------------------------------------------------------

def main():
    if USERNAME == "DIN_ANVANDARE":
        raise Exception("Fyll i USERNAME och PASSWORD innan du kör skriptet.")

    ensure_dir(OUT_ROOT)

    # 1. STAC-metadata
    stac_json = download_stac_items()

    # 2. URL till ZIP
    download_url = extract_download_url(stac_json)
    print(f"Nedladdningslänk: {download_url}")

    # 3. Ladda ner ZIP
    zip_path = os.path.join(OUT_ROOT, "ortnamn_se.zip")
    download_zip(download_url, zip_path)

    # 4. Packa upp ZIP → GPKG
    full_folder = os.path.join(OUT_ROOT, "full_gpkg")
    gpkg_path = unzip_first_gpkg(zip_path, full_folder)

    # 5. Lägg in i QGIS
    vl = load_ortnamn_layer(gpkg_path)

    # 6. Gruppera per lanskod
    groups = group_features_by_lanskod(vl)

    # 7. Exportera länspaket
    export_lan_packages(vl, groups)

    # 8. Städning (frivilligt)
    if not KEEP_ZIP and os.path.exists(zip_path):
        os.remove(zip_path)
        print("Tog bort ZIP enligt inställning")

    if not KEEP_FULL_GPKG and os.path.isdir(full_folder):
        for name in os.listdir(full_folder):
            if name.lower().endswith(".gpkg"):
                try:
                    os.remove(os.path.join(full_folder, name))
                except Exception as e:
                    print(f"Kunde inte ta bort {name}: {e}")

    print("\nKLART! Länsvisa paket finns i:")
    print(OUT_ROOT)

main()
