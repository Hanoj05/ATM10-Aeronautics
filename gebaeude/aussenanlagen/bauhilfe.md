# Bauhilfe Campus-Plan

Erzeugt mit `tools/bauhilfe-campus.py` aus dem Plan im Branch `umgebung-plan`. Das Datapack baut den Plan Block für Block in eurer Welt: planieren, Hohlräume füllen, Wege, Plätze, Becken, Bäume, Blumen und die Lichter an den Gebäuden. Insgesamt 735126 Blöcke in 42 Abschnitten.

## Vorher

1. **Backup der Welt machen.** Das Datapack kann zwar alles zurückbauen, aber Inhalte von Kisten und Maschinen in geänderten Blöcken kommen nicht zurück (es werden nur natürliche Blöcke ersetzt).
2. Die Truhen der Unterwasser-Ruine im Südosten (bei 400–423 / −192 bis −168, Y 48–63) ausräumen, sie werden zugeschüttet.
3. Ihr braucht OP-Rechte (oder Cheats in der Einzelspieler-Kopie zum Testen).

## So geht's

1. `download/campus-bau-datapack.zip` in den Ordner `world/datapacks` vom Server legen (die Zip, nicht entpacken).
2. Im Spiel `/reload`, dann `/datapack list` zeigt `file/campus-bau-datapack.zip`.
3. Erst einen Abschnitt testen: `/function campus:bau/a01`. Er lädt die Chunks selbst, baut und meldet „fertig“.
4. Passt alles: `/function campus:bau_alles` baut alle Abschnitte nacheinander, mit 20 Sekunden Pause dazwischen.
5. Gefällt etwas nicht: `/function campus:zurueck/aNN` für einen Abschnitt oder `/function campus:zurueck_alles`.
6. Danach das Datapack wieder rausnehmen (`/datapack disable "file/campus-bau-datapack.zip"`).

Die Mega Torches stehen nicht im Datapack, die setzt ihr von Hand (je etwa auf Y 64, unter der Oberfläche):

| | X | Z | Versteck |
| --- | --- | --- | --- |
| T1 | 88 | -221 | Mitte Magiehaus, im Keller unter der Kuppel |
| T2 | 158 | -196 | zwischen Magiehaus und Ring, unter der Wiese |
| T3 | 236 | -324 | unter dem ME-Platz |
| T4 | 286 | -196 | im Park, unter einem Beet |
| T5 | 362 | -300 | Nordwest-Ecke im Wabenhaus |

## Abschnitte

