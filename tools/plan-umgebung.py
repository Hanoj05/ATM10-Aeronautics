"""Plan für den fertigen Campus: zeigt auf der Map, wie alles aussehen soll.

Nutzung:  python3 tools/plan-umgebung.py
Braucht:  nur Python 3. Läuft etwa eine Minute (liest die Schematic zweimal).

Ausgangspunkt ist der Ist-Stand aus schematics/campus.nbt. Das Skript rechnet daraus neu:
  gebaeude/hauptgebaeude/modell.json   + Lichtkranz auf dem Dach, Wegeleuchten im Park
  gebaeude/magiehaus/modell.json       + violette Leuchtkanten am Stern, Kellerdecke aus
                                         Stufen, begrünte Ecken außerhalb vom Kreis
  gebaeude/aussenanlagen/modell.json   Bäume, Blumen, Mega Torches
  campus/gelaende.json                 Campus planiert auf eine Ebene, Wege, Plätze, Becken

Alle Koordinaten unten sind Weltkoordinaten (x, z), Höhen ebenfalls Welt-y.
Die Feral Flare Lanterns gehören nicht zum Plan, sie sieht man ohnehin nicht.
"""
import base64
import importlib.util
import json
import math
import random
import subprocess
import sys
from array import array
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parent.parent


def modul(name, datei):
    spec = importlib.util.spec_from_file_location(name, REPO / datei)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GEL = modul("modell_gelaende", "tools/modell-gelaende.py")

BODEN_Y = 65                 # Campus-Ebene: Oberkante Wiese, Wege und Plätze (wie die Gebäude)
RING = (263, -221)           # Mitte Hauptgebäude
MAGIE = (88, -221)           # Mitte Magiehaus
AUSSEN_P0 = (14, 65, -347)   # P0 der Außenanlagen (wie bisher)

# Mega Torches (Torchmaster, Reichweite 64 als Würfel): decken alle Gebäude ab
MEGA_TORCHES = [("T1", 88, -221, "Mitte Magiehaus, im Keller unter der Kuppel"),
                ("T2", 158, -196, "zwischen Magiehaus und Ring, unter der Wiese"),
                ("T3", 236, -324, "unter dem ME-Platz"),
                ("T4", 286, -196, "im Park, unter einem Beet"),
                ("T5", 362, -300, "Nordwest-Ecke im Wabenhaus")]

# Campus-Grenze: Rechteck mit runden Ecken. Innen wird alles auf BODEN_Y planiert,
# außen bleibt die Natur. Der alte Bau im Osten (ab x 424) bleibt draußen.
GRENZE = (8, 422, -446, -116, 36)      # x0, x1, z0, z1, Eckradius
RUNDWEG = (1, 5)                       # Rundweg: so weit innerhalb der Grenze (von, bis)

# Wege: Punkte (x, z) und Breite. Alle gleich gebaut: Quarz, grauer Rand, Lichter im Rand.
# Die Tore vom Ring liegen bei 58°, 148°, 238° und 328° (0° = Osten, 90° = Süden), dazu Norden zum ME.
WEGE = [
    ("Magierweg (Tor 148° zum Magiehaus)", [(189, -175), (147, -198)], 7),
    ("Bienenallee (Tor 328° zum Wabenhaus)", [(336, -266), (349, -271)], 5),
    ("Tor 238° zum ME-Platz", [(217, -294), (211, -307)], 5),
    ("Tor 58° zur Südterrasse", [(309, -147), (322, -126)], 5),
    ("Westzugang Magiehaus", [(12, -221), (30, -221)], 5),
    ("Nordweg Magiehaus–ME-Platz", [(88, -282), (88, -305), (206, -305)], 5),
    ("Südweg Magiehaus", [(88, -160), (88, -120)], 5),
    ("Nordachse ME–Landeplatz", [(263, -400), (263, -408)], 7),
    ("Wabenhaus Süd", [(381, -241), (381, -120)], 5),
    ("Wabenhaus Nord", [(381, -304), (381, -330), (330, -330)], 5),
]
ME_PLATZ = (205, 326, -404, -306)      # x0, x1, z0, z1 (Gebäude bleiben ausgespart)
LANDEPLATZ = (263, -420, 12)           # Mitte x, z und Radius
BECKEN = [("Wasserband Südterrasse", 213, 313, -131, -126)]
BIENENWEIDE = (348, 416, -234, -126)   # x0, x1, z0, z1
ALLEE = 10                             # Abstand der Bäume in den Alleen

