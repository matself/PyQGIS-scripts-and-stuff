
# Lantmäteriet STAC API – Exempelskript

Detta skript visar hur man kan hämta metadata om ortofoton från **Lantmäteriets STAC-API** och skapa ett **GeoPackage** med fotavtryck eller centroids för tillgängliga bildrutor.

Syftet är att ge ett praktiskt exempel för användning i **QGIS** och andra miljöer som stöder Python och PyQGIS.

---

## Syfte

Skriptet:
- autentiserar mot Lantmäteriets STAC-API för bilddata  
- hämtar alla ortofoton inom ett angivet område (bbox)  
- skapar ett GeoPackage-lager med metadata (år, upplösning, kampanjkod, länk till data)  
- kan köras direkt i QGIS Python-konsolen

---

##  Förberedelser

1. **Hämta API-nycklar**
   - Skapa konto hos Lantmäteriet:  
     [https://api.lantmateriet.se](https://api.lantmateriet.se)
   - Registrera din applikation och kopiera:
     ```
     consumer_key    = "DIN_CONSUMER_KEY"
     consumer_secret = "DIN_CONSUMER_SECRET"
     ```

2. **Ange område**
   - Justera variabeln `bbox_3006` till ditt område i **SWEREF 99 TM (EPSG:3006)**:
     ```python
     bbox_3006 = (minE, minN, maxE, maxN)
     ```
   - Exempel (Skåne):
     ```python
     bbox_3006 = (337500, 6127500, 487500, 6265000)
     ```

3. **Välj utfil**
   - Ange sökväg för GeoPackage:
     ```python
     gpkg_path = "C:/temp/ortofoto_footprints_example.gpkg"
     ```

---

##  Körning i QGIS

1. Öppna **QGIS Python-konsolen**  
2. Klistra in hela skriptet  
3. Kör det rad för rad eller i ett stycke  

Om allt fungerar:
- en token hämtas från Lantmäteriet  
- STAC-sökningen returnerar tillgängliga ortofotorutor  
- ett nytt lager skapas i QGIS-projektet med polygoner och attribut

---

##  Resultat

GeoPackage-lagret innehåller:
| Fält | Innehåll |
|------|-----------|
| `id` | Unikt tile-ID |
| `datetime` | Datum/tid för bildruta |
| `href` | Länk till STAC-post eller data |
| `year` | Bildår (beräknat) |
| `res_m` | Upplösning i meter |
| `campaign` | Kampanjkod |

Observera att **själva bilderna inte laddas ned** – endast metadata.  
För att ladda hem bilder krävs giltig åtkomst och separat API-förfrågan.

---

##  Exempel på områden

| Region | SWEREF 99 TM (EPSG:3006) |
|---------|---------------------------|
| Stockholm | (650000, 6570000, 680000, 6600000) |
| Göteborg  | (310000, 6380000, 340000, 6400000) |
| Norrbotten | (730000, 7280000, 820000, 7400000) |
| Ystad (test) | (420000, 6155000, 455000, 6180000) |

---

##  Licens och användning

- Data © **Lantmäteriet**, licensierad under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Skriptexempel © 2025 **Mats Elfström** & bidragsgivare
- Resultatet innehåller endast öppna metadata
- Dela aldrig dina personliga API-nycklar offentligt

---

##  Testad miljö

| Komponent | Version |
|------------|----------|
| QGIS | 3.44.x |
| Python | 3.12 |
| PyQt | 5.x |
| OS | Windows 10 Pro |

---

##  Tips

- Du kan ändra `Polygon?crs=EPSG:4326` till `Point?crs=EPSG:4326` om du hellre vill skapa centroids.  
- Om du redan har en lista över tile-ID:n kan du filtrera `feats` innan du skriver till fil.  
- Kombinera gärna med andra STAC-endpoints, exempelvis:
  - [STAC Höjd (Elevation)](https://api.lantmateriet.se/stac-hojd/v1)  
  - [STAC Laser (LIDAR)](https://api.lantmateriet.se/stac-laser/v1)

---

##  Samarbete

Detta exempelskript utvecklades gemensamt genom diskussion mellan  
**Mats Elfström** och **ChatGPT (GPT-5)**, som del i ett arbete att skapa reproducerbara exempel för STAC-baserad datatillgång i QGIS-miljöer.
