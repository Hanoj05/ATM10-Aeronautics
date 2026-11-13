# Hauptgebäude

Flacher Glasring nach dem Vorbild des Apple Park: 149 Blöcke Durchmesser, vier Etagen, an jeder Decke ein weißes Band, oben ein dünnes weißes Dach mit Solarfläche. Innen ein Park mit Hügeln, Obstbäumen, geschwungenen Wegen und Teich; darüber schwebt der Draconic Evolution Energy Core in einem weißen Ring auf vier Säulen. Steht dort, wo vorher Haus West und Haus Ost standen, nah am Wabenhaus. Ein Tor zeigt aufs Foyer des Wabenhauses, dazwischen liegt die Bienenallee mit Sechseck-Blumenbeeten. Zum ME-Gebäude führt eine Wasserallee mit zwei Wasserrinnen und Baumreihen.

| Datei | Inhalt |
| --- | --- |
| [gebaeude.json](gebaeude.json) | Steckbrief für die Website |
| [modell.json](modell.json) | Blockmodell, erzeugt von [tools/modell-hauptgebaeude.py](../../tools/modell-hauptgebaeude.py) |
| [konfig.json](konfig.json) | Teile mit Position (für die Hover-Ansicht) |
| [konfig.md](konfig.md) | Technik zum Lesen |
| [bauplan.html](bauplan.html) | Bauplan: Vorgehen, Abschnitte, Ebenen-Ansicht mit Weltkoordinaten, Material |
| [schematics/](schematics/) | Create-Schematics in 12 Bauabschnitten, erzeugt von [tools/bauhilfe-hauptgebaeude.py](../../tools/bauhilfe-hauptgebaeude.py) |
| [bauabschnitte.json](bauabschnitte.json) | Daten für den Bauplan (Ecken, Größen, Material) |

Modell neu erzeugen, nachdem man Maße im Skript geändert hat:

```
python3 tools/modell-hauptgebaeude.py
python3 tools/bauhilfe-hauptgebaeude.py
```

Das zweite Skript erzeugt die Schematics und die Bauplan-Daten neu.
