# Website

Ziel: eine Seite mit 3D-Ansicht vom ganzen Campus. Jedes Gebäude lässt sich anklicken und zeigt dann seine Übersicht aus `gebaeude.json`, `konfig.json` und `konfig.md`.

## Anschauen

Die Seite lädt ihre Daten per `fetch`, deshalb geht sie nicht per Doppelklick als Datei. So startest du sie lokal:

```
cd ATM10-Aeronautics
python3 -m http.server 8000
```

Dann im Browser `http://localhost:8000` öffnen. Die Startseite leitet auf die Campus-Ansicht weiter.

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
