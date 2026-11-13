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

# ---------------------------------------------------------------- Maße
N = 171                      # Kantenlänge des Rasters
C = N // 2                   # Mittelpunkt (Index 85)
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
    ("kern", "draconicevolution:energy_core", "Energy Core", "#62e0ff", False, False),
    ("redstone", "minecraft:redstone_block", "Redstone Block", "#a8190f", False, False),
    ("draconium", "draconicevolution:draconium_block", "Draconium Block", "#4b2f7a", False, False),
    ("erwacht", "draconicevolution:awakened_draconium_block", "Awakened Draconium Block", "#f08a24", False, False),
    ("stabilizer", "draconicevolution:energy_core_stabilizer", "Energy Core Stabilizer", "#8a4dff", False, False),
]

V = {}
H = {}                       # Geländehöhe im Park: oberster Grasblock


def setze(x, y, z, m):
    if 0 <= x < N and 0 <= z < N and y >= 0:
        V[(x, y, z)] = m


def loesche(x, y, z):
    V.pop((x, y, z), None)


FELD = []
for _x in range(N):
    for _z in range(N):
        _dx, _dz = _x - C, _z - C
        FELD.append((_x, _z, _dx, _dz, math.hypot(_dx, _dz), math.degrees(math.atan2(_dz, _dx)) % 360))


def im_tor(dx, dz):
    return (abs(dx) <= TOR_HALB) or (abs(dz) <= TOR_HALB)


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


def baue():
    dach = ETAGEN * ETAGE

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
        q = min(abs(dx), abs(dz))
        if q <= TOR_HALB:
            for y in range(1, ETAGE):
                loesche(x, y, z)
            if q == TOR_HALB:
                for y in range(1, ETAGE):
                    setze(x, y, z, "glass")

    # --- Park: Obstbäume, nicht auf Wegen
    rz = zufallszahlen(2024)
    plaetze = []
    for _ in range(900):
        ang = next(rz) % 3600 / 10
        rad = TEICH_R + 6 + (next(rz) % 1000) / 1000 * (R_INNEN - TEICH_R - 15)
        bx = round(C + rad * math.cos(math.radians(ang)))
        bz = round(C + rad * math.sin(math.radians(ang)))
        dx, dz = bx - C, bz - C
        d = math.hypot(dx, dz)
        if weg_abstand(dx, dz, d, math.degrees(math.atan2(dz, dx)) % 360) < 4.5:
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
        bx = round(C + 80.5 * math.cos(ang))
        bz = round(C + 80.5 * math.sin(ang))
        if im_tor(bx - C, bz - C):
            continue
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
    for x in range(C - r, C + r + 1):
        for y in range(KERN_Y - r, KERN_Y + r + 1):
            for z in range(C - r, C + r + 1):
                rr = math.sqrt((x - C) ** 2 + (y - KERN_Y) ** 2 + (z - C) ** 2)
                if rr > KERN_R:
                    continue
                m = "kern" if rr <= 2 else "redstone" if rr <= 3.6 else "draconium" if rr <= 5.1 else "erwacht"
                setze(x, y, z, m)
    for x, z, dx, dz, d, w in FELD:
        if abs(d - STAB_ABSTAND) <= 0.55:
            setze(x, KERN_Y, z, "white")
    for dx, dz in ((STAB_ABSTAND, 0), (-STAB_ABSTAND, 0), (0, STAB_ABSTAND), (0, -STAB_ABSTAND)):
        px, pz = C + dx, C + dz
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                setze(px + ox, 0, pz + oz, "quartz")     # kleine Insel im Teich
        for y in range(1, KERN_Y):
            setze(px, y, pz, "white")
        setze(px, KERN_Y, pz, "stabilizer")


def schreibe(ziel):
    baue()
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
        json.dump([N, hoehe, N], f)
        f.write(',"palette":')
        json.dump(palette, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")
    zaehlung = {}
    for m in V.values():
        zaehlung[m] = zaehlung.get(m, 0) + 1
    print(f"{ziel}: {len(bloecke)} Blöcke, Größe {N} x {hoehe} x {N}")
    for k in benutzt:
        print(f"  {info[k][2]:28} {zaehlung[k]}")


if __name__ == "__main__":
    wurzel = Path(__file__).resolve().parent.parent
    schreibe(wurzel / "gebaeude" / "hauptgebaeude" / "modell.json")