# Natur, die auf dem Campus-Gelände verschwindet (Magiehaus-Ecken)
NATUR = ("stone", "andesite", "diorite", "granite", "gravel", "dirt", "cobble", "tuff", "deepslate", "kivi",
         "asurine", "limestone", "calcite", "peat", "grass", "water", "sand", "clay", "leaves", "log", "fern",
         "flower", "tulip", "poppy", "dandelion", "bush", "sapling", "ore", "moss", "silt", "mud", "seagrass", "kelp")

FARBE = {
    "minecraft:grass_block": "#5d8f3a", "minecraft:smooth_quartz": "#ece6df",
    "minecraft:light_gray_concrete": "#a9a9a2", "minecraft:white_concrete": "#e4e8e8",
    "minecraft:sea_lantern": "#d6efe6", "minecraft:sand": "#dbcfa3", "minecraft:oak_planks": "#a2824e",
    "minecraft:spruce_planks": "#73553a", "minecraft:gray_concrete": "#36393d",
}

random.seed(14)


def lies(p):
    return json.loads((REPO / p).read_text(encoding="utf-8"))


def schreib_modell(pfad, m):
    with (REPO / pfad).open("w", encoding="utf-8") as f:
        f.write('{"quelle":' + json.dumps(m.get("quelle")) + ',"groesse":' + json.dumps(m["groesse"])
                + ',"zusatz":' + json.dumps(m.get("zusatz") or {}) + ',"palette":')
        json.dump(m["palette"], f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in m["bloecke"]))
        f.write("\n]}\n")


class Modell:
    """Bequemer Zugriff auf ein modell.json: Blöcke nach Position, Sorten nach id."""

    def __init__(self, daten):
        self.d = daten
        self.pal = daten["palette"]
        self.idx = {p["id"]: i for i, p in enumerate(self.pal)}
        self.pos = {}
        for b in daten["bloecke"]:
            self.pos[(b[0], b[1], b[2])] = b

    def sorte(self, sid, name=None, farbe=None, **extra):
        if sid not in self.idx:
            self.idx[sid] = len(self.pal)
            self.pal.append(dict({"id": sid, "name": name or GEL._mas.schoener_name(sid.split("|")[0]),
                                  "farbe": farbe or FARBE.get(sid) or GEL.farbe_von(sid), "transparent": False,
                                  "klein": False}, **extra))
        return self.idx[sid]

    def id_von(self, b):
        return self.pal[b[3]]["id"]

    def setze(self, x, y, z, sid, **kw):
        s = self.sorte(sid, **kw)
        self.pos[(x, y, z)] = [x, y, z, s]

    def weg(self, x, y, z):
        self.pos.pop((x, y, z), None)

    def fertig(self):
        bl = sorted(self.pos.values(), key=lambda b: (b[1], b[2], b[0]))
        self.d["bloecke"] = bl
        xs = [b[0] for b in bl]; ys = [b[1] for b in bl]; zs = [b[2] for b in bl]
        self.d["groesse"] = [max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1]
        return self.d


def oberste(m):
    top = {}
    for (x, y, z), b in m.pos.items():
        if (x, z) not in top or y > top[(x, z)][1]:
            top[(x, z)] = (b, y)
    return top


# --- Hauptgebäude: Lichtkranz und Parkleuchten -----------------------------------------

