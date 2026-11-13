# ME-Gebäude – Technik und Konfiguration

AE2-Hauptsystem.

Das Gebäude ist ein Ausschnitt aus der Campus-Schematic `schematics/campus.nbt`. Koordinaten sind relativ zur Ecke (0, 0, 0) des Gebäudes, das ist die Ecke unten im Nordwesten des Baukörpers, in der Welt 246, 65, -385 (x nach Osten, z nach Süden, y = 0 ist die Bodenebene).

Der Baukörper ist 53 × 53 Blöcke groß und 98 hoch. An der Nord-, Süd- und Ostseite stehen Framed Panels einen Block weiter außen, mit ihnen ist das Modell 54 × 55 groß und reicht an der Nordseite bis z = -1.

## Übersicht

Aus der Schematic ausgelesen:

| Teil | Anzahl | Position |
| --- | --- | --- |
| ME Controller | 157 Blöcke | Grundfläche 23, 23 bis 29, 29 in der Mitte. Keine volle Säule: belegt sind y 15 bis 21, 26 und 31 |
| ME Extended Drive | 64 | vier Bänke à 16, y 7 bis 10, in den Ecken |
| ME Wireless Hub | 1 | 26, 32, 26 (oben auf dem Controller) |
| ME Wireless Access Point | 1 | 26, 19, 26 (im Controller-Schacht) |
| ME Wireless Connector | 10 | 8 im Ring auf y 27 bei x/z 24 bis 28, in der Lücke des Controllers. Je einer bei 12, 19, 26 (West) und 40, 19, 26 (Ost) |
| Ender Gate (Nitro) | 3 | 26, 17, 26 · 26, 26, 25 · 26, 31, 25 |
| ME Smart Cable | 222 | Blue, Black und White, normal und Dense, y 11 bis 30. Dazu 58 ME P2P Tunnels |

## Drive-Bänke

| Bank | Von | Bis |
| --- | --- | --- |
| Nordwest | 7, 7, 7 | 15, 10, 15 |
| Nordost | 37, 7, 7 | 45, 10, 15 |
| Südwest | 7, 7, 37 | 15, 10, 45 |
| Südost | 37, 7, 37 | 45, 10, 45 |

## Anbindungen

| Wohin | Wie |
| --- | --- |
| Wabenhaus | Powah Ender Gate, Kanal 0: 3 Gates hier, 1 im Wabenhaus |
| Altes Haus | ME Wireless Connector West und Ost. Das alte Haus ist nicht Teil des Campus |

## Hinweise

- Die Schematic speichert keine Inventare. Zellen, Prioritäten und Partitionen von Hand eintragen.

## Stand

- [x] Weltkoordinate von P0 eingetragen: 246, 65, -385 (eingemessen am ME Wireless Hub = Welt 272, 97, -359)
- [ ] Einstellungen (Zellen, Prioritäten, Kanäle) ergänzen
