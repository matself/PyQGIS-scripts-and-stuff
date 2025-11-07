#  HVD Belägenhetsadresser – Index Builder för QGIS

Detta Python-script skapar ett GeoPackage med en centroidpunkt per svensk kommun, där varje objekt innehåller klickbara länkar till **Lantmäteriets Belägenhetsadresser-dataset** via STAC-API:t.

Scriptet är framtaget för **QGIS 3.44 (PyQGIS)** och utvecklat av **Mats Elfström & Gemini (Google 2025)**.

---

##  Funktion och syfte

Syftet är att snabbt skapa en översikt över vilka kommuner som har data tillgänglig i STAC-tjänsten, och erbjuda direkta nedladdningslänkar till respektive ZIP-fil.  
GPKG-filen innehåller ett enda lager: `kommun_centroid`, med attribut som kommunnamn, länskod, filstorlek, datum för skapande/uppdatering samt en **`download`-länk**.

---

##  Användning i QGIS

1. Öppna QGIS 3.44 eller senare.  
2. Gå till **Python-konsolen** (`Ctrl+Alt+P`).  
3. **Redigera credentials** högst upp i skriptet:
   ```python
   LM_USER = "DIN_ANVÄNDARE_HÄR"
   LM_PASS = "DITT_LÖSENORD_HÄR"
   ```
4. Kör hela skriptet i konsolen.  
5. Resultatet sparas som:
   ```
   C:/temp/belagenhetsadresser_index.gpkg
   ```
6. Lagret läggs automatiskt till i projektet.

---

##  Två funktioner att känna till

Skriptet skapar både data och erbjuder ett exempel på nedladdning:

### 1. Huvuddelen  
Körs direkt i Python-konsolen och bygger GeoPackage med en centroid per kommun.  

### 2. `download_kommun(kommun_title)`  
En funktion som kan köras **manuellt i konsolen** om man vill hämta ZIP-filen för en viss kommun:

```python
download_kommun("Luleå")
```

Den laddar ned filen till katalogen `C:/temp/lantmateriet_downloads`.

---

##  Viktigt

- **Autentisering krävs**.  
  Du måste ha giltiga användaruppgifter för Lantmäteriets STAC-tjänst.  
  Om du glömmer ändra `LM_USER` och `LM_PASS` stoppas skriptet automatiskt.

- **Körs i två steg**:  
  1. Huvudskriptet (bygg GeoPackage)  
  2. Valfri nedladdningsfunktion (`download_kommun`)  

- **Nedladdningslänkar** finns även som fält i tabellen `download` — du kan klicka på dessa direkt i QGIS attributtabell.

---

##  Utdata

| Fält | Beskrivning |
|------|--------------|
| `id` | Unikt STAC-id |
| `kommun` | Kommunnamn |
| `lanskod` | Länskod |
| `size_mb` | Storlek (MB) |
| `created` | Datum när datasetet skapades |
| `updated` | Datum för senaste uppdatering |
| `download` | Direktlänk till ZIP-fil |

---

##  Krav

- QGIS 3.44+  
- Lantmäteriet-konto med STAC-åtkomst  

---

##  Licens

Fri att använda och modifiera. Ange gärna källa:  
**Mats Elfström & Gemini (2025)**
