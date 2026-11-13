"""Erzeugt das Blockmodell des Hauptgebäudes nach dem Vorbild des Apple Park.

Der Ring ist groß und flach: vier Etagen, rundum Glas, an jeder Decke ein weißes
Vordach, das außen und innen übersteht (die typischen weißen Linien). Oben ein
dünnes weißes Dach mit dunkler Solarfläche. Innen ein Park mit Hügeln, Obstbäumen,
geschwungenen Wegen und einem Teich. Über dem Teich schwebt der Draconic
Evolution Energy Core, eingefasst von einem weißen Ring auf vier Säulen.

Nutzung:  python3 tools/modell-hauptgebaeude.py
Ergebnis: gebaeude/hauptgebaeude/modell.json

Koordinaten: x nach Osten, z nach Süden, y = 0 ist der Boden (Welt-Höhe 65).
"""
import json
import math
from pathlib import Path

# ---------------------------------------------------------------- Lage in der Welt
MITTE = (263, -221)          # Ringmitte (Welt x, z), Boden auf Welt-Höhe 65
FOYER = (348, -274)          # Eingang Wabenhaus (Westseite), dahin führt die Bienenallee
ME_SUED = (272, -333)        # Mitte der Südseite vom ME-Gebäude, dahin führt die Wasserallee
WELT_X = (177, 350)          # Rasterausdehnung in der Welt
WELT_Z = (-334, -135)
NX = WELT_X[1] - WELT_X[0] + 1
NZ = WELT_Z[1] - WELT_Z[0] + 1
P0 = (WELT_X[0], 65, WELT_Z[0])
CX = MITTE[0] - WELT_X[0]    # Ringmitte im Raster
CZ = MITTE[1] - WELT_Z[0]
TOR_WINKEL = math.degrees(math.atan2(FOYER[1] - MITTE[1], FOYER[0] - MITTE[0]))  # ein Tor zeigt aufs Wabenhaus

# ---------------------------------------------------------------- Maße
R_AUSSEN = 74.5              # Glasfassade außen (Durchmesser 149)
R_INNEN = 57.5               # Glasfassade innen (Durchmesser 115), Ring ist 17 breit
VORDACH = 2                  # Überstand der weißen Bänder an jeder Decke
DACH_UEBERSTAND = 3          # Überstand des Dachs
ETAGE = 5                    # Decke zu Decke (4 Blöcke lichte Höhe)
ETAGEN = 4
TOR_HALB = 4                 # Durchgänge N, O, S, W: 9 Blöcke breit, 4 hoch
TEICH_R = 13
KERN_R = 6.5                 # Platzhalter-Kugel für den Energy Core
KERN_Y = 32                  # Kernmitte, schwebt sichtbar über dem Dach (Dach bei 20)
STAB_ABSTAND = 14            # Stabilizer und weißer Ring um den Kern
GRUND_R = 84                 # bis hierhin wird Boden gesetzt

BLOECKE = [
    ("white", "minecraft:white_concrete", "White Concrete", "#e4e8e8", False, False),
    ("glass", "minecraft:glass", "Glass", "#c0d8de", True, False),
    ("quartz", "minecraft:smooth_quartz", "Smooth Quartz", "#ece6df", False, False),
    ("solar", "minecraft:gray_concrete", "Gray Concrete", "#3a3d42", False, False),
    ("platz", "minecraft:light_gray_concrete", "Light Gray Concrete", "#a9a9a2", False, False),
    ("light", "oritech:ceiling_light", "Ceiling Light", "#f4f1e3", False, False),
    ("grass", "minecraft:grass_block", "Grass Block", "#6a9a45", False, False),
    ("water", "minecraft:water", "Water", "#3d6fd6", True, False),
    ("log", "ars_nouveau:green_archwood_log", "Green Archwood Log", "#5b4a35", False, False),
    ("leaves", "ars_nouveau:green_archwood_leaves", "Green Archwood Leaves", "#4f8a3c", False, False),
    ("leaves2", "minecraft:oak_leaves", "Oak Leaves", "#3f7a33", False, False),
    ("flower", "minecraft:allium", "Allium", "#b565e0", False, True),
    ("flower2", "minecraft:dandelion", "Dandelion", "#f2d43a", False, True),
    ("flower3", "minecraft:cornflower", "Cornflower", "#4a6fe0", False, True),
    ("flower4", "minecraft:poppy", "Poppy", "#d8322a", False, True),
    ("kern", "draconicevolution:energy_core", "Energy Core", "#62e0ff", False, False),
    ("redstone", "minecraft:redstone_block", "Redstone Block", "#a8190f", False, False),
    ("draconium", "draconicevolution:draconium_block", "Draconium Block", "#4b2f7a", False, False),
    ("erwacht", "draconicevolution:awakened_draconium_block", "Awakened Draconium Block", "#f08a24", False, False),
    ("stabilizer", "draconicevolution:energy_core_stabilizer", "Energy Core Stabilizer", "#8a4dff", False, False),
]

