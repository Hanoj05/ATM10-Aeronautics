# Wabenhaus – Technik und Konfiguration

Alles, was eingestellt werden muss: Maschinen, Logistics Network, Filter, Energie.

Koordinaten sind Plan-Koordinaten relativ zu P0 (x nach Plan-Osten, z nach Plan-Süden, y = 0 ist der Boden).

Das Wabenhaus ist um 90° im Uhrzeigersinn gedreht gebaut: Plan-Norden zeigt in der Welt nach Osten, das Foyer liegt im Westen. Umrechnung in Weltkoordinaten: **Welt = (392 − z, 65 + y, −285 + x)**. Beispiel: Hive-Core (7, 2, 12) liegt in der Welt bei (380, 67, −278). Eingemessen über die Campus-Schematic vom 10.11.2026.

## Übersicht

| Teil | Ort | Position |
| --- | --- | --- |
| Modular Beehive | Produktion | x 6–8, y 1–3, z 10–12, Core vorne (7, 2, 12) |
| Modular Centrifuge | Produktion | x 17–19, y 1–3, z 10–12, Core vorne (18, 2, 12) |
| Overclocker Barrel | Technik | (41, 1, 20) |
| Honey Block Barrel | Technik | (41, 1, 21) |
| Bottle Barrel | Technik | (41, 1, 22) |
| Wax Barrel | Technik | (41, 1, 23) |
| Receiver Barrel | Technik | (41, 1, 24) |
| Energy Cube | Technik | (37, 1, 15) |
| Output Tank | Honigturm | (31, 1, 0) |

## Modular Beehive

Aufbau: 3 × 3 × 3, Ebenen von unten nach oben, Zeilen von hinten nach vorne.

```
y 1   A A A      y 2   T O T      y 3   O O O
      A A A            T A T            O F O
      A A A            O C O            O O O
```

A = Modular Alveary (10), O = Beehive Overclocker (11), T = Beehive Treater (4), C = Core (1), F = Modular Feeder (1).

| Teil | Einstellung |
| --- | --- |
| Core | 4 × Productivity Upgrade: Omega |
| Bienen | Draconic, Obsidian, Withered |
| Feeder | Blumenblöcke, für Draconic Bees ein Dragon Egg. Wird nicht verbraucht |
| Treater | Honey Blocks (+15 %) oder Honey Treats. Verbrauch pro Zyklus = Treater × Bienen |
| Overclocker | Strom nur über die gemusterte Seite, dazu eine Elektrode. Netherite ist am stärksten, verbraucht sich aber laufend |

## Modular Centrifuge

Aufbau: 3 hoch, unten nur die vier Eckbeine.

```
y 1   G . G      y 2   O E O      y 3   O O O
      . . .            G H G            G I G
      O . O            O C O            O O O
```

O = Centrifuge Overclocker (12), G = Centrifuge Gearbox (6), H = Centrifuge Heater (1), I = Import Hatch (1), E = Export Hatch (1), C = Core (1).

| Teil | Braucht | Wirkung |
| --- | --- | --- |
| Overclocker | Strom und Elektrode | schnellerer Zyklus, Boni addieren sich |
| Gearbox | Wax, 40 pro Zyklus | 1,5 × Combs pro Zyklus, solange Wax da ist |
| Heater | Strom | 3 × Tempo, verarbeitet Comb-Blöcke (4 × Ausbeute). Vernichtet dabei alles Wax. Höchstens einer, sonst bildet sich die Struktur nicht |
| Core | Upgrades | Productivity: mehr Combs pro Durchgang. Time: schneller. Stability: höhere Chancen |
| Import / Export Hatch | Node | Combs rein, Produkte und Flüssigkeiten raus |

Zwei Import Hatches nie aufeinander zeigen lassen, das erzeugt Geister-Combs.

## Logistics Network „Bienchen“

Alle Nodes mit Netherite Upgrade. Kanalnummern wie im Spiel, ab 0 gezählt. Den Takt (Tick Delay) stellt man am **sendenden** Node ein, die Mod rechnet die Wartezeit pro Sender-Kanal.

