# Magiehaus – Plan und Automatisierung

Mitte bei Welt 126, 65, -136. Koordinaten in konfig.json sind relativ zu P0 = Welt 65, 59, -197 (Kellerboden).

Blöcke mit der Kennung `platzhalter:*` im Modell sind keine echten Blöcke. Sie markieren nur, wo eine Maschine, ein Ritual oder ein Raum hinkommt.

## Ebenen

| Ebene | Welt-Höhe | lichte Höhe | Inhalt |
| --- | --- | --- | --- |
| Keller | 59–64 | 5 | P2P-Einspeisung, Kabelwege, Pattern Provider, Tanks, Mobfarm |
| EG | 66–70 | 5 | Werkstätten und Maschinen, Eingangshalle mit Wasserbecken |
| OG | 72–79 | 8 | Ritualsäle, Verzauberungshalle im Atrium |

## Aufzüge (Elevator Mod)

Sechs Aufzugsspalten, jede mit einem Elevator auf Keller-, EG- und OG-Boden (Welt-Höhe 59, 65 und 71). Springen fährt eine Ebene hoch, Schleichen eine runter. Die Aufzüge einer Spalte müssen genau übereinander stehen und brauchen darüber 2 Blöcke Luft, Decken dazwischen stören nicht.

| Spalte | Welt x, z |
| --- | --- |
| Atrium (neben der Treppe) | 113, -133 |
| Flügel Ars Nouveau | 145, -141 |
| Flügel Occultism | 136, -119 |
| Flügel Iron's Spells | 113, -121 |
| Flügel Forbidden & Arcanus | 108, -144 |
| Flügel EvilCraft | 128, -156 |

Die Block-ID `elevatorid:elevator_purple` bitte im JEI mit F3 + H prüfen.

## Platz je Flügel

Jeder Flügel ist bei den Ritualen 29 Blöcke breit, die größte freie Fläche ist 21 × 21. Die Spitzen werden ab etwa 15 Blöcken vor der Spitze schmal und eignen sich für Lager und Deko.

## Ars Nouveau

- **OG:** Ritual Brazier mit Ritualfläche (Ø 11)
- **EG:** Wixie Enchanting Apparatus mit 8 Arcane Pedestals im 3-Block-Radius, daneben Imbuement Chambers
- **Keller:** Pattern Provider, Source Jars, Sourcelinks
- **Automatisierung:** Wixie Charm per Schleichen auf den Apparatus: der Wixie holt die Zutaten aus Kisten in der Nähe. Der Pattern Provider im Keller füllt diese Kiste, das Ergebnis geht per Import Bus zurück ins ME.

## Occultism

- **OG:** Großer Ritualkreis bis 21 × 21 mit Golden Sacrificial Bowl in der Mitte, 8 Blöcke Raumhöhe für Beschwörungen
- **EG:** Spirit Fire, Dimensional Storage, Raum für Crusher-Spirits
- **Keller:** Pattern Provider, Ein- und Ausgabekisten der Spirits
- **Automatisierung:** Rituale bleiben Handarbeit. Crusher-Spirits arbeiten selbst: Pattern Provider füllt die Eingangskiste, Import Bus leert die Ausgabe.

## Iron's Spells 'n Spellbooks

- **OG:** Ausstellung der Spellbooks, Übungsfläche (Ø 15)
- **EG:** Arcane Anvil, Scroll Forge, Inscription Table, Alchemist Cauldrons
- **Keller:** Pattern Provider, Tanks für die Cauldrons
- **Automatisierung:** Cauldrons werden mit Items und Flüssigkeiten beliefert, Schriftrollen bleiben Handarbeit.

## Forbidden & Arcanus

- **OG:** Hephaestus Forge mit 8 Darkstone Pedestals und Enhancern (Ø 13)
- **EG:** Clibano (3 × 3 × 3)
- **Keller:** Pattern Provider für die Clibano, Essenz-Lager
- **Automatisierung:** Forge-Rituale bleiben Handarbeit. Die Clibano läuft über den Pattern Provider. Für Forge-Blut müssen Mobs nahe der Forge sterben: im Spiel prüfen, ob die Mobfarm im Keller nah genug ist, sonst eine Tötungsstelle im OG neben der Forge einplanen.

## EvilCraft

- **OG:** Environmental Accumulator, Ausstellung
- **EG:** Blood Infuser, Purifier, Dark Tanks
- **Keller:** Mobfarm (Spawnfläche 27 × 27, dunkel) mit Tötungskammer und Blood Extractor, Blut-Leitung nach oben
- **Automatisierung:** Pattern Provider schiebt Item und Blut in den Blood Infuser, das Ergebnis geht zurück ins ME. Das Blut kommt aus der Mobfarm direkt darunter.

## Mobfarm

- **Lage:** Keller unter dem EvilCraft-Flügel
- **Aufbau:** Dunkle Spawnfläche, Mobs werden zur Tötungskammer zur Mitte hin geleitet
- **Nutzen:** Blut für EvilCraft (Blood Extractor) und Mob-Drops

## P2P-Einspeisung

- **Aufgabe:** Kein eigener ME Controller. Das Netz kommt aus dem ME-Gebäude per ME P2P Tunnel, hier wird auf die Kabelwege zu den fünf Flügeln verteilt.
- **Kabel:** Sternförmig unter der Kellerdecke zu den Pattern Providern, dazu ein Ring um die Mitte
- **Kanäle:** Jeder Flügel bekommt einen eigenen P2P-Ausgang, damit die 32 Kanäle eines Tunnels nicht knapp werden

## Verzauberungshalle (Apothic Enchanting)

- **Aufbau:** Enchanting Table mit Regalring im OG des Atriums, Bookshelf im Modell als Platzhalter für die Apothic-Regale
- **Bibliothek:** Library of Alexandria daneben
- **Automatisierung:** Verzaubern bleibt Handarbeit
