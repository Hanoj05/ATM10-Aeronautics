# Magiehaus – Plan und Automatisierung

Mitte bei Welt 136, 65, -142. Koordinaten in konfig.json sind relativ zu P0 = Welt 83, 65, -195.

Blöcke mit der Kennung `platzhalter:*` im Modell sind keine echten Blöcke. Sie markieren nur, wo eine Maschine oder ein Ritual hinkommt.

## Aufbau

- **Atrium (Mitte):** unten der ME-Knoten, darüber die Verzauberungshalle mit Apothic Enchanting unter der Glaskuppel, Galerie auf Höhe 18.
- **Fünf Flügel:** unten Technik und Automatisierung, oben ein Ritualsaal mit lila Glas.
- **Eingang:** in der Kerbe, die zum Hauptgebäude zeigt. Eine Allee führt zum Westsüdwest-Tor vom Ring.
- **Außen:** Kreisweg um das Pentagramm (Pentakel), Gärten mit Archwood in vier Farben.

## Ars Nouveau

- **Oben:** Wixie Enchanting Apparatus mit Arcane Pedestals und Arcane Core, Source Jars an Relays
- **Unten:** Imbuement Chambers, Source-Erzeugung (Volcanic/Agronomic Sourcelinks), Pattern Provider
- **Automatisierung:** Wixie Charm per Schleichen auf den Apparatus: der Wixie holt die Zutaten aus Kisten in der Nähe. Ein Pattern Provider füllt eine Kiste neben dem Wixie, ein Import Bus oder Hopper bringt das Ergebnis zurück ins ME.

## Occultism

- **Oben:** Ritualkreis mit Golden Sacrificial Bowl in der Mitte und Sacrificial Bowls ringsum, polierter Boden für die Kreide
- **Unten:** Djinni oder Afrit als Crusher, Spirit Fire, Dimensional Storage
- **Automatisierung:** Rituale bleiben Handarbeit (Occult Engineering ist nicht im Pack). Crusher-Spirits arbeiten selbst: der Pattern Provider füllt ihre Eingangskiste mit Erz, die Ausgabekiste geht per Import Bus zurück ins ME.

## Iron's Spells 'n Spellbooks

- **Oben:** Arcane Anvil, Scroll Forge, Inscription Table, Ausstellung der Spellbooks
- **Unten:** Alchemist Cauldrons für Tinten und Tränke, Pattern Provider
- **Automatisierung:** Cauldrons lassen sich mit Items und Flüssigkeiten beliefern. Schriftrollen und Inschriften bleiben Handarbeit.

## Forbidden & Arcanus

- **Oben:** Hephaestus Forge mit Darkstone Pedestals, genug Platz für die Ausbaustufen
- **Unten:** Clibano, Lager für Essenzen, Pattern Provider
- **Automatisierung:** Die Forge-Rituale bleiben Handarbeit (der mittlere Slot lässt sich ohne Zusatzmod nicht befüllen). Die Clibano läuft automatisch über den Pattern Provider.

## EvilCraft

- **Oben:** Blood Infuser und Purifier
- **Unten:** Dark Tanks, Blood Extractor, Leitung zur Blut-Quelle, Pattern Provider
- **Automatisierung:** Der Blood Infuser ist eine normale Maschine: der Pattern Provider schiebt Item und Blut hinein, das Ergebnis geht zurück ins ME. Blut kommt aus einer Mobfarm mit Blood Extractor, gelagert in Dark Tanks.

## ME-Knoten

- **Aufgabe:** Eigener ME-Controller im Atrium, von hier gehen die Kabel zu den Pattern Providern in jedem Flügel
- **Anbindung:** Quantum Network Bridge oder P2P zum ME-Gebäude, alternativ Kabel unter der Allee und dem Ring

## Verzauberungshalle (Apothic Enchanting)

- **Aufbau:** Enchanting Table mit Regalring, im Modell Bookshelf als Platzhalter für die starken Apothic-Regale
- **Bibliothek:** Library of Alexandria daneben, Bücher per Hopper einwerfen
- **Automatisierung:** Verzaubern bleibt Handarbeit, die Bibliothek ist der Speicher für Verzauberungen

## ME-Anbindung

Jeder Flügel bekommt einen Pattern Provider, der die Maschine oder die Eingangskiste beliefert. Die Ergebnisse gehen per Import Bus oder Interface zurück ins Netz. Der ME-Knoten im Atrium hängt über eine Quantum Network Bridge oder P2P am Hauptnetz im ME-Gebäude.
