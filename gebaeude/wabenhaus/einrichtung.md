# Wabenhaus – Einrichtung und Deko

Die einzelnen Einrichtungsteile mit Position und Status stehen in [einrichtung.json](einrichtung.json). Auf der Website siehst du sie im Tab „Einrichtung“ als Liste und in der 3D-Ansicht unter der Ebene „Einrichtung“. Hier stehen nur die Regeln, die fürs ganze Gebäude gelten.

Koordinaten sind Plan-Koordinaten relativ zu P0. Das Gebäude ist gedreht gebaut, in der Welt gilt: **Welt = (392 − z, 65 + y, −286 + x)**. Wo im Plan Süden steht, ist in der Welt Westen.

## Stilregeln

- Hell: Smooth Quartz Block und White Concrete. Dunkle Akzente: Polished Deepslate.
- Signalfarbe nur Honig-Orange (Honeycomb Block, Orange Stained Glass). Keine weiteren bunten Akzente, Pflanzen ausgenommen.
- Metall ist Kupfer, immer gewachst, damit es nicht oxidiert.
- Holz sparsam und hell: Birch oder Stripped Birch für Möbel aus Handcrafted.
- Die Node-Zonen um die Maschinen bleiben leer, auch keine Deko auf dem dunklen Bodenrahmen.

## Mods und wofür

| Mod | Einsatz im Wabenhaus |
| --- | --- |
| Create | Framed Glass und Tiled Glass für die Vitrine, Copper Shingles und Copper Tiles für die Turmkrone |
| Macaw's Doors | Glastüren statt der Waxed Copper Doors in Glaswänden und Vitrine |
| Macaw's Windows | Fensterrahmen und Fensterbänke in den Lamellenfassaden |
| Macaw's Roofs | Dünne dunkle Attika statt der Dachkante aus Polished Deepslate |
| Macaw's Fences and Walls | Geländer im Bienengarten und um den Honigturm |
| Macaw's Bridges | Steg vom Wabenhaus zum ME-Gebäude |
| FramedBlocks | Framed Slab und Framed Panel als Tresenplatten, Sockelleisten, Kabelabdeckung |
| Chipped | Muster-Varianten von Quartz und Concrete für Bodenbänder |
| Handcrafted | Tische, Stühle, Couches, Regale, Bänke |
| Supplementaries | Sign Post als Wegweiser, Notice Board, Item Shelf, Pedestal, Flower Box, Planter |

## Neues Einrichtungsteil eintragen

In `einrichtung.json` unter `teile` einen Eintrag ergänzen:

```json
{ "id": "kurzname", "zelle": "Foyer", "name": "Anzeigename", "mod": "Handcrafted",
  "was": "Was genau hinkommt.",
  "orte": [[[x1, y1, z1], [x2, y2, z2]]], "status": "offen" }
```

`orte` ist eine Liste von Bereichen, jeweils von–bis in Plan-Koordinaten. Ist ein Teil fertig, `status` auf `fertig` setzen.