def plane_hauptgebaeude():
    geb = lies("gebaeude/hauptgebaeude/gebaeude.json")
    p0 = geb["welt"]["p0"]
    m = Modell(lies("gebaeude/hauptgebaeude/modell.json"))
    cx, cz = RING[0] - p0[0], RING[1] - p0[2]
    n_rippe = n_kranz = n_park = 0
    for (x, z), (b, y) in oberste(m).items():
        r = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
        winkel = math.degrees(math.atan2(z + 0.5 - cz, x + 0.5 - cx)) % 360
        sid = m.id_von(b)
        # Rippen-Enden auf dem Dach (weiße Rippen zwischen den grauen Feldern)
        if y == 21 and sid == "minecraft:white_concrete" and (r < 59.5 or r > 71.5):
            m.setze(x, y, z, "minecraft:sea_lantern"); n_rippe += 1
        # Lichtkranz innen und außen auf dem weißen Rand, jeder dritte Block
        elif y == 20 and sid == "minecraft:white_concrete" and (55 <= r < 56 or 75.5 <= r < 76.5):
            if int(winkel * r * math.pi / 180) % 3 == 0:
                m.setze(x, y, z, "minecraft:sea_lantern"); n_kranz += 1
    # Ecken außerhalb der Anlage (Radius 87): alles weg, Campus-Wiese
    weg_ecken = 0
    for (x, y, z) in list(m.pos):
        if math.hypot(x + 0.5 - cx, z + 0.5 - cz) >= 87:
            m.weg(x, y, z); weg_ecken += 1
    print("Hauptgebäude: %d Blöcke in den Ecken außerhalb der Anlage entfernt" % weg_ecken)
    # Park: Laternen am Rand der Quarzwege, etwa alle 7 Blöcke
    top = oberste(m)
    for (x, z), (b, y) in top.items():
        r = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
        if r > 50 or y > 2 or m.id_von(b) != "minecraft:smooth_quartz":
            continue
        rand = any(m.id_von(top[n][0]) == "minecraft:grass_block" for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)) if n in top)
        if rand and (x * 7 + z * 13) % 23 == 0 and (x, y + 1, z) not in m.pos:
            m.setze(x, y + 1, z, "minecraft:lantern", name="Lantern (Wegeleuchte)", farbe="#f2c46a", klein=True); n_park += 1
    schreib_modell("gebaeude/hauptgebaeude/modell.json", m.fertig())
    print("Hauptgebäude: %d Rippen-Enden und %d Kranz-Lichter auf dem Dach, %d Wegeleuchten im Park" % (n_rippe, n_kranz, n_park))


# --- Magiehaus: Leuchtkanten, Kellerdecke, Ecken ---------------------------------------

