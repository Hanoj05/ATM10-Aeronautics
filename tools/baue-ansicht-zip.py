"""Baut die abgespeckte Campus-Ansicht als Zip: nur Map und 3D-Ansicht pro Gebäude.

Nutzung:  python3 tools/baue-ansicht-zip.py
Ergebnis: download/campus-ansicht.zip

Die Zip enthält alles, auch three.js und die Blockmodelle. Entpacken und index.html
per Doppelklick öffnen, kein Webserver und kein Internet nötig. Nach Änderungen an
Gebäuden oder Modellen einfach neu bauen und die Zip mit committen.
"""
import base64
import json
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VORLAGE = REPO / "tools" / "ansicht"
ZIEL = REPO / "download" / "campus-ansicht.zip"
ORDNER = "campus-ansicht/"

LIES_MICH = """Tech-Campus – Ansicht
=====================

index.html per Doppelklick öffnen. Läuft offline im Browser.

- Map: alle Gebäude in 3D. Klick auf ein Gebäude öffnet seine Ansicht.
- Gebäude: das Blockmodell mit Schnitt-Regler. Hover zeigt Blockname und Position.

Erzeugt aus dem Repo mit tools/baue-ansicht-zip.py.
three.js steht unter MIT-Lizenz, siehe vendor/three-LICENSE.txt.
"""


def lies_json(pfad):
    return json.loads(pfad.read_text(encoding="utf-8"))


def daten():
    campus = lies_json(REPO / "campus" / "campus.json")
    liste = []
    for g in campus["gebaeude"]:
        eintrag = {k: g.get(k) for k in ("id", "name", "zweck", "status", "position", "drehung")}
        eintrag["modell"] = None
        if g.get("ordner"):
            ordner = REPO / g["ordner"]
            geb = lies_json(ordner / "gebaeude.json")
            eintrag["masse"] = geb.get("masse")
            datei = (geb.get("dateien") or {}).get("modell", "modell.json")
            if datei and (ordner / datei).exists():
                m = lies_json(ordner / datei)
                eintrag["modell"] = {"palette": m["palette"], "bloecke": m["bloecke"]}
        liste.append(eintrag)
    return {"welt": campus.get("welt"), "gebaeude": liste}


def texturen_js():
    """Blocktexturen für die Offline-Ansicht. Der Atlas kommt als data-URL mit, weil
    WebGL Bilder von file:// nicht benutzen darf. Ohne texturen/ bleibt es bei Farben."""
    ordner = REPO / "texturen"
    if not (ordner / "texturen.json").exists():
        return "/* keine Texturen, siehe tools/hole-texturen.py */\n"
    t = lies_json(ordner / "texturen.json")
    t["atlasDaten"] = "data:image/png;base64," + base64.b64encode((ordner / t["atlas"]).read_bytes()).decode("ascii")
    return "window.CAMPUS_TEXTUREN = " + json.dumps(t, ensure_ascii=False, separators=(",", ":")) + ";\n"


# Feste Zeit für alle Einträge: gleicher Inhalt ergibt Byte für Byte dieselbe Zip,
# sonst zeigt git nach jedem Bauen eine Änderung und Pull klappt nicht mehr.
ZEIT = (2020, 1, 1, 0, 0, 0)


def schreibe(z, name, inhalt):
    info = zipfile.ZipInfo(name, ZEIT)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, inhalt, compresslevel=9)


def main():
    d = daten()
    js = "window.CAMPUS_DATEN = " + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n"
    ZIEL.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIEL, "w") as z:
        for datei in sorted(VORLAGE.rglob("*")):
            if datei.is_file():
                schreibe(z, ORDNER + datei.relative_to(VORLAGE).as_posix(), datei.read_bytes())
        schreibe(z, ORDNER + "voxel.js", (REPO / "website" / "js" / "voxel.js").read_bytes())
        schreibe(z, ORDNER + "daten.js", js)
        schreibe(z, ORDNER + "texturen.js", texturen_js())
        schreibe(z, ORDNER + "LIES-MICH.txt", LIES_MICH)
    mit = [g["name"] for g in d["gebaeude"] if g["modell"]]
    print(f"{ZIEL.relative_to(REPO)}: {ZIEL.stat().st_size // 1024} KB, Gebäude mit Modell: {', '.join(mit)}")


if __name__ == "__main__":
    main()