V = {}
H = {}                       # Geländehöhe im Park: oberster Grasblock


def setze(x, y, z, m):
    if 0 <= x < NX and 0 <= z < NZ and y >= 0:
        V[(x, y, z)] = m


def loesche(x, y, z):
    V.pop((x, y, z), None)


_A = math.radians(TOR_WINKEL)
FELD = []
for _x in range(NX):
    for _z in range(NZ):
        _dx, _dz = _x - CX, _z - CZ
        # u, v: Koordinaten entlang der gedrehten Torachsen
        _u = _dx * math.cos(_A) + _dz * math.sin(_A)
        _v = -_dx * math.sin(_A) + _dz * math.cos(_A)
        FELD.append((_x, _z, _u, _v, math.hypot(_dx, _dz), (math.degrees(math.atan2(_dz, _dx)) - TOR_WINKEL) % 360))


def im_tor(u, v):
    return (abs(u) <= TOR_HALB) or (abs(v) <= TOR_HALB)


def raster(wx, wz):
    return wx - WELT_X[0], wz - WELT_Z[0]


def zufallszahlen(start):
    s = start
    while True:
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        yield s


def baum(bx, bz, stamm, krone, blatt):
    y0 = H.get((bx, bz), 0)
    for y in range(y0 + 1, y0 + stamm + 1):
        setze(bx, y, bz, "log")
    my = y0 + stamm + krone * 0.6
    r = int(krone) + 1
    for x in range(bx - r, bx + r + 1):
        for z in range(bz - r, bz + r + 1):
            for y in range(int(my - krone), int(my + krone) + 1):
                if math.sqrt((x - bx) ** 2 + ((y - my) * 1.25) ** 2 + (z - bz) ** 2) <= krone and (x, y, z) not in V:
                    setze(x, y, z, blatt)


def weg_abstand(dx, dz, d, w):
    """Abstand zum nächsten geschwungenen Weg von den Toren zum Teich."""
    best = 99.0
    for achse in (0, 90, 180, 270):
        rel = math.radians((w - achse + 180) % 360 - 180)
        if math.cos(rel) <= 0:
            continue
        quer = d * math.sin(rel)
        mitte = 4.5 * math.sin(d * 0.16)       # Schwung
        best = min(best, abs(quer - mitte))
    return best


STABILIZER = []


