# Schematics

Exporte der echten Gebäude aus der Welt. Daraus soll die Website später die 3D-Ansicht Block für Block bauen.

Die ganze Campus-Fläche liegt als eine Datei vor. Jedes Gebäude schneidet sich seinen Teil daraus aus.

| Datei | Inhalt |
| --- | --- |
| `campus.nbt` | ganze Fläche, Stand 10.11.2026. Ecke (0, 0, 0) = Welt 221, 65, −391 |

## Ausschnitt pro Gebäude

In `gebaeude/<id>/gebaeude.json`:

```json
"dateien": { "schematic": "schematics/campus.nbt", ... },
"ausschnitt": { "schematicP0": [221, 65, -391], "von": [x, y, z], "bis": [x, y, z] }
```

`von` und `bis` sind Weltkoordinaten. Das Skript rechnet die Blöcke über `welt.p0` und `welt.drehung` in die Koordinaten des Gebäudes um, beim gedrehten Wabenhaus also in die Plan-Koordinaten. Gelände in der untersten Lage bleibt nur innerhalb des Gebäudes stehen.

## Über die Website (empfohlen)

Auf der Website unter **Import** die neue `campus.nbt` hochladen, Vorschau prüfen, übernehmen. Das macht alles unten automatisch und ist im Haupt-README unter „Karte aktualisieren“ für alle ohne Technikwissen beschrieben.

Pro Gebäude steht in `gebaeude.json` unter `modellquelle`, woher das Modell kommt: `schematic` (aus dem Ausschnitt dieser Datei) oder `entwurf` (aus dem Skript in `dateien.generator`). Gebäude mit `entwurf` lässt `--alle` aus.

## Ins Modell für die Website umwandeln

```
python3 tools/modell-aus-schematic.py --alle
```

Schreibt für jedes Gebäude `modell.json`, einzeln geht `python3 tools/modell-aus-schematic.py gebaeude/<id>`. Braucht keine Zusatzpakete. Blockfarben stehen in der Tabelle `FARBEN` im Skript, unbekannte Blöcke bekommen eine Ersatzfarbe und werden beim Lauf aufgelistet.

Bei einer neuen Campus-Schematic: Datei ersetzen, `schematicP0` prüfen (Weltkoordinate der Ecke, die Create als (0, 0, 0) nimmt, also kleinstes x, y und z der Auswahl), dann `--alle`.

Was die Schematic nicht enthält: Inventare (Zellen in Drives, Items in Barrels) und Logistics Nodes. Die Nodes sind Entities und werden nicht mitgespeichert, sie stehen weiter von Hand in `konfig.json`.

## Export mit Create

Create ist in ATM10 dabei und bringt alles mit:

1. Schematic and Quill craften und in die Hand nehmen.
2. Erste Ecke des Gebäudes anklicken, dann die gegenüberliegende Ecke. Mit Strg und Mausrad lässt sich die Auswahl noch anpassen.
3. Speichern und einen Namen vergeben.
4. Die Datei liegt danach im Ordner `schematics` der Prism-Instanz (neben `mods` und `saves`). Hierher kopieren.

Achtung: Create begrenzt die Größe beim Hochladen auf Server. Für den reinen Export lokal ist das egal. Falls ein Gebäude zu groß wird, in Teilen exportieren, zum Beispiel `wabenhaus-nord.nbt` und `wabenhaus-sued.nbt`.

## Wichtig für die Auswahl

- Auf Bodenhöhe anfangen, sonst fehlt der Boden.
- Blöcke aus Mods (Maschinen, Deko) werden mitgespeichert. Die Website zeigt sie erst als farbige Blöcke, Texturen kommen vielleicht später.
