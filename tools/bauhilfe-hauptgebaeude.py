"""Bauhilfe fürs Hauptgebäude: Create-Schematics in Bauabschnitten plus Daten für den Bauplan.

Nutzung:  python3 tools/bauhilfe-hauptgebaeude.py
Ergebnis: gebaeude/hauptgebaeude/schematics/*.nbt
          gebaeude/hauptgebaeude/bauabschnitte.json  (liest bauplan.html)

Alle Schematics haben denselben Nullpunkt: die Ecke P0 des Hauptgebäudes. Im Spiel
gibt man deshalb bei jedem Abschnitt dieselbe Position ein (siehe bauplan.html).

Das Skript baut das Modell mit tools/modell-hauptgebaeude.py neu auf und teilt die
Blöcke in Abschnitte: acht Achtel vom Ring (mit Vorplatz und Baumreihe), der Park,
die Halterung vom Energy Core und die beiden Alleen. Jede Datei bleibt klein genug
für den Upload-Grenzwert von Create auf Servern.

Die Kugel vom Energy Core kommt NICHT in die Schematics: sie ist im Modell nur ein
Platzhalter. Den echten Core je nach Tier von Hand bauen.

Braucht keine Zusatzpakete.
"""
import gzip
import importlib.util
import json
import math
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZIEL = REPO / "gebaeude" / "hauptgebaeude"
DATA_VERSION = 3955          # Minecraft 1.21.1, wie in schematics/campus.nbt
GRENZE_KB = 256              # Create-Standard für maxTotalSchematicSize auf Servern