def plane_magiehaus():
    geb = lies("gebaeude/magiehaus/gebaeude.json")
    p0 = geb["welt"]["p0"]
    m = Modell(lies("gebaeude/magiehaus/modell.json"))
    cx, cz = MAGIE[0] - p0[0], MAGIE[1] - p0[2]
    top = oberste(m)
    # 1. Sternkanten: weiße Dachfläche (y 21), die an eine Nicht-Dach-Spalte grenzt
    dach = {(x, z) for (x, z), (b, y) in top.items() if y == 21 and m.id_von(b) == "minecraft:white_concrete"}
    kanten = 0
    for x, z in dach:
        if any(n not in dach and (n not in top or top[n][1] < 21) for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1))):
            m.setze(x, 21, z, "minecraft:sea_lantern")
            m.setze(x, 22, z, "minecraft:purple_stained_glass", name="Purple Stained Glass (Leuchtkante)",
                    farbe="#9a5ae0", transparent=True)
            kanten += 1
    # 2. Kellerdecke: unter Gras direkt über dem Kellerraum eine obere Stufe
    stufen = 0
    for (x, y, z), b in list(m.pos.items()):
        if y != 6 or m.id_von(b) != "minecraft:grass_block" or (x, 5, z) in m.pos:
            continue
        if any((x, yy, z) in m.pos for yy in (0, 1)):
            m.setze(x, 5, z, "minecraft:smooth_quartz_slab", name="Smooth Quartz Slab (obere Hälfte, neue Kellerdecke)",
                    farbe="#ece6df", form="platte-oben")
            stufen += 1
    # 3. Ecken außerhalb vom Kreis: Wiese auf Bodenhöhe statt kahler Stellen
    ecken = 0
    spalten = {(x, z) for (x, y, z) in m.pos}
    for x, z in spalten:
        if math.hypot(x + 0.5 - cx, z + 0.5 - cz) < 63:
            continue
        for y in [y for y in range(-6, 45) if (x, y, z) in m.pos]:
            m.weg(x, y, z)
        m.setze(x, BODEN_Y - p0[1], z, "minecraft:grass_block")
        ecken += 1
    xs = [x for x, z in spalten]; zs = [z for x, z in spalten]
    for x in range(min(xs), max(xs) + 1):
        for z in range(min(zs), max(zs) + 1):
            if (x, z) not in spalten and math.hypot(x + 0.5 - cx, z + 0.5 - cz) >= 63:
                m.setze(x, BODEN_Y - p0[1], z, "minecraft:grass_block"); ecken += 1
    schreib_modell("gebaeude/magiehaus/modell.json", m.fertig())
    print("Magiehaus: %d Leuchtkanten-Blöcke, %d Stufen als Kellerdecke, %d Spalten Wiese in den Ecken" % (kanten, stufen, ecken))


# --- Gelände ----------------------------------------------------------------------------

class Gelaende:
    def __init__(self):
        self.d = lies("campus/gelaende.json")
        self.nx, self.nz = self.d["groesse"]
        self.ox, self.oz = self.d["ursprung"]
        self.yb = self.d["ybasis"]
        self.h = bytearray(base64.b64decode(self.d["hoehe"]))
        self.b = array("H"); self.b.frombytes(base64.b64decode(self.d["block"]))
        if sys.byteorder != "little":
            self.b.byteswap()
        self.pal = self.d["palette"]
        self.idx = {p["id"]: i for i, p in enumerate(self.pal)}
        self.geschuetzt = set(GEL.gebaeude_spalten(lies("campus/campus.json"))[0])

    def i(self, x, z):
        if not (0 <= x - self.ox < self.nx and 0 <= z - self.oz < self.nz):
            return None
        return (x - self.ox) * self.nz + (z - self.oz)

    def oben(self, x, z):
        i = self.i(x, z)
        if i is None or not self.h[i]:
            return None, None
        return self.yb + self.h[i] - 1, self.pal[self.b[i]]["id"]

    def setze(self, x, z, sid, y=BODEN_Y, frei=False):
        i = self.i(x, z)
        if i is None or (not frei and (x, z) in self.geschuetzt):
            return False
        if sid not in self.idx:
            self.idx[sid] = len(self.pal)
            self.pal.append({"id": sid, "name": GEL._mas.schoener_name(sid), "farbe": FARBE.get(sid) or GEL.farbe_von(sid)})
        self.h[i] = y - self.yb + 1
        self.b[i] = self.idx[sid]
        return True

    def speichern(self):
        b = array("H", self.b)
        if sys.byteorder != "little":
            b.byteswap()
        self.d["hoehe"] = base64.b64encode(bytes(self.h)).decode("ascii")
        self.d["block"] = base64.b64encode(b.tobytes()).decode("ascii")
        self.d["hinweis"] += " Plan: bearbeitet mit tools/plan-umgebung.py."
        (REPO / "campus/gelaende.json").write_text(json.dumps(self.d, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def abstand_zur_strecke(px, pz, a, b):
    ax, az = a; bx, bz = b
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / float(dx * dx + dz * dz or 1)))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz)), t


