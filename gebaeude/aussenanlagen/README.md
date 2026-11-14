# Außenanlagen

## Plan für die Umgebung (Branch `umgebung-plan`)

So soll der Campus fertig aussehen. Auf der Map unter **Stand** `umgebung-plan` wählen und mit `umgebung` (Ist-Stand) vergleichen. Alles kommt aus `tools/plan-umgebung.py`, Koordinaten sind Weltkoordinaten.

**1. Keine Monster mehr: Mega Torches** (Torchmaster, Reichweite 64 als Würfel, auf etwa Y 64 einbauen)

| | X / Z | Versteck |
| --- | --- | --- |
| T1 | 88 / −221 | Mitte Magiehaus, im Keller unter der Kuppel |
| T2 | 158 / −196 | zwischen Magiehaus und Ring, unter dem Weg |
| T3 | 236 / −324 | unter dem ME-Platz |
| T4 | 286 / −196 | im Park, unter einem Beet |
| T5 | 362 / −300 | Nordwest-Ecke im Wabenhaus |

Auf der Map stehen sie als goldene Säulen, damit man sie findet. Gebaut werden sie versteckt.

**2. Licht**

- Hauptgebäude-Dach: Sea Lanterns an den Enden der weißen Rippen und als Lichtkranz auf dem inneren und äußeren weißen Rand (jeder dritte Block)
- Park: Laternen am Rand der Quarzwege
- Magiehaus-Dach: an den Sternkanten Sea Lantern mit Purple Stained Glass darüber

**3. Kellerdecke im Magiehaus:** unter jedem Grasblock, der direkt über dem Keller liegt, eine Smooth Quartz Slab in der oberen Hälfte. Von oben bleibt der Rasen, unten wird eine Kassettendecke in der Form der Gärten daraus. Der Raum verliert dort einen halben Block.

**4. Ein gemeinsamer Campus**

Alle vier Gebäude liegen auf einer gemeinsamen, ebenen Fläche. Innerhalb der Campus-Grenze wird alles auf Höhe 65 planiert, also auf die Bodenhöhe der Gebäude. Flüsse und Buchten werden zugeschüttet, Hügel abgetragen und die wilden Bäume entfernt. Außerhalb bleibt die Natur.

- Grenze: Rechteck x 8 bis 422, z −446 bis −116, Ecken mit Radius 36. Der alte Bau im Osten (ab x 424) bleibt draußen.
- Außen ein Bordstein, dahinter ein Rundweg (5 breit) mit Lichtern im Rand und eine Eichen-Allee.
- Wege gehen von den echten Toren des Rings aus: Tor 148° zum Magiehaus (Magierweg), Tor 328° zum Wabenhaus (Bienenallee), Tor 238° zum ME-Platz, Tor 58° zur Südterrasse. Dazu der Nord-, West- und Südweg vom Magiehaus und zwei Wege vom Wabenhaus. Alle sind gleich gebaut: Smooth Quartz, Rand aus Light Gray Concrete, alle 8 Blöcke eine Sea Lantern. An den Wegen stehen Birken-Alleen, die Wiesen dazwischen bleiben offen.
- ME-Platz (x 205–326, z −404 bis −306): Smooth Quartz mit Raster aus Light Gray Concrete alle 12 Blöcke, Baum-Inseln mit vier Lichtern
- Landeplatz für Luftschiffe auf der Nordachse (Mitte 263 / −420, Radius 12)
- Wasserband auf der Südterrasse (x 213–313, z −131 bis −126) mit Quarzrand und Lichtern
- Bienenweide südlich vom Wabenhaus mit Blumen in Streifen
- Magiehaus und Hauptgebäude: alles außerhalb vom Kreis bzw. der Ring-Anlage wird Campus-Wiese

Neu rechnen: `python3 tools/plan-umgebung.py` (etwa eine Minute).

## Älterer Entwurf (main)

Wege, Haine, Blumenwiesen, Teiche und Laternen auf den Flächen zwischen den Gebäuden:

- **Promenade:** Kreisweg mit Radius 95 um das Hauptgebäude, mit Sea-Lantern-Laternen
- **Magierweg:** geschwungener Weg vom Westsüdwest-Tor des Rings zum Magiehaus, mit Archwood-Allee und Amethyst-Laternen
- **Zuwege:** von den beiden freien Ring-Toren zur Promenade
- **Haine und Wiesen:** Eiche, Birke und Kirsche, am Magiehaus Archwood in vier Farben, dazwischen Blumenflecken
- **Teiche:** drei kleine Teiche im äußeren Gürtel

Die Gebäude bleiben unberührt, ihre Grundflächen sind mit 2 Blöcken Abstand ausgespart. Gebaut wird von Hand nach [bauplan.html](bauplan.html) (Reihenfolge, Baum-Vorlagen, Koordinatenlisten, Ebenen-Ansicht, Material).

| Datei | Inhalt |
| --- | --- |
| [gebaeude.json](gebaeude.json) | Steckbrief für die Website |
| [modell.json](modell.json) | Blockmodell |
| [bauanleitung.json](bauanleitung.json) | Daten für die Bauanleitung |
| [bauplan.html](bauplan.html) | Bauanleitung für den Handbau |

Neu erzeugen:

```
python3 tools/modell-aussenanlagen.py
```
