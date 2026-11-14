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
| `karte` | optional: `false` blendet das Gebäude auf der Map aus, es bleibt in der Liste |
| `drehung` | 0, 90, 180 oder 270: um wie viel Grad im Uhrzeigersinn das Gebäude gegenüber dem Plan gedreht gebaut ist. 90 heißt: Plan-Norden zeigt nach Osten |

`gelaende.json` (optional) ist das Gelände für die Map, erzeugt mit `tools/modell-gelaende.py`. Mehr dazu im Haupt-README unter „Anderen Stand auf der Map ansehen“.

## Roadmap

Die Roadmap ist jetzt das Kanban-Board, Daten und Felder in [kanban/README.md](../kanban/README.md).
