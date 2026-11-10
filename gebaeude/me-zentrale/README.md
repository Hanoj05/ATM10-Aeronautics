# ME-Gebäude

Zentrale des AE2-Hauptsystems: ein ME Controller als Säule in der Mitte, vier Drive-Bänke mit je 16 ME Extended Drives in den Ecken, oben ein ME Wireless Hub.

| Datei | Inhalt |
| --- | --- |
| [gebaeude.json](gebaeude.json) | Steckbrief für die Website |
| [modell.json](modell.json) | Blockmodell, erzeugt aus [schematics/me-zentrale.nbt](../../schematics/me-zentrale.nbt) |
| [konfig.json](konfig.json) | Teile mit Position (für die Hover-Ansicht) |
| [konfig.md](konfig.md) | Technik und Konfiguration zum Lesen |

Modell neu erzeugen, wenn die Schematic ersetzt wurde:

```
python3 tools/modell-aus-schematic.py gebaeude/me-zentrale
```
