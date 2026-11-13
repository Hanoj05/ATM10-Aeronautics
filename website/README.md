# Website

Ziel: eine Seite mit 3D-Ansicht vom ganzen Campus. Jedes Gebäude lässt sich anklicken und zeigt dann seine Übersicht aus `gebaeude.json`, `konfig.json` und `konfig.md`.

## Anschauen

Die Seite lädt ihre Daten per `fetch`, deshalb geht sie nicht per Doppelklick als Datei. So startest du sie lokal:

```
cd ATM10-Aeronautics
python3 -m http.server 8000
```

Dann im Browser `http://localhost:8000` öffnen. Die Startseite leitet auf die Campus-Ansicht weiter.

Daten (JSON, Texturen) holt die Seite immer frisch. Die Skripte in `website/js/` sind in den HTML-Dateien mit `?v=<Datum>` eingebunden: nach einer Änderung an einem Skript das Datum in allen `website/*.html` hochzählen, sonst zeigt der Browser noch die alte Version. Im Zweifel hilft Strg+Umschalt+R.

## Seiten

- `index.html` – **Übersicht:** eine Karte pro Gebäude mit Kennzahlen und Sprungmarken.
- `map.html` – **Map:** der Campus in 3D. Hover zeigt den Gebäudenamen, Klick öffnet die Gebäudeseite.
- `technik.html` – **Technik:** ME-System (Zahlen aus dem Blockmodell, Zellen und Anbindungen aus `konfig.json` unter `me`) und alle Logistics Networks, jedes einzeln aufklappbar mit Kanälen, Flüssen und Nodes.
- `roadmap.html` – **Roadmap:** Phasen mit Stand, getrennt nach Minecraft und Website, Filter nach Ort und Status. Daten aus `campus/roadmap.json`.
- `gebaeude.html?id=<id>` – **Gebäude** mit Unter-Tabs:
  - `#ansicht`: 3D-Modell mit Schnitt-Regler. Hover zeigt die Konfiguration eines Teils, Kanäle lassen sich markieren.
  - `#konfig`: Matrix, welches Teil auf welchem Kanal sendet oder empfängt, die Flüsse pro Kanal und darunter `konfig.md`.
  - `#bauplan`: der Bauplan eingebettet.

## Daten pro Gebäude

| Datei | Wofür |
| --- | --- |
| `gebaeude.json` | Steckbrief, Zellen, Dateiliste |
| `modell.json` | Blockmodell. Erzeugt mit `tools/modell-aus-bauplan.py` oder aus einer Schematic mit `tools/modell-aus-schematic.py` |
| `konfig.json` | Teile mit Position (`von`, `bis`), Einstellungen, Nodes und Kanälen. Das liest die Hover-Ansicht |
| `konfig.md` | Lesbare Details, erscheinen im Tab Konfiguration unter der Matrix |

## Texturen

Die 3D-Ansicht zeichnet die Blöcke mit den echten Texturen aus dem Spiel (`texturen/atlas.png`, Zuordnung in `texturen/texturen.json`). Fehlt für einen Block die Textur, bleibt er in seiner Palettenfarbe. Nach neuen Blöcken in einem Modell `tools/hole-texturen.py` laufen lassen, Details in [texturen/README.md](../texturen/README.md).

## Ursprünglicher Plan

- Statische Seite ohne Build-Schritt: eine `index.html` plus ein paar JavaScript-Dateien. Läuft auf jedem Webserver.
- 3D mit three.js. Die Seite liest `campus/campus.json`, platziert jedes Gebäude an seiner Weltkoordinate und lädt dessen Daten.
- Übersicht pro Gebäude: Steckbrief aus `gebaeude.json`, dazu `konfig.md` als formatierte Seite.

## 3D-Modelle in zwei Stufen

1. **Aus den Plandaten:** Jedes Gebäude als vereinfachtes Modell aus `gebaeude.json`, zum Beispiel die Waben des Wabenhauses mit ihren Höhen. Geht sofort, auch für Gebäude, die nur geplant sind.
2. **Aus Schematics:** Sobald ein Gebäude als `.nbt` in `schematics/` liegt, macht `tools/modell-aus-schematic.py` daraus `modell.json`. Das ersetzt das vereinfachte Modell. Erstes Gebäude so: ME-Gebäude.

## Hosting (kostenlos)

| Weg | Gut für | Zu beachten |
| --- | --- | --- |
| Cloudflare Pages | Einfachster Weg. Holt sich das Repo automatisch, auch wenn es privat ist, und baut bei jedem Push neu | Die Seite ist öffentlich erreichbar, außer man schaltet Cloudflare Access davor (kostenlos bis 50 Personen, Login per E-Mail-Code) |
| Eigener Debian-Server | Volle Kontrolle, alles bleibt bei dir | Ein Webserver wie Caddy, dazu `git pull` per Cron. Zugriff von außen über Tailscale, dann müssen die Mitspieler auch Tailscale haben |
| Netlify | Ähnlich wie Cloudflare Pages | Free-Plan hat Limits bei Build-Minuten, für eine statische Seite reicht es |

Entscheidung: _offen_