def baue():
    dach = ETAGEN * ETAGE
    for ang in (0, 90, 180, 270):
        a = math.radians(ang) + _A
        STABILIZER.append((round(STAB_ABSTAND * math.cos(a)), round(STAB_ABSTAND * math.sin(a))))

    # --- Gelände: sanfte Hügel im Park
    for x, z, dx, dz, d, w in FELD:
        if d < R_INNEN - VORDACH - 1:
            welle = math.sin(x * 0.11) + math.cos(z * 0.09) + 0.7 * math.sin((x + z) * 0.06)
            rand = min(1.0, max(0.0, (d - TEICH_R - 4) / 8), max(0.0, (R_INNEN - 6 - d) / 6))
            H[(x, z)] = max(0, round((welle + 1.2) * 0.9 * rand))
        else:
            H[(x, z)] = 0

    for x, z, dx, dz, d, w in FELD:
        if d > GRUND_R:
            continue
        h = H[(x, z)]
        if d < TEICH_R:
            setze(x, 0, z, "water")
            continue
        if d < TEICH_R + 1.3:
            setze(x, 0, z, "quartz")
            continue
        if d < R_INNEN:
            for y in range(0, h + 1):
                setze(x, y, z, "grass")
            weg = weg_abstand(dx, dz, d, w) <= 1.3
            rund = TEICH_R + 3 <= d < TEICH_R + 5.2          # Weg um den Teich
            lauf = R_INNEN - 9 <= d < R_INNEN - 7            # Laufrunde innen
            if weg or rund or lauf:
                setze(x, h, z, "quartz")
        elif d <= R_AUSSEN:
            setze(x, 0, z, "quartz")                         # Boden im Gebäude
        elif d <= R_AUSSEN + 7:
            setze(x, 0, z, "platz")                          # Vorplatz
        else:
            setze(x, 0, z, "grass")
        if min(abs(dx), abs(dz)) <= 2 and R_INNEN - 8 <= d <= GRUND_R:
            setze(x, H[(x, z)], z, "quartz")                 # Zufahrt durch den Ring

    # --- Glasfassade außen und innen über alle Etagen
    for x, z, dx, dz, d, w in FELD:
        if R_AUSSEN - 1.3 < d <= R_AUSSEN or R_INNEN <= d < R_INNEN + 1.3:
            for y in range(1, dach):
                setze(x, y, z, "glass")

    # --- Decken mit umlaufendem weißen Vordach (die Linien des Apple Park)
    for e in range(1, ETAGEN):
        y = e * ETAGE
        for x, z, dx, dz, d, w in FELD:
            if R_INNEN - VORDACH <= d <= R_AUSSEN + VORDACH:
                setze(x, y, z, "white")

    # --- Dach: dünne weiße Platte, Solarfläche leicht erhöht in der Mitte
    for x, z, dx, dz, d, w in FELD:
        if R_INNEN - DACH_UEBERSTAND <= d <= R_AUSSEN + DACH_UEBERSTAND:
            setze(x, dach, z, "white")
            if R_INNEN + 1 <= d <= R_AUSSEN - 1:
                fuge = d * math.radians(abs((w + 3.75) % 7.5 - 3.75)) <= 0.5
                setze(x, dach + 1, z, "white" if fuge else "solar")

    # --- Innen: Stützen und Deckenlicht
    mitte = (R_INNEN + R_AUSSEN) / 2
    for x, z, dx, dz, d, w in FELD:
        if abs(d - mitte) <= 0.6 and d * math.radians(abs((w + 3.75) % 7.5 - 3.75)) <= 0.6:
            for y in range(1, dach):
                if (x, y, z) not in V:
                    setze(x, y, z, "white")
    for e in range(ETAGEN):
        y = (e + 1) * ETAGE - 1
        for x, z, dx, dz, d, w in FELD:
            if R_INNEN + 3 < d < R_AUSSEN - 3 and x % 4 == 2 and z % 4 == 2 and (x, y, z) not in V:
                setze(x, y, z, "light")

    # --- Durchgänge durchs Erdgeschoss, seitlich verglast
    for x, z, dx, dz, d, w in FELD:
        if not (R_INNEN - 0.5 <= d <= R_AUSSEN + 0.5):
            continue
        q = min(abs(dx), abs(dz))  # dx, dz sind hier die gedrehten u, v
        if q <= TOR_HALB:
            for y in range(1, ETAGE):
                loesche(x, y, z)
            if q > TOR_HALB - 1:
                for y in range(1, ETAGE):
                    setze(x, y, z, "glass")

    # --- Park: Obstbäume, nicht auf Wegen
    rz = zufallszahlen(2024)
    plaetze = []
    for _ in range(900):
        ang = next(rz) % 3600 / 10
        rad = TEICH_R + 6 + (next(rz) % 1000) / 1000 * (R_INNEN - TEICH_R - 15)
        bx = round(CX + rad * math.cos(math.radians(ang + TOR_WINKEL)))
        bz = round(CZ + rad * math.sin(math.radians(ang + TOR_WINKEL)))
        d = math.hypot(bx - CX, bz - CZ)
        if weg_abstand(0, 0, d, ang % 360) < 4.5:
            continue
        if TEICH_R + 2 <= d < TEICH_R + 7 or R_INNEN - 11 <= d < R_INNEN - 5:
            continue
        if any((bx - px) ** 2 + (bz - pz) ** 2 < 49 for px, pz in plaetze):
            continue
        plaetze.append((bx, bz))
        stamm = 3 + next(rz) % 3
        krone = 2.4 + (next(rz) % 10) / 10
        baum(bx, bz, stamm, krone, "leaves" if next(rz) % 3 else "leaves2")
    # Baumreihe außen um den Ring
    for i in range(48):
        ang = math.radians(i * 7.5 + 3.75)
        if min(abs(80.5 * math.sin(ang)), abs(80.5 * math.cos(ang))) <= TOR_HALB + 2:
            continue
        bx = round(CX + 80.5 * math.cos(ang + _A))
        bz = round(CZ + 80.5 * math.sin(ang + _A))
        baum(bx, bz, 4, 2.6, "leaves2")
    # Wiese mit Blumen
    for x, z, dx, dz, d, w in FELD:
        h = H.get((x, z), 0)
        if TEICH_R + 2 < d < R_INNEN - 3 and V.get((x, h, z)) == "grass" and (x, h + 1, z) not in V:
            n = next(rz)
            if n % 23 == 0:
                setze(x, h + 1, z, "flower" if n % 2 else "flower2")

    # --- Energy Core: Kugel über dem Teich, weißer Ring auf vier Säulen
    r = int(KERN_R) + 1
    for x in range(CX - r, CX + r + 1):
        for y in range(KERN_Y - r, KERN_Y + r + 1):
            for z in range(CZ - r, CZ + r + 1):
                rr = math.sqrt((x - CX) ** 2 + (y - KERN_Y) ** 2 + (z - CZ) ** 2)
                if rr > KERN_R:
                    continue
                m = "kern" if rr <= 2 else "redstone" if rr <= 3.6 else "draconium" if rr <= 5.1 else "erwacht"
                setze(x, y, z, m)
    for x, z, dx, dz, d, w in FELD:
        if abs(d - STAB_ABSTAND) <= 0.55:
            setze(x, KERN_Y, z, "white")
    for dx, dz in STABILIZER:
        px, pz = CX + dx, CZ + dz
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                setze(px + ox, 0, pz + oz, "quartz")     # kleine Insel im Teich
        for y in range(1, KERN_Y):
            setze(px, y, pz, "white")
        setze(px, KERN_Y, pz, "stabilizer")


