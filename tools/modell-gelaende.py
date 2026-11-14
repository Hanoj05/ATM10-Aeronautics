"""Erzeugt campus/gelaende.json: die Oberfläche der ganzen Schematic für die Map.

Nutzung:  python3 tools/modell-gelaende.py
          python3 tools/modell-gelaende.py --p0 -33 45 -528    Ecke der Schematic von Hand
Braucht:  nur Python 3, keine Zusatzpakete

Pro Spalte (x, z) wird nur der oberste sichtbare Block gespeichert, also eine Höhenkarte
mit Farbe. Die Map zeichnet daraus Oberflächen und Hänge. So bleibt die Datei klein,
auch wenn die Schematic mehrere Millionen Blöcke hat.

Wo ein Gebäude auf der Map steht (Eintrag in campus/campus.json mit Modell und Position,
nicht "karte": false), zählt nur, was unter dem Gebäude liegt. Sonst lägen Gelände und
Gebäudemodell doppelt übereinander. Mit "aussparen": false bleibt das Gelände unter einem
Eintrag stehen, etwa für Außenanlagen, die nur Dinge auf das Gelände stellen.

Die Ecke (0, 0, 0) der Schematic kommt aus gebaeude.json unter ausschnitt.schematicP0
(alle Gebäude mit dieser Schematic müssen dieselbe haben) oder von --p0.
"""
import base64
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
from array import array
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMATIC = "schematics/campus.nbt"
ZIEL = "campus/gelaende.json"

# Farben und unsichtbare Blöcke aus dem Gebäude-Skript übernehmen, damit alles gleich aussieht
sys.dont_write_bytecode = True        # kein __pycache__ im Repo
_spec = importlib.util.spec_from_file_location("modell_aus_schematic", REPO / "tools/modell-aus-schematic.py")
_mas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mas)
FARBEN = dict(_mas.FARBEN)
UNSICHTBAR = set(_mas.UNSICHTBAR)

# Pflanzen ohne Körper: die Spalte zeigt dann den Block darunter
DURCHLAESSIG = ("short_grass", "tall_grass", "grass_sprouts", "fern", "seagrass", "kelp", "vine",
                "bubble_column", "dead_bush", "sugar_cane", "lily_pad", "glow_lichen", "torch",
                "flower", "tulip", "dandelion", "poppy", "orchid", "allium", "bluet", "daisy", "cornflower",
                "lily_of_the_valley", "rose", "peony", "lilac", "sapling", "mushroom", "berry_bush",
                "pebble", "twig", "sprouts", "button", "lever", "rail", "redstone_wire", "snow_layer",
                "carpet", "pressure_plate")

# Gelände-Farben, gesucht als Teil des Namens (die erste passende gewinnt)
GELAENDE = [
    ("water", "#3f6fd0"), ("lava", "#e0601a"), ("ice", "#9cc0f5"), ("snow", "#f3f6f6"),
    ("grass_block", "#5d8f3a"), ("moss", "#5a7a2c"), ("podzol", "#6a4a24"), ("mycelium", "#6f6265"),
    ("leaves", "#3f7a2e"), ("log", "#6b5133"), ("wood", "#6b5133"),
    ("coarse_dirt", "#77553a"), ("rooted_dirt", "#90684d"), ("dirt", "#866043"), ("farmland", "#6b4a2e"),
    ("mud", "#3e3a3c"), ("peat", "#4a3a2c"), ("clay", "#a0a6b3"),
    ("red_sand", "#be6621"), ("sandstone", "#d8cb9b"), ("sand", "#dbcfa3"), ("gravel", "#837e7c"),
    ("deepslate", "#4d4d52"), ("tuff", "#6c6d66"), ("calcite", "#dfe0dc"), ("diorite", "#bcbcbc"),
    ("granite", "#956755"), ("andesite", "#888888"), ("basalt", "#4c4c50"), ("cobble", "#7a7a7a"),
    ("ore", "#7a7a7a"), ("stone", "#7e7e7e"), ("terracotta", "#9a5c43"),
    ("concrete", "#cfd5d6"), ("glass", "#c0d8de"), ("quartz", "#ece6df"), ("planks", "#a2824e"),
]


def farbe_von(name):
    if name in FARBEN:
        return FARBEN[name]
    kurz = name.split(":", 1)[-1]
    for teil, f in GELAENDE:
        if teil in kurz:
            return f
    return _mas.ersatzfarbe(name)


# --- Schematic schnell lesen: nur Größe, Palette und pro Block Position und Zustand ---------

_FEST = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8}