### Kanäle

| Kanal | Typ | Sender | Empfänger | Takt |
| --- | --- | --- | --- | --- |
| 0 | Items | Hive Core (Honigflaschen), Centr Export (Draconic Dust, Obsidian Shard, Wither Skull Chip; Priorität −1) | Receiver Barrel (alles) | 40 Ticks |
| 1 | Items | Hive Core (Comb-Blöcke: Draconic, Obsidian, Withered) | Centr Import (dieselben drei) | 20 Ticks |
| 2 | Items | Overclocker Barrel, Honey Block Barrel, Bottle Barrel, Wax Barrel (Round Robin) | Overclocker (Netherite-Elektroden), Treater (Honey Treats, Honey Blocks), Hive Core (Glass Bottles), Gearbox (Wax) | 200 Ticks |
| 5 | Flüssigkeit | Hive Core, Centr Export | Output Tank | 40 Ticks |
| 8 | Energie | Energy Source am Energy Cube (alle Seiten) | Overclocker (alle Seiten), Heater | jeden Tick, fest in der Mod |

K3 (Wax aus der Zentrifuge in die Gearboxen) ist gestrichen: Mit Heater gibt die Zentrifuge kein Wax aus, der Kanal hat nie etwas transportiert.

### Leistung

Gemessen mit Spark am 10.11.2026, 4 Minuten, ganzer Server bei rund 57 ms pro Tick (TPS 17). Logistics Networks lag bei etwa **1 ms pro Tick, knapp 2 %**. Die Nodes sind also nicht der Grund für die Ruckler. Trotzdem lässt sich das Netz entlasten:

1. **K8 ist der Wecker.** Energie-Kanäle laufen in der Mod fest jeden Tick, unabhängig vom eingestellten Takt. Weil die 23 Overclocker und der Heater dauernd Strom ziehen, ist jede Übertragung erfolgreich, und die Mod weckt das ganze Netz „Bienchen“ im nächsten Tick wieder auf. Dann baut sie jedes Mal für alle 44 Nodes ihre Listen neu auf, auch wenn kein Item-Kanal dran ist. Das ist der größte Teil der 1 ms.
2. **Ohne K8 schläft das Netz.** Den Strom für Overclocker und Heater per Kabel liefern statt über Nodes, z. B. mit Mekanism Universal Cables oder Powah Energy Cables an die gemusterte Seite. Dann wacht „Bienchen“ nur noch auf, wenn ein Item- oder Flüssigkeitskanal dran ist. Nachteil: Kabel rund um Hive und Zentrifuge, die man verkleiden muss.
3. **Takte hochsetzen.** Nachschub (K2) reicht alle 10 Sekunden, mit Netherite Upgrade gehen pro Durchgang bis zu 10.000 Items. Produkte und Honig (K0, K5) alle 2 Sekunden. Wirkt erst richtig, wenn K8 weg ist.
4. **K3 abbauen**, siehe oben. Spart pro Gearbox und am Centr Export einen Kanal.
5. **Redstone-Modus auf „Ignored“ lassen.** Jeder Kanal mit Redstone-Bedingung lässt die Mod bei jedem Durchlauf die Signale aller Nodes prüfen.

Was im selben Profil wirklich Zeit kostet:

| Was | Anteil | pro Tick |
| --- | --- | --- |
| Mobs, vor allem Zombies, Skelette und Creeper, mit ihrer KI | gut 23 % | ca. 13 ms |
| Tick-Events von Curios, Accessories, Mahou Tsukai, Draconic Evolution, die pro Lebewesen laufen | gut 5 % | ca. 3 ms |
| AE2: Speicherinhalt jeden Tick neu zusammenzählen | 8,5 % | ca. 4,9 ms |
| Aeronautics-Physik, davon Simulated Coasters ca. 3,3 ms | 8 % | ca. 4,6 ms |
| Logistics Networks | 1,8 % | ca. 1 ms |
| Productive Bees (fliegende Bienen) | 1,2 % | ca. 0,7 ms |