| Funktion | x | z | Blöcke |
| --- | --- | --- | --- |
| `campus:bau/a01` | 8 … 71 | -446 … -383 | 49473 |
| `campus:bau/a02` | 72 … 135 | -446 … -383 | 53990 |
| `campus:bau/a03` | 136 … 199 | -446 … -383 | 36852 |
| `campus:bau/a04` | 200 … 263 | -446 … -383 | 16412 |
| `campus:bau/a05` | 264 … 327 | -446 … -383 | 19206 |
| `campus:bau/a06` | 328 … 391 | -446 … -383 | 7453 |
| `campus:bau/a07` | 392 … 455 | -446 … -383 | 12728 |
| `campus:bau/a08` | 8 … 71 | -382 … -319 | 45889 |
| `campus:bau/a09` | 72 … 135 | -382 … -319 | 37720 |
| `campus:bau/a10` | 136 … 199 | -382 … -319 | 15424 |
| `campus:bau/a11` | 200 … 263 | -382 … -319 | 6502 |
| `campus:bau/a12` | 264 … 327 | -382 … -319 | 6134 |
| `campus:bau/a13` | 328 … 391 | -382 … -319 | 28779 |
| `campus:bau/a14` | 392 … 455 | -382 … -319 | 21105 |
| `campus:bau/a15` | 8 … 71 | -318 … -255 | 30808 |
| `campus:bau/a16` | 72 … 135 | -318 … -255 | 19824 |
| `campus:bau/a17` | 136 … 199 | -318 … -255 | 14818 |
| `campus:bau/a18` | 200 … 263 | -318 … -255 | 11688 |
| `campus:bau/a19` | 264 … 327 | -318 … -255 | 7595 |
| `campus:bau/a20` | 328 … 391 | -318 … -255 | 4397 |
| `campus:bau/a21` | 392 … 455 | -318 … -255 | 5791 |
| `campus:bau/a22` | 8 … 71 | -254 … -191 | 19623 |
| `campus:bau/a23` | 72 … 135 | -254 … -191 | 3815 |
| `campus:bau/a24` | 136 … 199 | -254 … -191 | 22434 |
| `campus:bau/a25` | 200 … 263 | -254 … -191 | 6448 |
| `campus:bau/a26` | 264 … 327 | -254 … -191 | 2336 |
| `campus:bau/a27` | 328 … 391 | -254 … -191 | 18047 |
| `campus:bau/a28` | 392 … 455 | -254 … -191 | 13729 |
| `campus:bau/a29` | 8 … 71 | -190 … -127 | 18322 |
| `campus:bau/a30` | 72 … 135 | -190 … -127 | 11937 |
| `campus:bau/a31` | 136 … 199 | -190 … -127 | 19737 |
| `campus:bau/a32` | 200 … 263 | -190 … -127 | 16807 |
| `campus:bau/a33` | 264 … 327 | -190 … -127 | 12362 |
| `campus:bau/a34` | 328 … 391 | -190 … -127 | 53061 |
| `campus:bau/a35` | 392 … 455 | -190 … -127 | 28586 |
| `campus:bau/a36` | 8 … 71 | -126 … -63 | 1551 |
| `campus:bau/a37` | 72 … 135 | -126 … -63 | 2735 |
| `campus:bau/a38` | 136 … 199 | -126 … -63 | 3726 |
| `campus:bau/a39` | 200 … 263 | -126 … -63 | 4836 |
| `campus:bau/a40` | 264 … 327 | -126 … -63 | 9860 |
| `campus:bau/a41` | 328 … 391 | -126 … -63 | 10265 |
| `campus:bau/a42` | 392 … 455 | -126 … -63 | 2321 |

## Geschützte Stellen

Hier steht etwas von euch, das nicht zum Plan gehört. Diese Spalten fasst das Datapack nicht an, dort bleibt es so, wie es ist. Entweder von Hand angleichen oder abbauen und das Skript neu laufen lassen.

| Bereich (x, z, je 8 × 8) | Block | Spalten |
| --- | --- | --- |
| 216, -392 | minecraft:smooth_quartz | 1 |
| 240, -376 | framedblocks:framed_panel | 2 |
| 240, -352 | framedblocks:framed_panel | 1 |
| 240, -344 | framedblocks:framed_panel | 1 |
| 256, -392 | framedblocks:framed_panel | 2 |
| 280, -392 | framedblocks:framed_panel | 1 |
| 288, -392 | framedblocks:framed_panel | 1 |
| 328, -448 | torchmaster:feral_flare_lantern | 1 |
| 344, -320 | minecraft:barrel | 3 |
| 344, -312 | minecraft:barrel | 1 |
| 344, -288 | minecraft:smooth_quartz | 1 |
| 344, -280 | minecraft:light_gray_concrete | 1 |
| 344, -280 | minecraft:smooth_quartz | 5 |
| 344, -272 | minecraft:light_gray_concrete | 1 |
| 344, -272 | minecraft:smooth_quartz | 4 |
| 344, -264 | minecraft:smooth_quartz | 1 |
| 368, -312 | minecraft:quartz_pillar | 1 |
| 384, -448 | torchmaster:feral_flare_lantern | 1 |
| 392, -312 | minecraft:quartz_pillar | 1 |
| 400, -192 | minecraft:sea_lantern | 1 |
| 400, -176 | minecraft:sea_lantern | 1 |
| 408, -176 | minecraft:sea_lantern | 1 |

## Grenzen

- Die Schematic reicht nur bis Y 45. Höhlen tiefer als Y 45 bleiben, wie sie sind.
- Gefüllt wird mit Dirt (die drei Blöcke unter der Oberfläche) und Stone darunter.
- Die Bäume sind einfache Vorlagen mit Blättern, die nicht verwelken (persistent).