# ---------------------------------------------------------------- Außenanlagen
def nachbarn():
    """Grundflächen von Wabenhaus und ME-Gebäude in Rasterkoordinaten, um 2 Blöcke erweitert."""
    wurzel = Path(__file__).resolve().parent.parent
    belegt = set()
    for name in ("wabenhaus", "me-zentrale"):
        g = json.loads((wurzel / "gebaeude" / name / "gebaeude.json").read_text(encoding="utf-8"))
        m = json.loads((wurzel / "gebaeude" / name / "modell.json").read_text(encoding="utf-8"))
        p0, dreh = g["welt"]["p0"], g["welt"]["drehung"]
        for b in m["bloecke"]:
            if dreh == 90:
                wx, wz = p0[0] + 1 - b[2], p0[2] + b[0]
            else:
                wx, wz = p0[0] + b[0], p0[2] + b[2]
            gx, gz = raster(wx, wz)
            for ox in range(-2, 3):
                for oz in range(-2, 3):
                    belegt.add((gx + ox, gz + oz))
    return belegt


def allee(ziel, breite_halb):
    """Liefert Zellen entlang einer geraden Linie vom Vorplatz zum Ziel: (x, z, laengs, quer)."""
    zx, zz = raster(*ziel)
    rx, rz = zx - CX, zz - CZ
    laenge = math.hypot(rx, rz)
    ex, ez = rx / laenge, rz / laenge
    start = R_AUSSEN + 6
    zellen = []
    for x in range(NX):
        for z in range(NZ):
            dx, dz = x - CX, z - CZ
            l = dx * ex + dz * ez
            q = -dx * ez + dz * ex
            if start <= l <= laenge and abs(q) <= breite_halb:
                zellen.append((x, z, l - start, q))
    return zellen


def hex_abstand(x, z, hx, hz):
    """Abstand im Sechseck-Maß (Spitzen nach Osten und Westen)."""
    dx, dz = abs(x - hx), abs(z - hz)
    return max(dz / 0.866, (dx + dz / 1.732) / 1.0)


