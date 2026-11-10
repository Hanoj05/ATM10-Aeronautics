# Schematics

Exporte der echten Gebäude aus der Welt. Daraus soll die Website später die 3D-Ansicht Block für Block bauen.

Dateiname = Gebäude-ID, also zum Beispiel `wabenhaus.nbt`. In `gebaeude/<id>/gebaeude.json` unter `dateien.schematic` eintragen.

## Export mit Create

Create ist in ATM10 dabei und bringt alles mit:

1. Schematic and Quill craften und in die Hand nehmen.
2. Erste Ecke des Gebäudes anklicken, dann die gegenüberliegende Ecke. Mit Strg und Mausrad lässt sich die Auswahl noch anpassen.
3. Speichern und einen Namen vergeben.
4. Die Datei liegt danach im Ordner `schematics` der Prism-Instanz (neben `mods` und `saves`). Hierher kopieren.

Achtung: Create begrenzt die Größe beim Hochladen auf Server. Für den reinen Export lokal ist das egal. Falls ein Gebäude zu groß wird, in Teilen exportieren, zum Beispiel `wabenhaus-nord.nbt` und `wabenhaus-sued.nbt`.

## Wichtig für die Auswahl

- Die Nordwest-Ecke der Auswahl sollte P0 sein, auf Bodenhöhe. Dann passen die Koordinaten aus dem Bauplan direkt.
- Blöcke aus Mods (Maschinen, Deko) werden mitgespeichert. Die Website zeigt sie erst als farbige Blöcke, Texturen kommen vielleicht später.
