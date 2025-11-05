# NGP Detaljplan – QGIS‑verktyg

Detta projekt innehåller Python‑skript och konfigurationsfiler för att hämta och visualisera **Detaljplan (v2)** från **Lantmäteriets Nationella geodataplattform (NGP)** i QGIS.

Verktygen gör det möjligt att i QGIS:
- Hämta kommunvisa avgränsningar som utgångspunkt för nedladdning.
- Ladda ned planbestämmelser (detaljplaners delgeometrier) för valda kommuner.
- Visa Lantmäteriets officiella WMS‑tjänst för Detaljplan som bakgrundskarta.

---

## Installation

1. Ladda ned *.py-filerna från GitHub
2. Lägg dem gärna i en samlad mapp.
3. Öppna **Python‑konsolen** i QGIS (`Ctrl+Alt+P`) och kör skripten enligt instruktionerna nedan.
4. Se till att din dator har tillgång till internet och att du har en giltig API‑nyckel från Lantmäteriet.

---

## Komponenter

### `NGP_detaljplanekommuner.py`
Hämtar samtliga svenska kommuner från NGP:s API och skapar ett GeoPackage (`NGP_detaljplanekommuner.gpkg`) med en rektangulär avgränsning per kommun i **SWEREF 99 TM (EPSG:3006)**. Resultatet används för att välja vilka kommuner som ska laddas ned i nästa steg.

### `NGP_planbestammelser.py`
Hämtar planbestämmelser (delgeometrier inom varje detaljplan) för de kommuner som valts i kartan. Varje kommun sparas som ett eget GeoPackage i katalogen `NGP_plans`.

### `Detaljplan_WMS.qlr`
En QGIS‑lagerdefinition som kopplar mot Lantmäteriets WMS‑tjänst för Detaljplan. Användaren måste själv lägga in sin **API‑nyckel** i källsträngen (datasource) enligt:

```
http-header:Authorization=Bearer <DIN_TOKEN_HÄR>
```

> **Tips:** Använd **kort token (UUID)** för WMS‑tjänsten. Den är stabil och tidsoberoende. Den **långa JWT‑token** ska endast användas i Python‑skripten för OGC API Features.

---

## Förutsättningar

- Ett giltigt API‑konto hos Lantmäteriet (via apimanager.lantmateriet.se).
- QGIS 3.44 eller senare.
- Grundläggande vana vid att köra Python‑skript i QGIS Python‑konsolen.

---

## Användning

1. Kör `NGP_detaljplanekommuner.py` i QGIS (skapar `NGP_detaljplanekommuner.gpkg`).
2. Markera en eller flera kommuner i lagret.
3. Kör `NGP_planbestammelser.py` för att hämta planbestämmelser för markerade kommuner. Om ingen kommun är markerad laddas Skåne (alla kommuner med id som börjar på `12`).
4. Lägg till `Detaljplan_WMS.qlr` för att visa den officiella bakgrundskartan.

---

## Utdata

| Fil | Innehåll |
| --- | --- |
| `NGP_detaljplanekommuner.gpkg` | Kommuners avgränsningar (EPSG:3006) |
| `NGP_plans/planbestammelser_<id>.gpkg` | Planbestämmelser per kommun |
| `Detaljplan_WMS.qlr` | QGIS‑lager för Lantmäteriets WMS Detaljplan |

---

## Tekniska anteckningar

- Samtliga geometrier skrivs i **EPSG:3006**.
- Data hämtas via **NGP Detaljplan v2 – OGC API Features**.
- Attribut inkluderar bl.a. `beteckning`, `namn`, `status`, `lagakraft`, `typ`, `kategori` och `plan_url`.
- Skripten använder QGIS standard‑API samt `requests`.

---

## Licens och upphov

Utvecklad av **Mats Elfström** med tekniskt stöd av **ChatGPT (OpenAI)**.  
© 2025 – Fritt att använda för icke‑kommersiella och utbildningsmässiga syften.
