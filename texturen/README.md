# Texturen

Blocktexturen für die 3D-Ansicht, nur die Blöcke, die in einem `gebaeude/*/modell.json` vorkommen.

| Datei | Inhalt |
| --- | --- |
| `atlas.png` | alle Texturen in einem Bild, je 16 x 16 Pixel mit 8 Pixel Rand (gegen Farbbluten in der Ferne) |
| `texturen.json` | `bloecke`: Block-ID -> Textur je Seite (`up`, `down`, `north`, `south`, `west`, `east`), `texturen`: Textur -> Kachelnummer im Atlas und Alpha (`voll`, `loch` = ausgestanzt, `halb` = durchscheinend) |

Neu erzeugen, zum Beispiel nach einem neuen Gebäude oder neuen Blöcken im Modell:

```
python3 tools/hole-texturen.py "<Pfad zur Prism-Instanz>"
python3 tools/baue-ansicht-zip.py
```

Ohne Pfad nimmt das Skript die Flatpak-Instanz `All the Mods 10 Aeronautics ATM10A`. Es braucht keine Zusatzpakete.

- Vanilla-Texturen kommen aus der Minecraft-Client-Jar unter `PrismLauncher/libraries/com/mojang/minecraft/1.21.1/`, alles andere aus `minecraft/mods/*.jar`.
- Der Weg ist wie im Spiel: Blockstate -> Blockmodell mit Parent-Kette -> Textur je Seite. Deshalb stimmen oben, unten und Seite bei Logs, Grass Block, Quartz Pillar und Co.
- Gras, Laub und Wasser sind mit der Plains-Farbe eingefärbt, Birch Leaves, Spruce Leaves und Lily Pad mit ihrer festen Farbe, Productive-Bees-Bienenstöcke mit der Holzfarbe.
- Gleiche Eingaben ergeben Byte für Byte dieselben Dateien, auch bei der Zip. Nach einem Lauf ohne neue Blöcke zeigt git also keine Änderung.
- Framed Blocks bekommen die Textur ihrer Tarnung (`framedblocks:framed_panel|minecraft:white_concrete`).
- Blöcke, deren Modell erst im Spiel per Code entsteht (AE2-Kabel, Extended Drive), stehen als Sonderfall im Skript unter `SONDERFAELLE`.
- `platzhalter:`-Blöcke und alles ohne Textur bleiben in der Ansicht einfarbig (Farbe aus der Palette).

Die Texturen gehören Mojang und den jeweiligen Mod-Autoren und liegen hier nur für unsere eigene Ansicht.
