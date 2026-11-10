"""Baut die abgespeckte Campus-Ansicht als Zip: nur Map und 3D-Ansicht pro Gebäude.

Nutzung:  python3 tools/baue-ansicht-zip.py
Ergebnis: download/campus-ansicht.zip

Die Zip enthält alles, auch three.js und die Blockmodelle. Entpacken und index.html
per Doppelklick öffnen, kein Webserver und kein Internet nötig. Nach Änderungen an
Gebäuden oder Modellen einfach neu bauen und die Zip mit committen.
"""
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


def main():
    d = daten()
    js = "window.CAMPUS_DATEN = " + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n"
    ZIEL.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIEL, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for datei in sorted(VORLAGE.rglob("*")):
            if datei.is_file():
                z.write(datei, ORDNER + datei.relative_to(VORLAGE).as_posix())
        z.write(REPO / "website" / "js" / "voxel.js", ORDNER + "voxel.js")
        z.writestr(ORDNER + "daten.js", js)
        z.writestr(ORDNER + "LIES-MICH.txt", LIES_MICH)
    mit = [g["name"] for g in d["gebaeude"] if g["modell"]]
    print(f"{ZIEL.relative_to(REPO)}: {ZIEL.stat().st_size // 1024} KB, Gebäude mit Modell: {', '.join(mit)}")


if __name__ == "__main__":
    main()
