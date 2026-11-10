# Campus

`campus.json` ist die zentrale Liste aller Gebäude. Die Website liest sie ein, um die Gebäude auf der Karte zu platzieren.

Pro Gebäude:

| Feld | Bedeutung |
| --- | --- |
| `id` | Kurzname, gleich wie der Ordnername unter `gebaeude/` |
| `name` | Anzeigename |
| `ordner` | Pfad zum Gebäudeordner, `null` wenn noch keiner existiert |
| `zweck` | Wofür das Gebäude da ist |
| `status` | `geplant`, `im Bau` oder `gebaut` |
| `position` | Weltkoordinate von P0 als `[x, y, z]`, im Spiel mit F3 ablesen |
| `drehung` | 0, 90, 180 oder 270: um wie viel Grad im Uhrzeigersinn das Gebäude gegenüber dem Plan gedreht gebaut ist. 90 heißt: Plan-Norden zeigt nach Osten |

## Roadmap

`roadmap.json` ist die Roadmap für Campus und Website, die Seite `website/roadmap.html` zeigt sie an. Pro Phase `titel`, `ziel` und `punkte`. Pro Punkt:

| Feld | Bedeutung |
| --- | --- |
| `titel` | Was zu tun ist |
| `wo` | `Minecraft` (im Spiel: bauen, einstellen, exportieren) oder `Website` (am Repo und an der Seite) |
| `status` | `erledigt`, `in Arbeit` oder `offen` |
| `bereich` | `Gebäude`, `3D`, `Doku`, `Website` oder `Betrieb` |
| `text` | Optional: ein Satz mehr dazu |
| `gebaeude`, `tab` | Optional: verlinkt auf die Gebäudeseite, z. B. Tab `konfig` |