class Leser:
    def __init__(self, daten):
        self.d = daten

    def kurz(self, p):
        return struct.unpack_from(">H", self.d, p)[0]

    def text(self, p):
        n = self.kurz(p)
        return self.d[p + 2:p + 2 + n].decode("utf-8", "replace"), p + 2 + n

    def ueberspringe(self, t, p):
        d = self.d
        if t in _FEST:
            return p + _FEST[t]
        if t == 7:
            return p + 4 + struct.unpack_from(">i", d, p)[0]
        if t == 8:
            return p + 2 + self.kurz(p)
        if t == 11:
            return p + 4 + 4 * struct.unpack_from(">i", d, p)[0]
        if t == 12:
            return p + 4 + 8 * struct.unpack_from(">i", d, p)[0]
        if t == 9:
            et, n = d[p], struct.unpack_from(">i", d, p + 1)[0]
            p += 5
            if et in _FEST:
                return p + max(n, 0) * _FEST[et]
            for _ in range(n):
                p = self.ueberspringe(et, p)
            return p
        if t == 10:
            while True:
                tt = d[p]
                p += 1
                if tt == 0:
                    return p
                p = self.ueberspringe(tt, p + 2 + self.kurz(p))
        raise ValueError("unbekannter NBT-Typ %d" % t)

    def wert(self, t, p):
        d = self.d
        if t in _FEST:
            f = {1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}[t]
            return struct.unpack_from(f, d, p)[0], p + _FEST[t]
        if t == 8:
            return self.text(p)
        if t == 9:
            et, n = d[p], struct.unpack_from(">i", d, p + 1)[0]
            p += 5
            aus = []
            for _ in range(n):
                v, p = self.wert(et, p)
                aus.append(v)
            return aus, p
        if t == 10:
            aus = {}
            while True:
                tt = d[p]
                p += 1
                if tt == 0:
                    return aus, p
                k, p = self.text(p)
                aus[k], p = self.wert(tt, p)
        if t == 11:
            n = struct.unpack_from(">i", d, p)[0]
            return list(struct.unpack_from(">%di" % n, d, p + 4)), p + 4 + 4 * n
        return None, self.ueberspringe(t, p)


def lies_schematic(pfad):
    roh = Path(pfad).read_bytes()
    if roh[:2] == b"\x1f\x8b":
        roh = gzip.decompress(roh)
    L = Leser(roh)
    if roh[0] != 10:
        raise SystemExit("Keine gültige Schematic.")
    _, p = L.text(1)
    groesse, palette = None, None
    xs, ys, zs, st = array("h"), array("h"), array("h"), array("i")
    while True:
        t = roh[p]
        p += 1
        if t == 0:
            break
        name, p = L.text(p)
        if name == "blocks" and t == 9:
            n = struct.unpack_from(">i", roh, p + 1)[0]
            p += 5
            for _ in range(n):
                x = y = z = s = None
                while True:
                    tt = roh[p]
                    p += 1
                    if tt == 0:
                        break
                    ln = L.kurz(p)
                    k = roh[p + 2:p + 2 + ln]
                    p += 2 + ln
                    if k == b"pos" and tt == 9:
                        x, y, z = struct.unpack_from(">iii", roh, p + 5)
                        p += 17
                    elif k == b"state" and tt == 3:
                        s = struct.unpack_from(">i", roh, p)[0]
                        p += 4
                    else:
                        p = L.ueberspringe(tt, p)
                if s is not None and x is not None:
                    xs.append(x); ys.append(y); zs.append(z); st.append(s)
        elif name in ("size", "palette"):
            v, p = L.wert(t, p)
            if name == "size":
                groesse = v
            else:
                palette = v
        elif name == "palettes" and t == 9:
            v, p = L.wert(t, p)
            palette = v[0] if v else None
        else:
            p = L.ueberspringe(t, p)
    if not groesse or palette is None:
        raise SystemExit("In der Schematic fehlen size oder palette.")
    return groesse, palette, xs, ys, zs, st


# --- Gebäude aussparen ---------------------------------------------------------------

def lies_json(pfad):
    return json.loads(Path(pfad).read_text(encoding="utf-8"))


def ecke_aus_gebaeuden(campus):
    ecken = set()
    for g in campus.get("gebaeude", []):
        if not g.get("ordner"):
            continue
        pfad = REPO / g["ordner"] / "gebaeude.json"
        if not pfad.exists():
            continue
        geb = lies_json(pfad)
        aus = geb.get("ausschnitt") or {}
        if (geb.get("dateien") or {}).get("schematic") == SCHEMATIC and aus.get("schematicP0"):
            ecken.add(tuple(aus["schematicP0"]))
    if len(ecken) != 1:
        raise SystemExit("Die Ecke der Schematic ist nicht eindeutig (%s). Bitte mit --p0 x y z angeben." % (sorted(ecken) or "keine"))
    return list(ecken.pop())


