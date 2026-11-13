"""Bauhilfe fürs Magiehaus: Create-Schematics in Bauabschnitten plus Daten für den Bauplan.

Nutzung:  python3 tools/bauhilfe-magiehaus.py
Ergebnis: gebaeude/magiehaus/schematics/*.nbt
          gebaeude/magiehaus/bauabschnitte.json   (liest bauplan.html)

Alle Schematics haben denselben Nullpunkt und denselben Rahmen: die Ecke P0 des
Magiehauses (Kellerboden, Nordwest). Im Spiel gibt man deshalb bei jedem Abschnitt
dieselbe Position ein.

Platzhalter (platzhalter:*: Kabelwege, Maschinenplätze, Mobfarm, Treppe) kommen NICHT in
die Schematics. Sie sind nur im Modell und im Bauplan zu sehen. Ausnahme: Platzhalter auf
dem Kellerboden werden zu Polished Deepslate, damit der Boden geschlossen ist.

Liest gebaeude/magiehaus/modell.json, ändert das Modell nicht. Braucht keine Zusatzpakete.
"""
import importlib.util
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZIEL = REPO / "gebaeude" / "magiehaus"


def lade(name, datei):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / datei)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


nbt = lade("bauhilfe_ring", "bauhilfe-hauptgebaeude.py")   # NBT-Schreiber und Grenzwert
geo = lade("magie", "modell-magiehaus.py")                  # Sternform, Höhen

EIGENSCHAFTEN = {
    "ars_nouveau:purple_archwood_log": {"axis": "y"},
    "minecraft:water": {"level": "0"},
}
for _blatt in ("purple", "blue", "red", "green"):
    EIGENSCHAFTEN["ars_nouveau:%s_archwood_leaves" % _blatt] = {"persistent": "true", "distance": "7", "waterlogged": "false"}

ABSCHNITTE = [
    ("keller", "Keller", "Kellerboden, Außenwand aus Deepslate Tiles, Deckenlichter und die Elevator im Keller. Ohne Mobfarm, Kabel und Maschinen: die sind nur Platzhalter."),
    ("boden", "Boden auf Höhe 65", "Die ganze Ebene auf Höhe 65: Erdgeschossboden im Gebäude, Wasserbecken im Atrium, Gras, Kreisweg und Lichtpunkte des Pentakels, Eingang, Weg bis zum Kreis und die Elevator im EG."),
    ("eg", "Erdgeschoss", "Glaswände, Eckstützen, Atriumwand mit Durchgängen und Deckenlichter im EG."),
    ("og", "Obergeschoss", "Decke über dem EG mit Ritualböden, lila Glaswände, Verzauberungstisch mit Regalring, Elevator im OG und Deckenlichter."),
    ("dach", "Dach und Atrium-Turm", "Dachplatte mit den Amethyst-Linien, Atriumwand über dem Dach, Galerie und Glaskuppel."),
    ("gaerten", "Gärten", "Archwood-Bäume, Allium und Lichtsäulen am Weg außerhalb des Gebäudes."),
]


def abschnitt_von(x, y, z, cx, cz):
    px, pz = x - cx, z - cz
    drin = geo.innen(px, pz) or math.hypot(px, pz) <= geo.ATRIUM_R + 1 or geo.randabstand(px, pz) <= 1.0
    if y < geo.G:
        return "keller"
    if y == geo.G:
        return "boden"
    if not drin:
        return "gaerten"
    if y < geo.EG_DECKE:
        return "eg"
    if y < geo.DACH:
        return "og"
    return "dach"


