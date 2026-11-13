"""Erzeugt die Außenanlagen des Campus: Wege, Haine, Blumenwiesen, Teiche und Laternen
auf den Flächen zwischen den Gebäuden.

Die Gebäude selbst werden nicht verändert. Das Skript liest ihre Modelle nur, um ihre
Grundflächen (mit 2 Blöcken Abstand) frei zu lassen.

Nutzung:  python3 tools/modell-aussenanlagen.py
Ergebnis: gebaeude/aussenanlagen/modell.json
          gebaeude/aussenanlagen/bauanleitung.json   (liest bauplan.html)

Alles liegt auf Bodenhöhe 65 (y = 0 im Modell). Gebaut wird von Hand, deshalb gibt es
neben der Ebenen-Ansicht Koordinatenlisten für Wege, Laternen, Bäume und Teiche und drei
feste Baum-Vorlagen.
"""
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- Lage (aus den Gebäuden)
RING = (263, -221)               # Mitte Hauptgebäude
RING_GRUND = 84                  # Anlage Hauptgebäude reicht bis hier
TORE = [-31.94 + k * 90 for k in range(4)]   # Torrichtungen vom Ring (Welt: 0 = Ost, 90 = Süd)
MAGIE = (88, -221)               # Mitte Magiehaus
MAGIE_GRUND = 61                 # Anlage Magiehaus reicht bis hier
AUSSEN_R = 128                   # Grüngürtel um den Ring bis hier
MAGIE_GUERTEL = 74               # Grüngürtel um das Magiehaus bis hier
PROMENADE_R = 95                 # Rundweg um den Ring

BLOECKE = [
    ("grass", "minecraft:grass_block", "Grass Block", "#6a9a45", False, False),
    ("quartz", "minecraft:smooth_quartz", "Smooth Quartz", "#ece6df", False, False),
    ("rand", "minecraft:light_gray_concrete", "Light Gray Concrete", "#a9a9a2", False, False),
    ("purpur", "minecraft:purple_concrete", "Purple Concrete", "#64209c", False, False),
    ("white", "minecraft:white_concrete", "White Concrete", "#e4e8e8", False, False),
    ("lantern", "minecraft:sea_lantern", "Sea Lantern", "#c8dcd4", False, False),
    ("amethyst", "minecraft:amethyst_block", "Amethyst Block", "#9a6fd6", False, False),
    ("water", "minecraft:water", "Water", "#3d6fd6", True, False),
    ("lily", "minecraft:lily_pad", "Lily Pad", "#3f8a3a", False, True),
    ("oak_log", "minecraft:oak_log", "Oak Log", "#6b5233", False, False),
    ("oak_leaves", "minecraft:oak_leaves", "Oak Leaves", "#3f7a33", False, False),
    ("birch_log", "minecraft:birch_log", "Birch Log", "#d8d2bf", False, False),
    ("birch_leaves", "minecraft:birch_leaves", "Birch Leaves", "#6e9a4a", False, False),
    ("cherry_log", "minecraft:cherry_log", "Cherry Log", "#3a2430", False, False),
    ("dark_log", "minecraft:dark_oak_log", "Dark Oak Log", "#3c2a1a", False, False),
    ("dark_leaves", "minecraft:dark_oak_leaves", "Dark Oak Leaves", "#2f5e26", False, False),
    ("cherry_leaves", "minecraft:cherry_leaves", "Cherry Leaves", "#e8a8c8", False, False),
    ("arch_log", "ars_nouveau:purple_archwood_log", "Purple Archwood Log", "#5b4a5a", False, False),
    ("l_purple", "ars_nouveau:purple_archwood_leaves", "Purple Archwood Leaves", "#8a4fc4", False, False),
    ("l_blue", "ars_nouveau:blue_archwood_leaves", "Blue Archwood Leaves", "#3f7fd6", False, False),
    ("l_red", "ars_nouveau:red_archwood_leaves", "Red Archwood Leaves", "#c23a3a", False, False),
    ("l_green", "ars_nouveau:green_archwood_leaves", "Green Archwood Leaves", "#4f8a3c", False, False),
    ("allium", "minecraft:allium", "Allium", "#b565e0", False, True),
    ("dandelion", "minecraft:dandelion", "Dandelion", "#f2d43a", False, True),
    ("cornflower", "minecraft:cornflower", "Cornflower", "#4a6fe0", False, True),
    ("poppy", "minecraft:poppy", "Poppy", "#d8322a", False, True),
    ("daisy", "minecraft:oxeye_daisy", "Oxeye Daisy", "#f0f0e0", False, True),
]

