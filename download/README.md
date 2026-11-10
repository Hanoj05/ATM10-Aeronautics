# Download

[campus-ansicht.zip](campus-ansicht.zip) ist eine abgespeckte Campus-Ansicht: nur die Map und pro Gebäude das 3D-Modell mit Schnitt-Regler. Keine Technik, keine Einrichtung, keine Dokumente.

Entpacken und `index.html` per Doppelklick öffnen. Läuft offline, ohne Webserver.

Neu bauen, wenn sich Gebäude oder Modelle geändert haben:

```
python3 tools/baue-ansicht-zip.py
```

Die Seiten dafür liegen in `tools/ansicht/`, der 3D-Teil kommt aus `website/js/voxel.js`.
