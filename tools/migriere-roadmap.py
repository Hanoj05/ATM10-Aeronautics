"""Einmalig: campus/roadmap.json in das Kanban-Board unter kanban/ übernehmen.

Nutzung:  python3 tools/migriere-roadmap.py
Braucht:  nur Python 3

Schreibt kanban/phasen.json, kanban/liste.json und eine Datei pro Karte unter
kanban/karten/ und löscht danach campus/roadmap.json. Bricht ab, wenn es kanban/karten/
schon gibt. Die Reihenfolge in jeder Spalte folgt der alten Roadmap (Phase, dann Punkt).
Zuständig ist erst einmal niemand, das trägt jeder auf dem Board selbst ein.
Bleibt im Repo, damit nachvollziehbar ist, woher die ersten Karten kommen.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUELLE = REPO / "campus" / "roadmap.json"
ZIEL = REPO / "kanban"


def kurzname(titel, vergeben):
    """Lesbare, eindeutige ID aus dem Titel: "ME-Gebäude fertig bauen" -> "me-gebaeude-fertig-bauen"."""
    t = titel.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > 40:
        t = t[:41].rsplit("-", 1)[0]          # an einer Wortgrenze kürzen
    t = t or "karte"
    kid, n = t, 2
    while kid in vergeben:
        kid, n = "%s-%d" % (t, n), n + 1
    vergeben.add(kid)
    return kid


def schreibe(pfad, daten):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if (ZIEL / "karten").exists():
        sys.exit("kanban/karten/ gibt es schon, nichts gemacht.")
    roadmap = json.loads(QUELLE.read_text(encoding="utf-8"))
    phasen, ids, vergeben = [], [], set()
    rang = 0
    for phase in roadmap["phasen"]:
        phasen.append({"id": phase["id"], "titel": phase["titel"], "ziel": phase.get("ziel", "")})
        for punkt in phase["punkte"]:
            rang += 1000
            kid = kurzname(punkt["titel"], vergeben)
            karte = {
                "id": kid,
                "titel": punkt["titel"],
                "beschreibung": punkt.get("text", ""),
                "status": punkt["status"],
                "phase": phase["id"],
                "wo": punkt.get("wo", "Website"),
                "bereich": punkt.get("bereich", "Website"),
                "gebaeude": punkt.get("gebaeude"),
                "tab": punkt.get("tab"),
                "zustaendig": [],
                "faellig": None,
                "rang": rang,
            }
            schreibe(ZIEL / "karten" / (kid + ".json"), karte)
            ids.append(kid)
    schreibe(ZIEL / "phasen.json", phasen)
    (ZIEL / "liste.json").write_text(json.dumps(sorted(ids), ensure_ascii=False) + "\n", encoding="utf-8")
    QUELLE.unlink()
    print("%d Karten in %d Phasen übernommen, campus/roadmap.json gelöscht." % (len(ids), len(phasen)))


if __name__ == "__main__":
    main()
