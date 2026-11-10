# ATM10 Aeronautics – Campus

Doku zu unserem Tech-Campus in der ATM10-Aeronautics-Welt. Jedes Gebäude hat eine Aufgabe (Bienen, ME, …) und einen eigenen Ordner mit Modell und Konfiguration. Daraus soll später eine Website werden: eine 3D-Ansicht vom ganzen Campus, in der man jedes Gebäude anklicken kann und dann dessen Übersicht bekommt.

## Aufbau

```
campus/
  campus.json          Liste aller Gebäude mit Lage in der Welt
  roadmap.json         Roadmap, angezeigt auf website/roadmap.html
gebaeude/
  vorlage/             Kopiervorlage für ein neues Gebäude
  wabenhaus/           Bienengebäude
    gebaeude.json      Steckbrief: Zellen, Maße, P0, Drehung, Dateien
    bauplan.html       Bauanleitung Block für Block
    modell.json        Blockmodell für die 3D-Ansicht
    konfig.json        Teile mit Position, Nodes und Kanälen (für die Website)
    konfig.md          Technik und Konfiguration zum Lesen
  me-zentrale/         ME-Gebäude
  haus-west/, haus-ost/  zwei Gebäude, Zweck noch offen
schematics/
  campus.nbt           die ganze Campus-Fläche, daraus werden alle Modelle ausgeschnitten
tools/                 Hilfsskripte: modell.json aus Bauplan oder Schematic, Zip bauen
website/               Die Campus-Website
download/              campus-ansicht.zip: nur Map und 3D-Ansicht, offline per Doppelklick
```

## Website ansehen

```
python3 -m http.server 8000
```

im Repo-Ordner starten und `http://localhost:8000` öffnen. Details in [website/README.md](website/README.md).

Ohne Server und ohne Technik: [download/campus-ansicht.zip](download/campus-ansicht.zip) entpacken und `index.html` öffnen.

## Neues Gebäude anlegen

1. Ordner `gebaeude/vorlage` kopieren und umbenennen, zum Beispiel `gebaeude/me-zentrale`.
2. `gebaeude.json` ausfüllen, vor allem `id`, `name` und `zweck`.
3. Das Gebäude in `campus/campus.json` eintragen.
4. `konfig.json` und `konfig.md` nach und nach füllen, dann erscheinen die Teile auf der Website.

## Gebäude

| Gebäude | Zweck | Status |
| --- | --- | --- |
| [Wabenhaus](gebaeude/wabenhaus/) | Bienen: Modular Beehive, Modular Centrifuge | gebaut |
| [ME-Gebäude](gebaeude/me-zentrale/) | AE2-Hauptsystem: ME Controller, 64 Extended Drives | im Bau |
| [Haus West](gebaeude/haus-west/) | noch offen | leer |
| [Haus Ost](gebaeude/haus-ost/) | noch offen | leer |

## Konventionen

- Block- und Itemnamen auf Englisch, so wie sie im Spiel und im JEI heißen.
- Koordinaten im Bauplan sind relativ zum Punkt P0 des Gebäudes. Die Weltkoordinate von P0 steht in `gebaeude.json` unter `welt.p0`.
- Keine versteckten Dateien. Leere Ordner bekommen eine `README.md`.
