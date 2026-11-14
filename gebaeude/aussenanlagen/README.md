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

**4. Umgebung**

- ME-Platz: die schwarze Bodenplatte wird Smooth Quartz mit Raster aus Light Gray Concrete (alle 12 Blöcke), dazu Baum-Inseln mit Sea Lanterns
- Landeplatz für Luftschiffe nördlich vom ME-Gebäude (Mitte 316 / −417, Radius 14) mit Weg zum Platz
- Wege auf Höhe 64: Magierweg (als Brücke über das Wasser), Nordweg Magiehaus–ME, Südtor zur Uferpromenade, Weg zur Bienenweide. Smooth Quartz mit Rand aus Light Gray Concrete, alle 9 Blöcke eine Sea Lantern im Rand
- Steg vom Ring-Ufer in die Bucht (330 / −152 bis 372 / −128) mit Plattform und Laternen
- Kahle Flächen (Stein, Kies, Erde) werden Wiese, am Wasser Sand
- Hain zwischen Magiehaus und Ring, Bienenweide östlich vom Wabenhaus, Bäume an der Promenade
- Magiehaus: Ecken außerhalb vom Kreis werden Wiese auf Bodenhöhe

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