def main():
    m = json.loads((ZIEL / "modell.json").read_text(encoding="utf-8"))
    geb = json.loads((ZIEL / "gebaeude.json").read_text(encoding="utf-8"))
    p0 = geb["welt"]["p0"]
    mitte = geo.MITTE
    cx, cz = mitte[0] - p0[0], mitte[1] - p0[2]
    pal = m["palette"]
    rahmen = m["groesse"]

    # Platzhalter auf dem Kellerboden (Mobfarm, Tötungskammer) werden in der Schematic
    # zu normalem Kellerboden, sonst hätte der Boden dort Löcher
    boden = next(n for n, q in enumerate(pal) if q["id"] == "minecraft:polished_deepslate")
    teile = {a[0]: [] for a in ABSCHNITTE}
    je_block = []
    for b in m["bloecke"]:
        x, y, z, i = b
        if y == 0 and pal[i]["id"].startswith("platzhalter:"):
            b = [x, y, z, boden]
            i = boden
        a = abschnitt_von(x, y, z, cx, cz)
        platz = pal[i]["id"].startswith("platzhalter:")
        je_block.append("p" if platz else a)
        if not platz:
            teile[a].append(b)

    (ZIEL / "schematics").mkdir(exist_ok=True)
    liste = []
    for nr, (aid, name, text) in enumerate(ABSCHNITTE, 1):
        bl = teile[aid]
        if not bl:
            continue
        ids = []
        for b in bl:
            if pal[b[3]]["id"] not in ids:
                ids.append(pal[b[3]]["id"])
        idx = {k: n for n, k in enumerate(ids)}
        palette = [(k, EIGENSCHAFTEN.get(k)) for k in ids]
        daten = nbt.schematic_bytes(rahmen, palette, [((b[0], b[1], b[2]), idx[pal[b[3]]["id"]]) for b in sorted(bl, key=lambda b: (b[1], b[2], b[0]))])
        datei = "%02d-%s.nbt" % (nr, aid)
        (ZIEL / "schematics" / datei).write_bytes(daten)
        kb = len(daten) / 1024
        if kb > nbt.GRENZE_KB:
            print(f"WARNUNG: {datei} ist {kb:.0f} KB groß")
        mn = [min(b[k] for b in bl) for k in range(3)]
        mx = [max(b[k] for b in bl) for k in range(3)]
        menge = {}
        for b in bl:
            menge[b[3]] = menge.get(b[3], 0) + 1
        liste.append({
            "nr": nr, "id": aid, "name": name, "text": text, "datei": "schematics/" + datei, "kb": round(kb, 1),
            "position": p0, "bereichAb": [p0[0] + mn[0], p0[1] + mn[1], p0[2] + mn[2]],
            "groesse": [mx[k] - mn[k] + 1 for k in range(3)], "bloecke": len(bl),
            "material": [{"id": pal[k]["id"], "name": pal[k]["name"], "farbe": pal[k]["farbe"], "anzahl": n} for k, n in sorted(menge.items(), key=lambda t: -t[1])],
        })
        print(f"{datei:20} {len(bl):6} Blöcke  {kb:6.1f} KB")

    gesamt = {}
    for t in liste:
        for mat in t["material"]:
            g = gesamt.setdefault(mat["id"], dict(mat, anzahl=0))
            g["anzahl"] += mat["anzahl"]
    codes = {a[0]: str(n) for n, a in enumerate(ABSCHNITTE)}
    codes["p"] = str(len(ABSCHNITTE))
    daten = {
        "hinweis": "Erzeugt von tools/bauhilfe-magiehaus.py. Nicht von Hand ändern.",
        "p0": p0, "position": p0, "rahmen": rahmen,
        "mitte": [mitte[0], 65, mitte[1]],
        "mittePlan": [cx, geo.G, cz],
        "abschnittNamen": [a[1] for a in ABSCHNITTE] + ["Platzhalter (nicht in den Schematics)"],
        "abschnittIds": [a[0] for a in ABSCHNITTE] + ["platzhalter"],
        "abschnitt_je_block": "".join(codes[a] for a in je_block),
        "abschnitte": liste,
        "material": sorted(gesamt.values(), key=lambda t: -t["anzahl"]),
    }
    (ZIEL / "bauabschnitte.json").write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
