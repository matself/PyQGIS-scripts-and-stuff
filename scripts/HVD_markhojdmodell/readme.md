# Markhöjdmodell 1m -- STAC-hämtning av tile-polygoner

Detta verktyg hämtar alla 1m-tiles från Lantmäteriets Markhöjdmodell som
faller inom ett angivet område. Resultatet lagras som polygoner i ett
GeoPackage i SWEREF 99 TM (EPSG:3006). Koden är avsedd att köras i QGIS
Python Console.

## Funktion och syfte

Skriptet använder Lantmäteriets STAC-API och producerar en polygon per
tile. Funktionen är användbar när man vill identifiera vilka
markhöjdmodeller som täcker ett visst projektområde och samtidigt
dokumentera vilka filer som kan laddas ned.

Metoden bygger på följande steg:

1.  Användaren anger en bounding box i EPSG:3006\
2.  Skriptet transformerar området till EPSG:4326 för STAC-sökningen\
3.  Endast de STAC-kollektioner vars utbredning överlappar området
    hämtas\
4.  Varje tile retransformeras från EPSG:4326 till EPSG:3006\
5.  GeoPackage skrivs med polygongeometrier och relevanta metadatafält

## Innehåll

Skriptet skapar en vektordatafil med följande fält:

-   **id**: Tile-ID från STAC\
-   **collection**: Kollektion som tile tillhör\
-   **datetime**: Produktions- eller insamlingsdatum\
-   **href**: Direktlänk till datafilen

## Användning

1.  Öppna QGIS och starta Python Console\
2.  Klistra in och kör skriptet\
3.  Ange egen bounding box i EPSG:3006 genom att ändra raden
    `bbox_3006 = [minX, minY, maxX, maxY]`\
4.  Ange egna OAuth-uppgifter\
5.  När skriptet är färdigt laddas lagret automatiskt in i QGIS

## Krav

-   QGIS 3.22 eller senare\
-   Python 3 via QGIS\
-   Ett giltigt konto för Lantmäteriets API-tjänster

## Begränsningar

STAC-API har en begränsad anropshastighet. Skriptet innehåller därför
både fördröjningar och ett förfilter som säkerställer att endast
relevanta kollektioner anropas. Detta gör körningen stabil även för
stora områden.

Skriptet hämtar metadata och tile-polygoner men inte själva
rasterfilerna. Nedladdning sker via de länkar som lagras i fältet
**href**.

## Samarbete och upphov

Detta verktyg har utvecklats i samarbete mellan Mats Elfström och
ChatGPT (GPT-5), genom iterativ utveckling och anpassning för robust
användning i svenska geodataflöden.

## Licenser

Kodexemplet är fritt att använda och anpassa. Data som hämtas via
Lantmäteriet regleras av respektive licensvillkor.
