# Website

Ziel: eine Seite mit 3D-Ansicht vom ganzen Campus. Jedes Gebäude lässt sich anklicken und zeigt dann seine Übersicht aus `gebaeude.json`, `einrichtung.md` und `konfig.md`.

## Geplanter Aufbau

- Statische Seite ohne Build-Schritt: eine `index.html` plus ein paar JavaScript-Dateien. Läuft auf jedem Webserver.
- 3D mit three.js. Die Seite liest `campus/campus.json`, platziert jedes Gebäude an seiner Weltkoordinate und lädt dessen Daten.
- Übersicht pro Gebäude: Steckbrief aus `gebaeude.json`, dazu `einrichtung.md` und `konfig.md` als formatierte Seiten.

## 3D-Modelle in zwei Stufen

1. **Aus den Plandaten:** Jedes Gebäude als vereinfachtes Modell aus `gebaeude.json`, zum Beispiel die Waben des Wabenhauses mit ihren Höhen. Geht sofort, auch für Gebäude, die nur geplant sind.
2. **Aus Schematics:** Sobald ein Gebäude als `.nbt` in `schematics/` liegt, wird es Block für Block geladen und ersetzt das vereinfachte Modell.

## Hosting (kostenlos)

| Weg | Gut für | Zu beachten |
| --- | --- | --- |
| Cloudflare Pages | Einfachster Weg. Holt sich das Repo automatisch, auch wenn es privat ist, und baut bei jedem Push neu | Die Seite ist öffentlich erreichbar, außer man schaltet Cloudflare Access davor (kostenlos bis 50 Personen, Login per E-Mail-Code) |
| Eigener Debian-Server | Volle Kontrolle, alles bleibt bei dir | Ein Webserver wie Caddy, dazu `git pull` per Cron. Zugriff von außen über Tailscale, dann müssen die Mitspieler auch Tailscale haben |
| Netlify | Ähnlich wie Cloudflare Pages | Free-Plan hat Limits bei Build-Minuten, für eine statische Seite reicht es |

Entscheidung: _offen_
