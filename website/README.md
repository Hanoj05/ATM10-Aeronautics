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
- `team.html` – **Team:** ein Profil pro Person aus `team/`. Das eigene Profil lässt sich bearbeiten (nur angemeldet auf dem Server). Das Passwort ändert man in Authentik.
- `import.html` – **Karte aktualisieren:** neue Campus-Schematic hochladen, Vorschau mit Blöcken dazu/weg pro Gebäude, neuen Blöcken ohne Textur, Gebautem außerhalb aller Gebäude und 3D-Vergleich (vorher, nachher, Unterschied). Pro Gebäude einstellbar, ob das Modell aus der Schematic oder aus dem Entwurfs-Skript kommt. Übernehmen wird ein Commit. Anleitung im Haupt-README unter „Karte aktualisieren“.
- `versionen.html` – **Versionen:** alle Commits mit Autor, Zeit und Bereich. Admins können einen früheren Kartenstand zurückholen (als neuer Commit).
- `admin.html` – **Admin:** Konten anlegen (Authentik-Benutzer mit Profil verbinden), Authentik-Namen ändern, sperren (nur für Admins, also Authentik-Gruppe `campus-admins`).
- `kanban.html` – **Kanban:** Spalten offen, in Arbeit, erledigt. Karten per Drag & Drop verschieben, anklicken zum Bearbeiten. Filter nach Person („Meine Aufgaben“), Gebäude, Bereich, Ort und Phase, auf Wunsch nach Phase gruppiert. Die Filter stehen in der Adresse, ein Link zeigt also genau diese Ansicht. Offene Seiten holen sich Änderungen von anderen alle 20 Sekunden. Daten in `kanban/`, Ändern nur angemeldet auf dem Server. `roadmap.html` leitet hierher weiter.
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

Entscheidung: **eigener Server** (CentOS) mit nginx, davor Nginx Proxy Manager mit Authentik (Single Sign-on). Einrichtung im Haupt-README unter „Server einrichten“.
