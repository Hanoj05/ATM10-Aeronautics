# Kanban

Daten für das Board auf `website/kanban.html`. Ersetzt die frühere `campus/roadmap.json` (übernommen mit `tools/migriere-roadmap.py`).

Normalerweise ändert man hier nichts von Hand: Auf der Website Karten anlegen, bearbeiten und per Drag & Drop verschieben, jede Änderung wird ein eigener Commit mit der Person als Autor.

| Datei | Inhalt |
| --- | --- |
| `phasen.json` | Die Phasen in ihrer Reihenfolge: `id`, `titel`, `ziel`. Auf dem Board als Filter und als Gruppierung |
| `liste.json` | IDs aller Karten |
| `karten/<id>.json` | Eine Karte |

Eine Datei pro Karte, damit zwei Leute gleichzeitig an verschiedenen Karten arbeiten können, ohne sich in die Quere zu kommen.

## Felder einer Karte

| Feld | Bedeutung |
| --- | --- |
| `id` | Kurzname aus dem Titel, gleich dem Dateinamen |
| `titel` | Was zu tun ist |
| `beschreibung` | Optional, mehr Text dazu |
| `status` | `offen`, `in Arbeit` oder `erledigt` (die drei Spalten) |
| `phase` | ID aus `phasen.json` |
| `wo` | `Minecraft` (im Spiel: bauen, einstellen, exportieren) oder `Website` (am Repo und an der Seite) |
| `bereich` | `Gebäude`, `3D`, `Doku`, `Website` oder `Betrieb` |
| `gebaeude` | Optional: Gebäude-ID aus `campus/campus.json`, dann verlinkt die Karte dorthin |
| `tab` | Optional: Tab der Gebäudeseite (`ansicht`, `konfig`, `bauplan`) |
| `zustaendig` | Liste von Profil-IDs aus `team/`, auch leer |
| `faellig` | Optional: Datum `JJJJ-MM-TT` |
| `rang` | Reihenfolge in der Spalte, kleiner steht weiter oben |

Wer doch von Hand eine Karte anlegt: Datei unter `karten/` schreiben und die ID in `liste.json` eintragen.