spec = importlib.util.spec_from_file_location("gen", REPO / "tools" / "modell-hauptgebaeude.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

PLATZHALTER = {"kern", "redstone", "draconium", "erwacht"}
EIGENSCHAFTEN = {
    "log": {"axis": "y"},
    "leaves": {"persistent": "true", "distance": "7", "waterlogged": "false"},
    "leaves2": {"persistent": "true", "distance": "7", "waterlogged": "false"},
    "water": {"level": "0"},
}
RICHTUNG = ["Ost", "Südost", "Süd", "Südwest", "West", "Nordwest", "Nord", "Nordost"]


# ---------------------------------------------------------------- NBT schreiben
def _s(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _int_liste(werte):
    return struct.pack(">bi", 3, len(werte)) + b"".join(struct.pack(">i", w) for w in werte)


def _compound(eintraege):
    """eintraege: Liste aus (typ, name, rohdaten)."""
    out = b""
    for typ, name, roh in eintraege:
        out += struct.pack(">b", typ) + _s(name) + roh
    return out + b"\x00"


def schematic_bytes(groesse, palette, bloecke):
    pal = []
    for name, props in palette:
        e = [(8, "Name", _s(name))]
        if props:
            e.append((10, "Properties", _compound([(8, k, _s(v)) for k, v in sorted(props.items())])))
        pal.append(_compound(e))
    bl = [_compound([(9, "pos", _int_liste(list(p))), (3, "state", struct.pack(">i", s))]) for p, s in bloecke]
    root = _compound([
        (3, "DataVersion", struct.pack(">i", DATA_VERSION)),
        (9, "size", _int_liste(list(groesse))),
        (9, "palette", struct.pack(">bi", 10, len(pal)) + b"".join(pal)),
        (9, "blocks", struct.pack(">bi", 10, len(bl)) + b"".join(bl)),
        (9, "entities", struct.pack(">bi", 0, 0)),
    ])
    return gzip.compress(b"\x0a" + _s("") + root, compresslevel=9)


# ---------------------------------------------------------------- Abschnitte
def abschnitt_von(x, y, z, m):
    if m in PLATZHALTER:
        return None
    dx, dz = x - gen.CX, z - gen.CZ
    d = math.hypot(dx, dz)
    w = (math.degrees(math.atan2(dz, dx)) - gen.TOR_WINKEL) % 360   # 0 = Tor zum Wabenhaus
    if d <= gen.STAB_ABSTAND + 1.5 and y >= 1 and m in ("white", "stabilizer"):
        return "core"
    if d > gen.GRUND_R + 0.5:
        zu_me = (math.degrees(math.atan2(gen.ME_SUED[1] - gen.MITTE[1], gen.ME_SUED[0] - gen.MITTE[0])) - gen.TOR_WINKEL) % 360
        abw_foyer = min(w, 360 - w)
        abw_me = min(abs(w - zu_me), 360 - abs(w - zu_me))
        return "bienenallee" if abw_foyer < abw_me else "wasserallee"
    if d < gen.R_INNEN - gen.DACH_UEBERSTAND - 0.5:
        return "park"
    return "ring-%d" % (int(((w + 22.5) % 360) // 45) + 1)


def welt_richtung(k):
    """Himmelsrichtung des Achtels k (1..8) in der Welt."""
    w = (gen.TOR_WINKEL + (k - 1) * 45) % 360        # Welt: 0 = Ost, 90 = Süd
    return RICHTUNG[int(((w + 22.5) % 360) // 45)]


def main():
    gen.V.clear()
    gen.H.clear()
    gen.STABILIZER.clear()
    gen.baue()
    gen.aussenanlagen()
    info = {b[0]: b for b in gen.BLOECKE}

    teile = {}
    for (x, y, z), m in gen.V.items():
        a = abschnitt_von(x, y, z, m)
        if a:
            teile.setdefault(a, []).append((x, y, z, m))

    reihenfolge = ["ring-%d" % k for k in range(1, 9)] + ["park", "core", "bienenallee", "wasserallee"]
    titel = {
        "park": ("Park", "Gelände mit Hügeln, Teich mit Inseln, Wege, Bäume und Blumen im Innenhof."),
        "core": ("Energy-Core-Halterung", "Vier weiße Säulen, der weiße Ring und die vier Stabilizer. Die Kugel selbst fehlt: Core je nach Tier von Hand bauen."),
        "bienenallee": ("Bienenallee", "Weg vom Ring zum Foyer des Wabenhauses mit Sechseck-Blumenbeeten."),
        "wasserallee": ("Wasserallee", "Weg zum ME-Gebäude zwischen zwei Wasserrinnen, außen Baumreihen."),
    }
    (ZIEL / "schematics").mkdir(exist_ok=True)
    liste = []
    for nr, a in enumerate(reihenfolge, 1):
        bl = teile.get(a, [])
        if not bl:
            continue
        mn = [min(b[i] for b in bl) for i in range(3)]
        mx = [max(b[i] for b in bl) for i in range(3)]
        groesse = [mx[i] - mn[i] + 1 for i in range(3)]
        # Alle Abschnitte teilen sich denselben Nullpunkt (P0) und denselben Rahmen.
        # So gibt man im Spiel bei jeder Schematic dieselbe Position ein.
        rahmen = [gen.NX, max(b[1] for b in gen.V) + 1, gen.NZ]
        schluessel = sorted({b[3] for b in bl}, key=lambda k: [x[0] for x in gen.BLOECKE].index(k))
        idx = {k: i for i, k in enumerate(schluessel)}
        palette = [(info[k][1], EIGENSCHAFTEN.get(k)) for k in schluessel]
        daten = schematic_bytes(rahmen, palette, [((x, y, z), idx[m]) for x, y, z, m in sorted(bl, key=lambda b: (b[1], b[2], b[0]))])
        datei = "%02d-%s.nbt" % (nr, a)
        (ZIEL / "schematics" / datei).write_bytes(daten)
        kb = len(daten) / 1024
        if kb > GRENZE_KB:
            print(f"WARNUNG: {datei} ist {kb:.0f} KB groß")
        menge = {}
        for b in bl:
            menge[b[3]] = menge.get(b[3], 0) + 1
        if a.startswith("ring-"):
            k = int(a.split("-")[1])
            name = f"Ring {k}/8 ({welt_richtung(k)})"
            text = "Ein Achtel vom Ring über alle Etagen mit Glas, Decken, weißen Bändern, Dach, Vorplatz und Baumreihe." + (" Mit dem Tor zum Wabenhaus." if k == 1 else " Mit einem Tor." if k in (3, 5, 7) else "")
        else:
            name, text = titel[a]
        ecke = [gen.P0[0] + mn[0], gen.P0[1] + mn[1], gen.P0[2] + mn[2]]
        liste.append({
            "nr": nr, "id": a, "name": name, "text": text, "datei": "schematics/" + datei, "kb": round(kb, 1),
            "position": list(gen.P0), "bereichAb": ecke, "bereichPlan": mn, "groesse": groesse, "bloecke": len(bl),
            "material": [{"id": info[k][1], "name": info[k][2], "farbe": info[k][3], "anzahl": menge[k]} for k in schluessel],
        })
        print(f"{datei:24} {len(bl):6} Blöcke  {kb:6.1f} KB  Bereich ab Welt {ecke}  Größe {groesse}")

    gesamt = {}
    for t in liste:
        for m in t["material"]:
            g = gesamt.setdefault(m["id"], dict(m, anzahl=0))
            g["anzahl"] += m["anzahl"]
    daten = {
        "hinweis": "Erzeugt von tools/bauhilfe-hauptgebaeude.py. Nicht von Hand ändern.",
        "p0": list(gen.P0),
        "position": list(gen.P0),
        "rahmen": [gen.NX, max(b[1] for b in gen.V) + 1, gen.NZ],
        "mitte": [gen.MITTE[0], 65, gen.MITTE[1]],
        "mittePlan": [gen.CX, 0, gen.CZ],
        "torWinkel": round(gen.TOR_WINKEL, 2),
        "meWinkel": round(math.degrees(math.atan2(gen.ME_SUED[1] - gen.MITTE[1], gen.ME_SUED[0] - gen.MITTE[0])), 2),
        "grundR": gen.GRUND_R,
        "platzhalter": sorted(info[k][1] for k in PLATZHALTER),
        "radien": {"glasAussen": gen.R_AUSSEN, "glasInnen": gen.R_INNEN, "vordach": gen.VORDACH, "dachUeberstand": gen.DACH_UEBERSTAND, "teich": gen.TEICH_R, "stabilizer": gen.STAB_ABSTAND},
        "etage": gen.ETAGE, "etagen": gen.ETAGEN,
        "core": {"mitte": [gen.MITTE[0], 65 + gen.KERN_Y, gen.MITTE[1]], "stabilizerAbstand": gen.STAB_ABSTAND},
        "abschnitte": liste,
        "material": sorted(gesamt.values(), key=lambda m: -m["anzahl"]),
    }
    (ZIEL / "bauabschnitte.json").write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
