# ME-Gebäude – Technik und Konfiguration

AE2-Hauptsystem. Einrichtung und Deko stehen in [einrichtung.md](einrichtung.md).

Koordinaten sind relativ zur Ecke (0, 0, 0) der Schematic `schematics/me-zentrale.nbt`, das ist die Ecke unten im Nordwesten (x nach Osten, z nach Süden, y = 0 ist die Bodenebene). Das Gebäude ist 53 × 53 Blöcke groß und 98 hoch.

## Übersicht

Aus der Schematic ausgelesen:

| Teil | Anzahl | Position |
| --- | --- | --- |
| ME Controller | 157 Blöcke | 23, 15, 23 bis 29, 31, 29 (Säule in der Mitte) |
| ME Extended Drive | 64 | vier Bänke à 16, y 7 bis 10, in den Ecken |
| ME Wireless Hub | 1 | 26, 32, 26 (oben auf dem Controller) |
| ME Wireless Connector | 10 | 8 im Ring auf y 27 um den Controller, je einer bei 12, 19, 26 und 40, 19, 26 |
| Ender Gate (Nitro) | 3 | 26, 17, 26 · 26, 26, 25 · 26, 31, 25 |
| ME Smart Cable | 222 | Blue, Black und White, normal und Dense, y 11 bis 30. Dazu 58 ME P2P Tunnels |

## Drive-Bänke

| Bank | Von | Bis |
| --- | --- | --- |
| Nordwest | 7, 7, 7 | 15, 10, 15 |
| Nordost | 37, 7, 7 | 45, 10, 15 |
| Südwest | 7, 7, 37 | 15, 10, 45 |
| Südost | 37, 7, 37 | 45, 10, 45 |

## Hinweise

- 

## Stand

- [ ] Weltkoordinate von P0 in `gebaeude.json` und `campus/campus.json` eintragen
- [ ] Einstellungen (Zellen, Prioritäten, Kanäle) ergänzen