def aussenanlagen():
    belegt = nachbarn()
    rz = zufallszahlen(77)
    blumen = ("flower", "flower2", "flower3", "flower4")

    # Bienenallee zum Wabenhaus: weißer Weg, links und rechts Sechseck-Beete voller Blumen
    beete = []
    for x, z, l, q in allee(FOYER, 12):
        if (x, z) in belegt or math.hypot(x - CX, z - CZ) <= GRUND_R:
            continue
        if abs(q) <= 2.5:
            setze(x, 0, z, "quartz")
        elif abs(q) <= 3.5:
            setze(x, 0, z, "platz")
    for x, z, l, q in allee(FOYER, 12):
        if abs(q) < 3.5 or (x, z) in belegt or math.hypot(x - CX, z - CZ) <= GRUND_R - 1:
            continue
        seite = 1 if q > 0 else -1
        nr = round((l - 4) / 8)
        hl, hq = 4 + nr * 8, seite * 8
        # Beetmitte zurück ins Raster rechnen
        zx, zz = raster(*FOYER)
        ex, ez = (zx - CX), (zz - CZ)
        n = math.hypot(ex, ez); ex, ez = ex / n, ez / n
        ml = R_AUSSEN + 6 + hl
        hx = CX + ex * ml - ez * hq
        hz = CZ + ez * ml + ex * hq
        h = hex_abstand(x, z, hx, hz)
        if h <= 3.2:
            setze(x, 0, z, "grass")
            if next(rz) % 3:
                setze(x, 1, z, blumen[next(rz) % 4])
        elif h <= 4.1:
            setze(x, 0, z, "quartz")
        else:
            setze(x, 0, z, "grass")

    # Wasserallee zum ME-Gebäude: Weg zwischen zwei schmalen Wasserrinnen, außen Baumreihen
    baeume = []
    for x, z, l, q in allee(ME_SUED, 8):
        if (x, z) in belegt or math.hypot(x - CX, z - CZ) <= GRUND_R:
            continue
        a = abs(q)
        if a <= 2.5:
            setze(x, 0, z, "quartz")
        elif a <= 3.5:
            setze(x, 0, z, "water")
        elif a <= 4.5:
            setze(x, 0, z, "quartz")
        else:
            setze(x, 0, z, "grass")
            if 6.5 <= a <= 7.5 and round(l) % 6 == 3:
                baeume.append((x, z))
    gesehen = set()
    for x, z in baeume:
        if any(abs(x - a) + abs(z - b) < 4 for a, b in gesehen):
            continue
        gesehen.add((x, z))
        baum(x, z, 4, 2.4, "leaves2")


def schreibe(ziel):
    baue()
    aussenanlagen()
    reihenfolge = [b[0] for b in BLOECKE]
    benutzt = [k for k in reihenfolge if k in set(V.values())]
    index = {k: i for i, k in enumerate(benutzt)}
    info = {b[0]: b for b in BLOECKE}
    palette = [
        {"id": info[k][1], "name": info[k][2], "farbe": info[k][3], "transparent": info[k][4], "klein": info[k][5]}
        for k in benutzt
    ]
    bloecke = sorted(([x, y, z, index[m]] for (x, y, z), m in V.items()), key=lambda b: (b[1], b[2], b[0]))
    hoehe = max(b[1] for b in bloecke) + 1
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("w", encoding="utf-8") as f:
        f.write('{"quelle":"tools/modell-hauptgebaeude.py","groesse":')
        json.dump([NX, hoehe, NZ], f)
        f.write(',"palette":')
        json.dump(palette, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")
    zaehlung = {}
    for m in V.values():
        zaehlung[m] = zaehlung.get(m, 0) + 1
    print(f"{ziel}: {len(bloecke)} Blöcke, Größe {NX} x {hoehe} x {NZ}, P0 {P0}, Mitte im Raster ({CX}, 0, {CZ}), Torwinkel {TOR_WINKEL:.1f}")
    for k in benutzt:
        print(f"  {info[k][2]:28} {zaehlung[k]}")


if __name__ == "__main__":
    wurzel = Path(__file__).resolve().parent.parent
    schreibe(wurzel / "gebaeude" / "hauptgebaeude" / "modell.json")