def weg_spalten(punkte, breite):
    """{(x, z): (abstand zur Mitte, Länge entlang des Wegs)}"""
    aus, laenge = {}, 0.0
    for a, b in zip(punkte, punkte[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        for x in range(min(a[0], b[0]) - breite, max(a[0], b[0]) + breite + 1):
            for z in range(min(a[1], b[1]) - breite, max(a[1], b[1]) + breite + 1):
                d, t = abstand_zur_strecke(x + 0.5, z + 0.5, (a[0] + 0.5, a[1] + 0.5), (b[0] + 0.5, b[1] + 0.5))
                if d <= breite / 2.0 and ((x, z) not in aus or d < aus[(x, z)][0]):
                    aus[(x, z)] = (d, laenge + t * seg)
        laenge += seg
    return aus


def baum(aussen, x, z, y, art="oak", hoehe=5):
    stamm, blatt = {"oak": ("minecraft:oak_log", "minecraft:oak_leaves"),
                    "birch": ("minecraft:birch_log", "minecraft:birch_leaves"),
                    "cherry": ("minecraft:cherry_log", "minecraft:cherry_leaves")}[art]
    for k in range(1, hoehe + 1):
        aussen.welt(x, y + k, z, stamm)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(-1, 2):
                if abs(dx) + abs(dz) + abs(dy) <= 3 and not (dx == 0 and dz == 0 and dy < 1):
                    aussen.welt(x + dx, y + hoehe + dy, z + dz, blatt, nur_frei=True)
    aussen.welt(x, y + hoehe + 2, z, blatt, nur_frei=True)


class Aussen(Modell):
    def welt(self, x, y, z, sid, nur_frei=False, **kw):
        p = (x - AUSSEN_P0[0], y - AUSSEN_P0[1], z - AUSSEN_P0[2])
        if nur_frei and p in self.pos:
            return
        self.setze(p[0], p[1], p[2], sid, **kw)


def in_grenze(x, z, einzug=0):
    x0, x1, z0, z1, r = GRENZE
    x0, x1, z0, z1, r = x0 + einzug, x1 - einzug, z0 + einzug, z1 - einzug, max(1, r - einzug)
    if not (x0 <= x <= x1 and z0 <= z <= z1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cz = min(max(z, z0 + r), z1 - r)
    return math.hypot(x - cx, z - cz) <= r


def plane_aussen_und_gelaende():
    gel = Gelaende()
    aussen = Aussen({"quelle": "tools/plan-umgebung.py", "groesse": [1, 1, 1], "zusatz": {}, "palette": [], "bloecke": []})
    zaehler = {}
    belegt = set()          # Spalten mit Weg, Platz, Becken: dort keine Bäume

    def plus(k, n=1):
        zaehler[k] = zaehler.get(k, 0) + n

    x0, x1, z0, z1, _ = GRENZE
    innen = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if in_grenze(x, z)]

    # 1. Planieren: alles innerhalb der Grenze wird Wiese auf Campus-Höhe
    for x, z in innen:
        gel.setze(x, z, "minecraft:grass_block")
    plus("planiert (Spalten)", len(innen))

    # 2. Grenze: Bordstein, Rundweg mit Lichtern, Baumreihe dahinter
    for x, z in innen:
        if (x, z) in gel.geschuetzt:
            continue
        if not in_grenze(x, z, 1):
            gel.setze(x, z, "minecraft:light_gray_concrete"); belegt.add((x, z))
        elif not in_grenze(x, z, RUNDWEG[1] + 1):
            rand = in_grenze(x, z, RUNDWEG[1]) is False or not in_grenze(x, z, RUNDWEG[0] + 1)
            sid = "minecraft:light_gray_concrete" if rand else "minecraft:smooth_quartz"
            if rand and (x + z) % 9 == 0:
                sid = "minecraft:sea_lantern"
            gel.setze(x, z, sid); belegt.add((x, z))
    plus("Rundweg und Bordstein", len(belegt))

    # 3. ME-Platz: Pflaster mit Raster, Baum-Inseln mit Lichtern
    px0, px1, pz0, pz1 = ME_PLATZ
    platz = [(x, z) for x in range(px0, px1 + 1) for z in range(pz0, pz1 + 1)
             if (x, z) not in gel.geschuetzt and in_grenze(x, z, RUNDWEG[1] + 1)]
    inseln = [(x, z) for x, z in platz if (x - px0 - 10) % 24 == 0 and (z - pz0 - 10) % 24 == 0 and abs(x - 263) > 8
              and all((x + dx, z + dz) not in gel.geschuetzt for dx in range(-6, 7) for dz in range(-6, 7))]
    for x, z in platz:
        if any(math.hypot(x - ix, z - iz) <= 3.2 for ix, iz in inseln):
            gel.setze(x, z, "minecraft:grass_block")
        elif (x - px0) % 12 == 0 or (z - pz0) % 12 == 0:
            gel.setze(x, z, "minecraft:light_gray_concrete")
        else:
            gel.setze(x, z, "minecraft:smooth_quartz")
        belegt.add((x, z))
    for ix, iz in inseln:
        baum(aussen, ix, iz, BODEN_Y, "oak", 5)
        for dx, dz in ((4, 0), (-4, 0), (0, 4), (0, -4)):
            gel.setze(ix + dx, iz + dz, "minecraft:sea_lantern")
    plus("ME-Platz", len(platz)); plus("Baum-Inseln", len(inseln))

    # 4. Landeplatz für Luftschiffe auf der Nordachse
    lx, lz, lr = LANDEPLATZ
    for x in range(lx - lr - 1, lx + lr + 2):
        for z in range(lz - lr - 1, lz + lr + 2):
            r = math.hypot(x - lx, z - lz)
            if r > lr + 0.5:
                continue
            if lr - 1.5 < r and int(math.degrees(math.atan2(z - lz, x - lx)) % 360) % 30 < 8:
                sid = "minecraft:sea_lantern"
            elif lr - 1.5 < r or (abs(x - lx) <= 1 and r < lr - 3) or (abs(z - lz) <= 1 and r < lr - 3):
                sid = "minecraft:white_concrete"
            else:
                sid = "minecraft:gray_concrete"
            gel.setze(x, z, sid); belegt.add((x, z))

    # 5. Wege
    for name, punkte, breite in WEGE:
        n = 0
        for (x, z), (d, s) in weg_spalten(punkte, breite).items():
            if not in_grenze(x, z):
                continue
            rand = d > breite / 2.0 - 1
            sid = ("minecraft:sea_lantern" if int(s) % 8 == 0 else "minecraft:light_gray_concrete") if rand else "minecraft:smooth_quartz"
            if gel.setze(x, z, sid):
                belegt.add((x, z)); n += 1
        plus("Weg " + name, n)

    # 6. Wasserbecken mit Rand aus Quarz und Lichtern
    for name, bx0, bx1, bz0, bz1 in BECKEN:
        for x in range(bx0 - 1, bx1 + 2):
            for z in range(bz0 - 1, bz1 + 2):
                innen_b = bx0 <= x <= bx1 and bz0 <= z <= bz1
                if innen_b:
                    gel.setze(x, z, "minecraft:water", y=BODEN_Y - 1)
                else:
                    gel.setze(x, z, "minecraft:sea_lantern" if (x + z) % 6 == 0 else "minecraft:smooth_quartz")
                belegt.add((x, z))
        plus("Becken " + name, (bx1 - bx0 + 1) * (bz1 - bz0 + 1))

    # 7. Bienenweide südlich vom Wabenhaus: Blumen in Streifen
    blumen = ["minecraft:allium", "minecraft:dandelion", "minecraft:cornflower", "minecraft:poppy",
              "minecraft:oxeye_daisy", "minecraft:azure_bluet", "minecraft:orange_tulip"]
    bx0, bx1, bz0, bz1 = BIENENWEIDE
    nb = 0
    for x in range(bx0, bx1 + 1):
        for z in range(bz0, bz1 + 1):
            if (x, z) in belegt or (x, z) in gel.geschuetzt or not in_grenze(x, z, RUNDWEG[1] + 2):
                continue
            if random.random() < 0.55:
                aussen.welt(x, BODEN_Y + 1, z, blumen[((x - bx0) // 4) % len(blumen)], klein=True); nb += 1
            belegt.add((x, z))
    plus("Blumen Bienenweide", nb)

    # 8. Alleen: Bäume in festem Abstand beidseits der Wege und innen am Rundweg, Wiesen bleiben offen
    def frei(x, z, a):
        return all((x + dx, z + dz) not in belegt and (x + dx, z + dz) not in gel.geschuetzt
                   for dx in range(-a, a + 1) for dz in range(-a, a + 1))
    gesetzt = []

    def pflanze(x, z, art):
        if in_grenze(x, z, RUNDWEG[1] + 3) and frei(x, z, 3) and all(math.hypot(x - a, z - b) >= ALLEE - 1 for a, b in gesetzt):
            baum(aussen, x, z, BODEN_Y, art, 5); gesetzt.append((x, z))

    for name, punkte, breite in WEGE:
        for (ax, az), (bx, bz) in zip(punkte, punkte[1:]):
            lang = math.hypot(bx - ax, bz - az)
            nx_, nz_ = -(bz - az) / lang, (bx - ax) / lang
            for s_ in range(ALLEE // 2, int(lang), ALLEE):
                for seite in (-1, 1):
                    abst = breite / 2.0 + 4
                    pflanze(round(ax + (bx - ax) * s_ / lang + seite * nx_ * abst),
                            round(az + (bz - az) * s_ / lang + seite * nz_ * abst), "birch")
    # am Rundweg entlang: Spalten mit genau dem richtigen Abstand zur Grenze, im Takt
    for x, z in innen:
        if in_grenze(x, z, RUNDWEG[1] + 5) and not in_grenze(x, z, RUNDWEG[1] + 6) and (x + 2 * z) % ALLEE == 0:
            pflanze(x, z, "oak")
    plus("Bäume in Alleen", len(gesetzt))

    # 9. Mega Torches zeigen (werden versteckt eingebaut)
    for name, x, z, wo in MEGA_TORCHES:
        for k in (1, 2):
            aussen.welt(x, BODEN_Y + k, z, "torchmaster:megatorch|" + name,
                        name="Mega Torch %s: %s (später versteckt einbauen)" % (name, wo), farbe="#e8b923", klein=k == 2)

    gel.speichern()
    m = aussen.fertig()
    m["quelle"] = "tools/plan-umgebung.py"
    schreib_modell("gebaeude/aussenanlagen/modell.json", m)
    for k, v in zaehler.items():
        print("  %s: %d" % (k, v))
    print("Außenanlagen: %d Blöcke" % len(m["bloecke"]))


def main():
    # Ist-Stand der beiden Gebäude frisch aus der Schematic
    for g in ("hauptgebaeude", "magiehaus"):
        subprocess.run([sys.executable, "-B", str(REPO / "tools/modell-aus-schematic.py"), str(REPO / "gebaeude" / g)],
                       check=True, stdout=subprocess.DEVNULL)
    plane_hauptgebaeude()
    plane_magiehaus()
    # Gelände aus der Schematic, dann die Planung darauf
    subprocess.run([sys.executable, "-B", str(REPO / "tools/modell-gelaende.py")], check=True, cwd=str(REPO))
    plane_aussen_und_gelaende()


if __name__ == "__main__":
    main()