### Nodes

| Label | Anzahl | Kanäle |
| --- | --- | --- |
| Overclocker | 23 | K2 rein (Elektroden), K8 rein (FE). 11 am Hive, 12 an der Zentrifuge |
| Treater | 4 | K2 rein (Honey Treats, Honey Blocks) |
| Hive Core | 1 | K0 raus, K1 raus, K2 rein (Glass Bottles), K5 raus |
| Centr Import | 1 | K1 rein |
| Centr Export | 1 | K0 raus, K5 raus |
| Gearbox | 6 | K2 rein (Wax) |
| Heater | 1 | K8 rein (FE) |
| Energy Source | 1 | K8 raus |
| Overclocker Barrel | 1 | K2 raus |
| Honey Block Barrel | 1 | K2 raus |
| Bottle Barrel | 1 | K2 raus |
| Wax Barrel | 1 | K2 raus (Round Robin) |
| Receiver Barrel | 1 | K0 rein |
| Output Tank | 1 | K5 rein |

Zusammen 44 Nodes.

### Wo die Nodes sitzen

- **Hive:** Overclocker und Treater auf ihrer Außenseite, der Core vorne. Die Alveary-Ebene unten braucht keine.
- **Zentrifuge:** Außenseiten wie beim Hive. Die Heater-Node sitzt unter dem Heater zwischen den Beinen (18, 1, 11), die Import-Node oben auf dem Import (18, 4, 11).
- **Heater:** Als einzige Energie-Node ohne „alle Seiten“. Bekommt er keinen Strom, die Seite wie beim Overclocker auf alle stellen.

## Wichtige Hinweise

- **Wax:** Mit Heater gibt die Zentrifuge kein Wax aus, der Heater löscht es (steht so im Quellcode von Modular Bees). Die Gearboxen hängen also komplett am Wax Barrel, und das braucht eine eigene Wax-Quelle. Solange es keine gibt, tun die 6 Gearbox-Nodes nichts und können auch ganz weg.
- **Neue Bienen:** Was die Zentrifuge ausgibt und nicht im K0-Filter von Centr Export steht, bleibt liegen und verstopft sie irgendwann. Bei neuen Comb-Sorten den Filter erweitern.

## Anbindung ans ME-Gebäude

Das ME-System steht im ME-Gebäude. Receiver Barrel und die vier Nachschub-Barrels bleiben in der Technik des Wabenhauses und sind wireless ans ME angebunden.

- Receiver Barrel: ME Import Bus holt die Produkte ins ME.
- Nachschub-Barrels: werden aus dem ME nachgefüllt (Elektroden, Honey Blocks, Glass Bottles, Wax).

## Zweiter Hive, zweite Zentrifuge

Kommen in die Erweiterungszelle, an dieselben relativen Positionen: Hive 2 bei x 6–8, z −12 bis −10, Zentrifuge 2 bei x 17–19, z −12 bis −10.

- Hive-2-Core: K0, K1 und K5 raus, K2 rein (Glass Bottles).
- Zentrifuge 2: Import K1 rein, Export K0 und K5 raus.
- Overclocker, Treater, Gearbox und Heater wie beim ersten Paar.
- K1 hat dann zwei Sender und zwei Empfänger. Die Sender auf Round Robin stellen, damit beide Zentrifugen Combs bekommen.
- Zusätzlich 37 Nodes (16 + 21).

## Stand

- [x] Hive gebaut
- [x] Zentrifuge gebaut
- [x] Anbindung ans ME-Gebäude: wireless, Barrels bleiben in der Technik
- [ ] Wax-Quelle für das Wax Barrel
- [ ] Leistung: K3 abbauen, Takte setzen (K0/K5 40, K2 200 Ticks)
- [ ] Leistung: Strom per Kabel statt K8, dann schläft das Netz
- [ ] Hive 2 und Zentrifuge 2
