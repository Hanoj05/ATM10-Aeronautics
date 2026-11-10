# ATM10 Aeronautics – Campus

Doku zu unserem Tech-Campus in der ATM10-Aeronautics-Welt. Jedes Gebäude hat eine Aufgabe (Bienen, ME, …) und einen eigenen Ordner mit Bauplan, Einrichtung und Konfiguration. Daraus soll später eine Website werden: eine 3D-Ansicht vom ganzen Campus, in der man jedes Gebäude anklicken kann und dann dessen Übersicht bekommt.

## Aufbau

```
campus/
  campus.json          Liste aller Gebäude mit Lage in der Welt
gebaeude/
  vorlage/             Kopiervorlage für ein neues Gebäude
  wabenhaus/           Bienengebäude
    gebaeude.json      Steckbrief: Zellen, Maße, P0, Drehung, Dateien
    bauplan.html       Bauanleitung Block für Block
    modell.json        Blockmodell für die 3D-Ansicht
    konfig.json        Teile mit Position, Nodes und Kanälen (für die Website)
    einrichtung.json   Einrichtungsteile mit Position und Status (für die Website)
    konfig.md          Technik und Konfiguration zum Lesen
    einrichtung.md     Stilregeln und Mods zum Lesen
schematics/            Exportierte Gebäude aus der Welt für die 3D-Ansicht
tools/                 Hilfsskripte, z. B. modell.json aus dem Bauplan erzeugen
website/               Die Campus-Website
```

## Website ansehen

```
python3 -m http.server 8000
```

im Repo-Ordner starten und `http://localhost:8000` öffnen. Details in [website/README.md](website/README.md).

## Neues Gebäude anlegen

1. Ordner `gebaeude/vorlage` kopieren und umbenennen, zum Beispiel `gebaeude/me-zentrale`.
2. `gebaeude.json` ausfüllen, vor allem `id`, `name` und `zweck`.
3. Das Gebäude in `campus/campus.json` eintragen.
4. `konfig.json` und `einrichtung.json` nach und nach füllen, dann erscheinen die Teile auf der Website.

## Gebäude

| Gebäude | Zweck | Status |
| --- | --- | --- |
| [Wabenhaus](gebaeude/wabenhaus/) | Bienen: Modular Beehive, Modular Centrifuge | gebaut |
| ME-Gebäude | AE2-Hauptsystem | geplant |

## Konventionen

- Block- und Itemnamen auf Englisch, so wie sie im Spiel und im JEI heißen.
- Koordinaten im Bauplan sind relativ zum Punkt P0 des Gebäudes. Die Weltkoordinate von P0 steht in `gebaeude.json` unter `welt.p0`.
- Keine versteckten Dateien. Leere Ordner bekommen eine `README.md`.
