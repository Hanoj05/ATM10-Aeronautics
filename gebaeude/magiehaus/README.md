# Magiehaus

Pentagramm im Pentakel-Kreis, westlich vom Hauptgebäude. Fünf Flügel für Ars Nouveau, Occultism, Iron's Spells, Forbidden & Arcanus und EvilCraft auf drei Ebenen: Keller mit Technik und Mobfarm, Werkstätten im EG, hohe Ritualsäle im OG. Im Atrium die Eingangshalle und darüber die Verzauberungshalle (Apothic Enchanting) unter einer Glaskuppel. Das ME kommt per P2P-Tunnel aus dem ME-Gebäude.

| Datei | Inhalt |
| --- | --- |
| [gebaeude.json](gebaeude.json) | Steckbrief für die Website |
| [modell.json](modell.json) | Blockmodell, erzeugt von [tools/modell-magiehaus.py](../../tools/modell-magiehaus.py) |
| [konfig.json](konfig.json) | Flügel und Bereiche mit Position (für die Hover-Ansicht) |
| [konfig.md](konfig.md) | Plan und Automatisierung zum Lesen |
| [bauplan.html](bauplan.html) | Bauplan: Position, Abschnitte, Ebenen-Ansicht, Material |
| [schematics/](schematics/) | Create-Schematics in 6 Abschnitten mit gemeinsamem Nullpunkt, erzeugt von [tools/bauhilfe-magiehaus.py](../../tools/bauhilfe-magiehaus.py) |
| [bauabschnitte.json](bauabschnitte.json) | Daten für den Bauplan |

Modell neu erzeugen:

```
python3 tools/modell-magiehaus.py
python3 tools/bauhilfe-magiehaus.py
```

Das zweite Skript erzeugt die Schematics und die Bauplan-Daten neu. Platzhalter kommen nicht in die Schematics.