def welt_von(p0, drehung, x, y, z):
    """Wie weltVon() in website/js/voxel.js."""
    d = (drehung or 0) % 360
    dx, dz = x, z
    if d == 90:
        dx, dz = -z, x
    elif d == 180:
        dx, dz = -x, -z
    elif d == 270:
        dx, dz = z, -x
    return p0[0] + dx, p0[1] + y, p0[2] + dz


def gebaeude_boxen(campus):
    """[(x0, x1, z0, z1, y_unten)] in Weltkoordinaten für alle Gebäude, die auf der Map stehen."""
    boxen = []
    for g in campus.get("gebaeude", []):
        if not g.get("ordner") or not g.get("position") or g.get("karte") is False or g.get("aussparen") is False:
            continue
        pfad = REPO / g["ordner"] / "modell.json"
        if not pfad.exists():
            continue
        bl = lies_json(pfad).get("bloecke") or []
        if not bl:
            continue
        mn = [min(b[a] for b in bl) for a in range(3)]
        mx = [max(b[a] for b in bl) for a in range(3)]
        ecken = [welt_von(g["position"], g.get("drehung"), x, mn[1], z) for x in (mn[0], mx[0]) for z in (mn[2], mx[2])]
        boxen.append((min(e[0] for e in ecken), max(e[0] for e in ecken),
                      min(e[2] for e in ecken), max(e[2] for e in ecken), ecken[0][1], g["id"]))
    return boxen


# --- Hauptteil -------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    p0 = None
    if args[:1] == ["--p0"]:
        p0 = [int(v) for v in args[1:4]]
    campus = lies_json(REPO / "campus/campus.json")
    if p0 is None:
        p0 = ecke_aus_gebaeuden(campus)
    groesse, palette, xs, ys, zs, st = lies_schematic(REPO / SCHEMATIC)
    nx, ny, nz = groesse
    if ny > 254:
        raise SystemExit("Die Schematic ist höher als 254 Blöcke, das passt nicht ins Format.")

    namen = [b.get("Name", "?") for b in palette]
    zaehlt = [not (n in UNSICHTBAR or any(t in n.split(":", 1)[-1] for t in DURCHLAESSIG)) for n in namen]

    # Pro Spalte die Höhe, bis zu der das Gelände zählt (unter einem Gebäude nur bis darunter)
    grenze = bytearray([255]) * (nx * nz)
    boxen = gebaeude_boxen(campus)
    for x0, x1, z0, z1, yu, gid in boxen:
        lokal = yu - p0[1]
        for x in range(max(0, x0 - p0[0]), min(nx, x1 - p0[0] + 1)):
            for z in range(max(0, z0 - p0[2]), min(nz, z1 - p0[2] + 1)):
                i = x * nz + z
                grenze[i] = max(0, min(grenze[i], lokal))

    hoehe = bytearray(nx * nz)              # 0 = leer, sonst y + 1 (relativ zur Schematic)
    block = array("H", bytes(2 * nx * nz))
    for x, y, z, s in zip(xs, ys, zs, st):
        if not zaehlt[s]:
            continue
        i = x * nz + z
        if y < grenze[i] and y + 1 > hoehe[i]:
            hoehe[i] = y + 1
            block[i] = s

    # Palette nur mit Blöcken, die oben liegen
    neu, index = [], {}
    benutzt = array("H", bytes(2 * nx * nz))
    for i in range(nx * nz):
        if not hoehe[i]:
            continue
        s = block[i]
        if s not in index:
            index[s] = len(neu)
            n = namen[s]
            neu.append({"id": n, "name": _mas.schoener_name(n), "farbe": farbe_von(n)})
        benutzt[i] = index[s]
    if sys.byteorder != "little":
        benutzt.byteswap()

    belegt = sum(1 for h in hoehe if h)
    daten = {
        "quelle": SCHEMATIC,
        "hinweis": "Erzeugt mit tools/modell-gelaende.py. Spalte i = x * groesse[1] + z, Welt = ursprung + (x, z). "
                   "hoehe: ein Byte pro Spalte, 0 = leer, sonst Oberkante über ybasis. block: zwei Byte (little endian) pro Spalte, Index in palette.",
        "ursprung": [p0[0], p0[2]],
        "groesse": [nx, nz],
        "ybasis": p0[1],
        "ausgespart": [b[5] for b in boxen],
        "palette": neu,
        "hoehe": base64.b64encode(bytes(hoehe)).decode("ascii"),
        "block": base64.b64encode(benutzt.tobytes()).decode("ascii"),
    }
    ziel = REPO / ZIEL
    ziel.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("%s: %d × %d Spalten, davon %d belegt, %d Blocksorten oben, Gebäude ausgespart: %s"
          % (ZIEL, nx, nz, belegt, len(neu), ", ".join(daten["ausgespart"]) or "keine"))


if __name__ == "__main__":
    main()