# Baum-Vorlagen: feste, von Hand nachbaubare Formen mit Stamm, Ästen, Wurzeln und
# unregelmäßiger Krone. Die Unregelmäßigkeit ist fest (aus den Koordinaten berechnet),
# jeder Baum einer Vorlage sieht also gleich aus.
def _h(ox, y, oz, seed):
    return ((ox * 73856093) ^ (y * 19349663) ^ (oz * 83492791) ^ (seed * 2654435761)) & 0xFFFFFFFF


def _blob(z, cx, cy, cz, rx, ry, rz, seed, loecher=3):
    for ox in range(int(cx - rx) - 1, int(cx + rx) + 2):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for oz in range(int(cz - rz) - 1, int(cz + rz) + 2):
                d = ((ox - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((oz - cz) / rz) ** 2
                if d <= 1 and not (d > 0.72 and _h(ox, y, oz, seed) % loecher == 0):
                    z.setdefault((ox, y, oz), "blatt")


def _vorlage_eiche():
    z = {}
    for y in range(1, 9):
        z[(0, y, 0)] = "holz"
    for c in ((1, 1, 0), (0, 1, -1), (-1, 1, 0)):           # Wurzeln
        z[c] = "holz"
    aeste = (((1, 4, 0), (2, 5, 0), (3, 5, 1)), ((-1, 5, 1), (-2, 6, 1), (-3, 6, 2)),
             ((0, 5, -1), (0, 6, -2), (-1, 6, -3)), ((1, 6, 1), (2, 7, 2)))
    for ast in aeste:
        for c in ast:
            z[c] = "holz"
    _blob(z, 0, 9.0, 0, 3.4, 2.2, 3.4, 1)
    _blob(z, 3.4, 7.0, 1.2, 2.6, 1.7, 2.6, 2)
    _blob(z, -3.2, 7.6, 2.2, 2.6, 1.8, 2.5, 3)
    _blob(z, -0.8, 7.4, -3.4, 2.5, 1.7, 2.6, 4)
    _blob(z, 2.4, 8.4, 2.6, 2.0, 1.6, 2.0, 11)
    return z


def _vorlage_birke():
    z = {}
    for y in range(1, 11):
        z[(0, y, 0)] = "holz"
    z[(1, 6, 0)] = "holz"
    z[(-1, 8, 0)] = "holz"
    _blob(z, 0.8, 6.8, 0.3, 1.9, 1.4, 1.8, 5, loecher=4)
    _blob(z, -0.7, 8.8, -0.2, 1.8, 1.4, 1.8, 6, loecher=4)
    _blob(z, 0.3, 10.8, 0.4, 1.5, 1.4, 1.5, 12, loecher=4)
    _blob(z, 0, 12.2, 0, 0.9, 0.9, 0.9, 13)
    return z


def _vorlage_kirsche():
    z = {}
    for c in ((0, 1, 0), (0, 2, 0), (0, 3, 0), (1, 4, 0), (1, 5, 0), (2, 5, 1), (0, 5, -1)):
        z[c] = "holz"
    _blob(z, 1, 6.6, 0, 4.3, 1.5, 4.1, 7)
    _blob(z, 1, 7.7, 0, 2.5, 1.0, 2.4, 8)
    for (ox, y, oz), t in list(z.items()):                 # hängende Blüten am Rand
        if t == "blatt" and y == 6 and math.hypot(ox - 1, oz) > 3.2 and _h(ox, y, oz, 9) % 3 == 0:
            z.setdefault((ox, 5, oz), "blatt")
    return z


def _vorlage_zauberbaum():
    z = {}
    for c in ((0, 1, 0), (0, 2, 0), (0, 3, 0), (0, 4, 1), (0, 5, 1), (0, 6, 1), (1, 1, 0)):
        z[c] = "holz"
    _blob(z, 0, 7.8, 0.6, 3.1, 2.5, 3.1, 10)
    for k in range(8):                                      # hängende Ranken unter der Krone
        a = k * math.pi / 4 + 0.3
        ox, oz = round(2.8 * math.cos(a)), round(0.6 + 2.8 * math.sin(a))
        for y in (6, 5) if k % 2 == 0 else (6,):
            z.setdefault((ox, y, oz), "blatt")
    return z


def _vorlage_prachtbaum():
    z = {}
    for y in range(1, 10):
        for ox in (0, 1):
            for oz in (0, 1):
                z[(ox, y, oz)] = "holz"
    for c in ((2, 1, 0), (2, 1, 1), (-1, 1, 1), (0, 1, 2), (1, 1, -1), (-1, 2, 1), (2, 2, 0)):   # Wurzeln
        z[c] = "holz"
    aeste = [((2, 6, 0), (3, 7, 0), (4, 8, 0)), ((-1, 7, 1), (-2, 8, 1), (-3, 9, 1)),
             ((1, 6, 2), (1, 7, 3), (1, 8, 4)), ((0, 7, -1), (0, 8, -2), (0, 9, -3))]
    for ast in aeste:
        for c in ast:
            z[c] = "holz"
    for i, (ex, ey, ez) in enumerate(a[-1] for a in aeste):
        _blob(z, ex, ey + 1.6, ez, 3.0, 2.1, 3.0, 20 + i)
    _blob(z, 0.5, 11.2, 0.5, 4.2, 2.6, 4.2, 30)
    return z


VORLAGEN = {
    "E": {"name": "Eiche", "bau": _vorlage_eiche, "radius": 6},
    "B": {"name": "Birke", "bau": _vorlage_birke, "radius": 3},
    "K": {"name": "Kirsche", "bau": _vorlage_kirsche, "radius": 6},
    "Z": {"name": "Zauberbaum", "bau": _vorlage_zauberbaum, "radius": 4},
    "P": {"name": "Prachtbaum", "bau": _vorlage_prachtbaum, "radius": 8},
}
_VORLAGEN_CACHE = {}


def vorlage(k):
    if k not in _VORLAGEN_CACHE:
        _VORLAGEN_CACHE[k] = VORLAGEN[k]["bau"]()
    return _VORLAGEN_CACHE[k]


ARTEN = {
    "Eiche": ("oak_log", "oak_leaves"),
    "Birke": ("birch_log", "birch_leaves"),
    "Kirsche": ("cherry_log", "cherry_leaves"),
    "Dunkle Eiche": ("dark_log", "dark_leaves"),
    "Archwood lila": ("arch_log", "l_purple"),
    "Archwood blau": ("arch_log", "l_blue"),
    "Archwood rot": ("arch_log", "l_red"),
    "Archwood grün": ("arch_log", "l_green"),
}
ELEMENTE = ["Wiese", "Promenade", "Magierweg", "Zuweg", "Laterne", "Baum", "Teich", "Blumen"]

V = {}       # (x, y, z) Welt -> Material
E = {}       # (x, y, z) Welt -> Element


def setze(x, y, z, m, el):
    V[(x, y, z)] = m
    E[(x, y, z)] = el


# ---------------------------------------------------------------- Gebäude-Grundflächen
def belegt_von_gebaeuden():
    campus = json.loads((REPO / "campus" / "campus.json").read_text(encoding="utf-8"))
    belegt = set()
    for g in campus["gebaeude"]:
        if g["id"] == "aussenanlagen":
            continue
        ordner = REPO / g["ordner"]
        geb = json.loads((ordner / "gebaeude.json").read_text(encoding="utf-8"))
        m = json.loads((ordner / "modell.json").read_text(encoding="utf-8"))
        p0, dreh = geb["welt"]["p0"], geb["welt"].get("drehung") or 0
        for b in m["bloecke"]:
            if dreh == 90:
                wx, wz = p0[0] + 1 - b[2], p0[2] + b[0]
            else:
                wx, wz = p0[0] + b[0], p0[2] + b[2]
            belegt.add((wx, wz))
    weit = set()
    for x, z in belegt:
        for ox in range(-2, 3):
            for oz in range(-2, 3):
                weit.add((x + ox, z + oz))
    return weit


# ---------------------------------------------------------------- Wege
def bezier(p0, p1, p2, p3, n=400):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def magierweg_punkte():
    """Geschwungener Weg vom Westsüdwest-Tor des Rings zum Eingang des Magiehauses."""
    w = math.radians(TORE[2])
    start = (RING[0] + RING_GRUND * math.cos(w), RING[1] + RING_GRUND * math.sin(w))
    zum_tor = math.atan2(start[1] - MAGIE[1], start[0] - MAGIE[0])
    ende = (MAGIE[0] + MAGIE_GRUND * math.cos(zum_tor), MAGIE[1] + MAGIE_GRUND * math.sin(zum_tor))
    k = 0.42 * math.hypot(start[0] - ende[0], start[1] - ende[1])
    p1 = (start[0] + k * math.cos(w), start[1] + k * math.sin(w))
    p2 = (ende[0] + k * math.cos(zum_tor), ende[1] + k * math.sin(zum_tor))
    return bezier(start, p1, p2, ende)


def abstand_zur_linie(px, pz, linie, schritt=1):
    best = 1e9
    for i in range(0, len(linie) - 1, schritt):
        x1, z1 = linie[i]
        x2, z2 = linie[i + 1]
        dx, dz = x2 - x1, z2 - z1
        ll = dx * dx + dz * dz or 1e-9
        t = max(0.0, min(1.0, ((px - x1) * dx + (pz - z1) * dz) / ll))
        best = min(best, math.hypot(px - x1 - t * dx, pz - z1 - t * dz))
    return best


def entlang(linie, abstand):
    """Punkte im festen Abstand entlang der Linie, mit Richtung."""
    out = [(linie[0], 0.0)]
    rest = abstand
    for i in range(len(linie) - 1):
        x1, z1 = linie[i]
        x2, z2 = linie[i + 1]
        seg = math.hypot(x2 - x1, z2 - z1)
        richtung = math.atan2(z2 - z1, x2 - x1)
        pos = 0.0
        while seg - pos >= rest:
            pos += rest
            t = pos / seg
            out.append(((x1 + t * (x2 - x1), z1 + t * (z2 - z1)), richtung))
            rest = abstand
        rest -= seg - pos
    return out


# ---------------------------------------------------------------- Baum
def baum_passt(bx, bz, k, frei):
    for (ox, y, oz) in vorlage(k):
        if (bx + ox, bz + oz) not in frei:
            return False
        if (bx + ox, y, bz + oz) in V:
            return False
    return True


def baum(bx, bz, k, art):
    log, blatt = ARTEN[art]
    for (ox, y, oz), t in vorlage(k).items():
        setze(bx + ox, y, bz + oz, log if t == "holz" else blatt, "Baum")


def laterne(x, z, oben="lantern"):
    setze(x, 1, z, "white", "Laterne")
    setze(x, 2, z, "white", "Laterne")
    setze(x, 3, z, oben, "Laterne")


# ---------------------------------------------------------------- Aufbau
def baue():
    belegt = belegt_von_gebaeuden()
    weg_magie = magierweg_punkte()
    rz = 20261113

    def zufall():
        nonlocal rz
        rz = (rz * 1103515245 + 12345) & 0x7FFFFFFF
        return rz

    x0, x1 = MAGIE[0] - MAGIE_GUERTEL - 2, RING[0] + AUSSEN_R + 2
    z0, z1 = RING[1] - AUSSEN_R - 2, RING[1] + AUSSEN_R + 2

    def im_bereich(x, z):
        dr = math.hypot(x - RING[0], z - RING[1])
        dm = math.hypot(x - MAGIE[0], z - MAGIE[1])
        if dr <= RING_GRUND + 0.5 or dm <= MAGIE_GRUND + 0.5:
            return False
        if (x, z) in belegt:
            return False
        return dr <= AUSSEN_R or dm <= MAGIE_GUERTEL or abstand_zur_linie(x, z, weg_magie, 8) <= 14

    frei = {}
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if im_bereich(x, z):
                frei[(x, z)] = abstand_zur_linie(x, z, weg_magie, 4) if abs(z - RING[1]) < 110 and x < RING[0] else 99

    # --- Wiese überall
    for (x, z) in frei:
        setze(x, 0, z, "grass", "Wiese")

    wegzellen = set()
    # --- Magierweg: 5 breit, lila Kante
    for (x, z), d in frei.items():
        if d <= 2.5:
            setze(x, 0, z, "quartz", "Magierweg")
            wegzellen.add((x, z))
        elif d <= 3.5:
            setze(x, 0, z, "purpur", "Magierweg")
            wegzellen.add((x, z))

    # --- Promenade um den Ring: 3 breit, graue Kante
    for (x, z) in frei:
        dr = math.hypot(x - RING[0], z - RING[1])
        if abs(dr - PROMENADE_R) <= 1.5:
            setze(x, 0, z, "quartz", "Promenade")
            wegzellen.add((x, z))
        elif abs(dr - PROMENADE_R) <= 2.5:
            setze(x, 0, z, "rand", "Promenade")
            wegzellen.add((x, z))

    # --- Zuwege von den freien Toren (Süd-Südost und Nord-Nordwest) zur Promenade
    zuwege = []
    for w in (TORE[1], TORE[3]):
        ax, az = math.cos(math.radians(w)), math.sin(math.radians(w))
        for (x, z) in frei:
            l = (x - RING[0]) * ax + (z - RING[1]) * az
            q = -(x - RING[0]) * az + (z - RING[1]) * ax
            if RING_GRUND - 1 <= l <= PROMENADE_R and abs(q) <= 3.5:
                setze(x, 0, z, "quartz" if abs(q) <= 2.5 else "rand", "Zuweg")
                wegzellen.add((x, z))
        zuwege.append({"tor": round(w % 360, 1),
                       "von": [round(RING[0] + RING_GRUND * ax), 65, round(RING[1] + RING_GRUND * az)],
                       "bis": [round(RING[0] + PROMENADE_R * ax), 65, round(RING[1] + PROMENADE_R * az)], "breite": 7})

    def nah_am_weg(x, z, abst):
        for ox in range(-abst, abst + 1):
            for oz in range(-abst, abst + 1):
                if (x + ox, z + oz) in wegzellen:
                    return True
        return False

    def platz_frei(x, z, r):
        for ox in range(-r, r + 1):
            for oz in range(-r, r + 1):
                if (x + ox, z + oz) not in frei:
                    return False
        return True

    laternen, baeume, teiche = [], [], []

    # --- Laternen: Promenade alle 12 Blöcke außen, Magierweg alle 9 Blöcke beidseitig (Amethyst)
    for k in range(int(2 * math.pi * PROMENADE_R / 12)):
        a = k * 12 / PROMENADE_R
        x = round(RING[0] + (PROMENADE_R + 3.5) * math.cos(a))
        z = round(RING[1] + (PROMENADE_R + 3.5) * math.sin(a))
        if (x, z) in frei and (x, z) not in wegzellen:
            laterne(x, z)
            laternen.append({"weg": "Promenade", "x": x, "z": z, "oben": "Sea Lantern"})
    for i, ((px, pz), r) in enumerate(entlang(weg_magie, 9)):
        if i == 0:
            continue
        for s in (-1, 1):
            x = round(px - s * 4.5 * math.sin(r))
            z = round(pz + s * 4.5 * math.cos(r))
            if (x, z) in frei and (x, z) not in wegzellen:
                laterne(x, z, "amethyst")
                laternen.append({"weg": "Magierweg", "x": x, "z": z, "oben": "Amethyst Block"})

    # --- Archwood-Allee am Magierweg: abwechselnd vier Farben, versetzt zu den Laternen
    farben = ["Archwood lila", "Archwood blau", "Archwood rot", "Archwood grün"]
    for i, ((px, pz), r) in enumerate(entlang(weg_magie, 9)):
        if i == 0:
            continue
        for s in (-1, 1):
            for off in (7.5, 9, 10.5):
                x = round(px - s * off * math.sin(r + 0.35))
                z = round(pz + s * off * math.cos(r + 0.35))
                if not nah_am_weg(x, z, 2) and baum_passt(x, z, "Z", frei):
                    art = farben[(i + (s > 0)) % 4]
                    baum(x, z, "Z", art)
                    baeume.append({"vorlage": "Z", "art": art, "x": x, "z": z, "gruppe": "Magierweg"})
                    break

    # --- Teiche: bis zu drei, gleichmäßig verteilt im äußeren Gürtel
    for k in range(24):
        if len(teiche) >= 3:
            break
        a = math.radians(70 + k * 15)
        cx = round(RING[0] + 113 * math.cos(a))
        cz = round(RING[1] + 113 * math.sin(a))
        r = 6
        if not platz_frei(cx, cz, r + 3) or nah_am_weg(cx, cz, r + 3):
            continue
        if any(math.hypot(cx - t["x"], cz - t["z"]) < 60 for t in teiche):
            continue
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r:
                    setze(x, 0, z, "water", "Teich")
                    if zufall() % 9 == 0 and d < r - 1:
                        setze(x, 1, z, "lily", "Teich")
                elif d <= r + 1:
                    setze(x, 0, z, "quartz", "Teich")
        teiche.append({"x": cx, "z": cz, "radius": r, "rand": "Smooth Quartz, 1 breit"})

    def am_teich(x, z, abst):
        return any(math.hypot(x - t["x"], z - t["z"]) <= t["radius"] + abst for t in teiche)

    # --- Wiesen und Haine: ruhige Muster entscheiden, wo offen und wo Wald ist
    def wiese(x, z):
        return math.sin(x * 0.07) + math.cos(z * 0.06) + 0.8 * math.sin((x - z) * 0.045) > 1.1

    def hain(x, z):
        return math.sin(x * 0.05 + 1.3) + math.cos(z * 0.045 + 0.4) + 0.6 * math.sin((x + z) * 0.03) > 0.25

    def birkengruppe(x, z):
        return math.sin(x * 0.11 + 2.0) * math.cos(z * 0.09 + 1.1) > 0.45

    stamm = [(b["x"], b["z"], VORLAGEN[b["vorlage"]]["radius"]) for b in baeume]

    def abstand_ok(x, z, r):
        return all((x - a) ** 2 + (z - b) ** 2 >= (r + rr) ** 2 for a, b, rr in stamm)

    def pflanze(x, z, k, art, gruppe):
        r = VORLAGEN[k]["radius"]
        if not abstand_ok(x, z, r * 0.62) or nah_am_weg(x, z, 3) or am_teich(x, z, 2):
            return False
        if not baum_passt(x, z, k, frei):
            return False
        baum(x, z, k, art)
        stamm.append((x, z, r))
        baeume.append({"vorlage": k, "art": art, "x": x, "z": z, "gruppe": gruppe})
        return True

    # Prachtbäume: wenige große Solitäre auf offenen Wiesen
    pracht = 0
    for (x, z) in sorted(frei.keys(), key=lambda p: (zufall(), p)):
        if pracht >= 6:
            break
        if not wiese(x, z) or nah_am_weg(x, z, 9):
            continue
        if any(math.hypot(x - b["x"], z - b["z"]) < 45 for b in baeume if b["vorlage"] == "P"):
            continue
        if pflanze(x, z, "P", "Dunkle Eiche", "Solitär"):
            pracht += 1

    # Kirschen rund um die Teiche
    for t in teiche:
        for k in range(5):
            a = k * 2 * math.pi / 5 + 0.4
            pflanze(round(t["x"] + 11 * math.cos(a)), round(t["z"] + 11 * math.sin(a)), "K", "Kirsche", "Teich")

    # Haine: Eichen, Birken in Gruppen, am Magiehaus Zauberbäume
    for (x, z) in sorted(frei.keys(), key=lambda p: (zufall(), p)):
        if not hain(x, z) or wiese(x, z):
            continue
        dm = math.hypot(x - MAGIE[0], z - MAGIE[1])
        if dm <= MAGIE_GUERTEL:
            pflanze(x, z, "Z", farben[(x + z) % 4], "Hain")
        elif birkengruppe(x, z):
            pflanze(x, z, "B", "Birke", "Hain")
        else:
            pflanze(x, z, "E", "Eiche", "Hain")

    # Am Rand der Wiesen ab und zu eine Kirsche
    for (x, z) in sorted(frei.keys(), key=lambda p: (zufall(), p)):
        if wiese(x, z) and not wiese(x + 6, z) and zufall() % 6 == 0:
            pflanze(x, z, "K", "Kirsche", "Wiesenrand")

    # --- Blumen zum Schluss, nur wo frei
    blumen = ["allium", "dandelion", "cornflower", "poppy", "daisy"]
    for (x, z) in frei:
        if V.get((x, 0, z)) == "grass" and wiese(x, z) and (x, 1, z) not in V and zufall() % 3 == 0:
            setze(x, 1, z, blumen[(x * 7 + z * 13) % 5], "Blumen")

    return weg_magie, laternen, baeume, teiche, zuwege


def schreibe():
    weg_magie, laternen, baeume, teiche, zuwege = baue()
    minx = min(k[0] for k in V)
    minz = min(k[2] for k in V)
    p0 = [minx, 65, minz]
    reihenfolge = [b[0] for b in BLOECKE]
    benutzt = [k for k in reihenfolge if k in set(V.values())]
    index = {k: i for i, k in enumerate(benutzt)}
    info = {b[0]: b for b in BLOECKE}
    palette = [{"id": info[k][1], "name": info[k][2], "farbe": info[k][3], "transparent": info[k][4], "klein": info[k][5]} for k in benutzt]
    schluessel = sorted(V.keys(), key=lambda k: (k[1], k[2], k[0]))
    bloecke = [[x - minx, y, z - minz, index[V[(x, y, z)]]] for (x, y, z) in schluessel]
    elemente = "".join(str(ELEMENTE.index(E[k])) for k in schluessel)
    groesse = [max(b[0] for b in bloecke) + 1, max(b[1] for b in bloecke) + 1, max(b[2] for b in bloecke) + 1]
    ziel = REPO / "gebaeude" / "aussenanlagen"
    ziel.mkdir(parents=True, exist_ok=True)
    with (ziel / "modell.json").open("w", encoding="utf-8") as f:
        f.write('{"quelle":"tools/modell-aussenanlagen.py","groesse":')
        json.dump(groesse, f)
        f.write(',"palette":')
        json.dump(palette, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")

    menge = {}
    for m in V.values():
        menge[m] = menge.get(m, 0) + 1
    wegpunkte = [[round(px), 65, round(pz)] for (px, pz), _ in entlang(weg_magie, 6)]
    vorlagen = {}
    for k, v in VORLAGEN.items():
        zellen = vorlage(k)
        vorlagen[k] = {"name": v["name"], "radius": v["radius"],
                       "hoehe": max(c[1] for c in zellen),
                       "holz": sum(1 for t in zellen.values() if t == "holz"),
                       "blaetter": sum(1 for t in zellen.values() if t == "blatt"),
                       "lagen": sorted(([c[0], c[1], c[2], "H" if t == "holz" else "B"] for c, t in zellen.items()), key=lambda c: (c[1], c[2], c[0]))}
    daten = {
        "hinweis": "Erzeugt von tools/modell-aussenanlagen.py. Nicht von Hand ändern.",
        "p0": p0,
        "elemente": ELEMENTE,
        "element_je_block": elemente,
        "promenade": {"mitte": [RING[0], 65, RING[1]], "radius": PROMENADE_R, "breite": 3, "kante": "Light Gray Concrete, je 1 breit"},
        "magierweg": {"breite": 5, "kante": "Purple Concrete, je 1 breit", "punkte": wegpunkte},
        "zuwege": zuwege,
        "laternen": laternen,
        "baeume": sorted(baeume, key=lambda b: (b["gruppe"] != "Magierweg", b["x"], b["z"])),
        "teiche": teiche,
        "vorlagen": vorlagen,
        "arten": {k: [info[v[0]][2], info[v[1]][2]] for k, v in ARTEN.items()},
        "material": sorted(({"id": info[k][1], "name": info[k][2], "farbe": info[k][3], "anzahl": menge[k]} for k in benutzt), key=lambda m: -m["anzahl"]),
    }
    (ziel / "bauanleitung.json").write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(bloecke)} Blöcke, Größe {groesse}, P0 {p0}, Bäume {len(baeume)}, Laternen {len(laternen)}, Teiche {len(teiche)}")
    return p0, groesse


if __name__ == "__main__":
    schreibe()
