# Ortnamn: Nedladdning och länsvis uppdelning (PyQGIS)

Detta pyqgis-skript laddar ner **Lantmäteriets ortnamnsdata** via deras
öppna STAC-gränssnitt och delar därefter upp datan i **länsvisa
geopackage-filer**:

    ortnamn_lan_<lanskod>_<lansnamn>.gpkg

Exempel:

    ortnamn_lan_12_skane_lan.gpkg
    ortnamn_lan_01_stockholms_lan.gpkg

Syftet är att ge användaren **små, överskådliga datafiler** istället för
Lantmäteriets nationella GPKG på \~60 MB.\
Allt sker **lokalt** på användarens dator -- ingen data redistribueras.

------------------------------------------------------------------------

## Funktioner

Skriptet:

1.  Hämtar STAC-metadata från Lantmäteriet\
2.  Laddar ner ZIP-filen med nationellt ortnamns-GPKG\
3.  Packar upp filen lokalt\
4.  Läser in den stora filen med alla ortnamnen i QGIS via PyQGIS\
5.  Skriver ett GPKG per län baserat på attributet `lanskod`\
6.  Sparar filerna på formen `ortnamn_lan_<kod>_<namn>.gpkg`

------------------------------------------------------------------------

## Förutsättningar

-   QGIS 3.22 eller senare\
-   PyQGIS (ingår i QGIS)
-   Ett konto hos **Lantmäteriet** med behörighet till STAC-tjänsten
-   Python-modulen `requests` (finns i QGIS standardinstallation)

------------------------------------------------------------------------

## Installation

Ingen installation krävs.\
Öppna QGIS → *Python Editor* → klistra in skriptet.

------------------------------------------------------------------------

## Konfiguration

Börja med att fylla i dina egna användaruppgifter i skriptet:

``` python
USERNAME = "DIN_ANVANDARE"
PASSWORD = "DITT_LOSEN"
OUT_ROOT = r"C:\temp\ortnamn_lan"
```

Spara och kör.

------------------------------------------------------------------------

## Resultat

Efter körning får du:

    OUT_ROOT/
        full_gpkg/
            ortnamn_se.gpkg  (original från Lantmäteriet)
        ortnamn_lan_01_stockholms_lan.gpkg
        ortnamn_lan_03_uppsala_lan.gpkg
        ...
        ortnamn_lan_25_norrbottens_lan.gpkg

------------------------------------------------------------------------

## Licens och attribution

Data kommer från:

**Lantmäteriet -- Ortnamn Nedladdning, licens CC BY 4.0**

Skriptet redistribuerar ingen data utan hjälper användaren att hämta och
hantera sin egen nedladdade kopia.

------------------------------------------------------------------------

## Syfte

Detta projekt syftar till att:

-   göra ortnamnsdata mer lättillgänglig\
-   ge användare en enklare struktur än det nationella samlingspaketet\
-   underlätta egen analys i QGIS och FME\
-   undvika att hosting eller redistribution behöver ske av tredje part

------------------------------------------------------------------------

## Support

Frågor eller förbättringsförslag välkomnas via GitHub-issues.
