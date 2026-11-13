"""Erzeugt das Blockmodell des Magiehauses: ein Pentagramm im Pentakel-Kreis.

Fünf Flügel (Ars Nouveau, Occultism, EvilCraft, Forbidden & Arcanus, Iron's Spells)
um ein rundes Atrium. Im Atrium unten der ME-Knoten, oben die Verzauberungshalle
(Apothic Enchanting) unter einer Glaskuppel. Jeder Flügel hat unten die
Automatisierung und oben einen Ritualsaal mit lila Glas. Auf dem Dach leuchten die
Mittellinien der Zacken, am Boden schließt ein Kreisweg das Pentagramm zum Pentakel.
Der Eingang liegt in der Kerbe, die zum Hauptgebäude zeigt, eine Allee führt zum Tor.

Blöcke mit der Kennung platzhalter:* markieren nur, wo eine Maschine oder ein Ritual
hinkommt. Sie sind keine echten Blöcke.

Nutzung:  python3 tools/modell-magiehaus.py
Ergebnis: gebaeude/magiehaus/modell.json
"""
import json
import math
from pathlib import Path

# ---------------------------------------------------------------- Lage
RING_MITTE = (263, -221)     # Mitte vom Hauptgebäude
RING_GRUND = 84              # bis hier reicht die Anlage vom Hauptgebäude
TOR_WINKEL = -31.94 + 180    # das Ring-Tor nach Westsüdwest (148°), Welt: 0 = Ost, 90 = Süd
ABSTAND = 150                # Abstand Ringmitte – Magiehausmitte
_t = math.radians(TOR_WINKEL)
MITTE = (round(RING_MITTE[0] + ABSTAND * math.cos(_t)), round(RING_MITTE[1] + ABSTAND * math.sin(_t)))
ZUM_RING = math.degrees(math.atan2(RING_MITTE[1] - MITTE[1], RING_MITTE[0] - MITTE[0]))

# ---------------------------------------------------------------- Maße
R_SPITZE = 44                # Radius der Zackenspitzen
R_KERBE = 23                 # Radius der Innenecken
ETAGE = 6
ETAGEN = 2                   # Flügel: unten Technik, oben Ritualsaal
ATRIUM_R = 13.5
ATRIUM_H = 24                # Atrium-Wand bis hier, darüber die Kuppel
KUPPEL_H = 9
PENTAKEL_R = (47, 49.2)      # Kreisweg um das Pentagramm
GRUND_R = 53
EINGANG_HALB = 3

FLUEGEL = [  # in Uhrzeigerrichtung ab der Zacke rechts vom Eingang
    ("ars", "Ars Nouveau", "#3f8fd6"),
    ("occultism", "Occultism", "#7a3fbf"),
    ("irons", "Iron's Spells 'n Spellbooks", "#d6a33f"),
    ("forbidden", "Forbidden & Arcanus", "#2e2a3a"),
    ("evilcraft", "EvilCraft", "#a3242a"),
]

BLOECKE = [
    ("white", "minecraft:white_concrete", "White Concrete", "#e4e8e8", False, False),
    ("glass", "minecraft:glass", "Glass", "#c0d8de", True, False),
    ("lila", "minecraft:purple_stained_glass", "Purple Stained Glass", "#8a4fc4", True, False),
    ("quartz", "minecraft:smooth_quartz", "Smooth Quartz", "#ece6df", False, False),
    ("deepslate", "minecraft:polished_deepslate", "Polished Deepslate", "#45454d", False, False),
    ("purpur", "minecraft:purple_concrete", "Purple Concrete", "#64209c", False, False),
    ("amethyst", "minecraft:amethyst_block", "Amethyst Block", "#9a6fd6", False, False),
    ("lantern", "minecraft:sea_lantern", "Sea Lantern", "#c8dcd4", False, False),
    ("grass", "minecraft:grass_block", "Grass Block", "#6a9a45", False, False),
    ("water", "minecraft:water", "Water", "#3d6fd6", True, False),
    ("shelf", "minecraft:bookshelf", "Bookshelf", "#8b6a3e", False, False),
    ("table", "minecraft:enchanting_table", "Enchanting Table", "#3a2a5a", False, False),
    ("log", "ars_nouveau:purple_archwood_log", "Purple Archwood Log", "#5b4a5a", False, False),
    ("l_purple", "ars_nouveau:purple_archwood_leaves", "Purple Archwood Leaves", "#8a4fc4", False, False),
    ("l_blue", "ars_nouveau:blue_archwood_leaves", "Blue Archwood Leaves", "#3f7fd6", False, False),
    ("l_red", "ars_nouveau:red_archwood_leaves", "Red Archwood Leaves", "#c23a3a", False, False),
    ("l_green", "ars_nouveau:green_archwood_leaves", "Green Archwood Leaves", "#4f8a3c", False, False),
    ("flower", "minecraft:allium", "Allium", "#b565e0", False, True),
    ("me", "ae2:controller", "ME Controller", "#4a5a66", False, False),
    ("p_ars", "platzhalter:ars_nouveau", "Platz: Wixie Enchanting Apparatus mit Arcane Pedestals", "#3f8fd6", False, False),
    ("p_ars_t", "platzhalter:ars_nouveau_technik", "Platz: Source Jars, Imbuement Chamber, Pattern Provider", "#7fb3e6", False, False),
    ("p_occ", "platzhalter:occultism", "Platz: Ritualkreis (Golden Sacrificial Bowl, Bowls)", "#7a3fbf", False, False),
    ("p_occ_t", "platzhalter:occultism_technik", "Platz: Djinni Crusher, Spirit Fire, Dimensional Storage", "#a87fd6", False, False),
    ("p_irons", "platzhalter:irons_spells", "Platz: Arcane Anvil, Scroll Forge, Inscription Table", "#d6a33f", False, False),
    ("p_irons_t", "platzhalter:irons_spells_technik", "Platz: Alchemist Cauldrons, Pattern Provider", "#e6c47f", False, False),
    ("p_forb", "platzhalter:forbidden_arcanus", "Platz: Hephaestus Forge mit Darkstone Pedestals", "#2e2a3a", False, False),
    ("p_forb_t", "platzhalter:forbidden_arcanus_technik", "Platz: Clibano, Essenz-Lager, Pattern Provider", "#6a6680", False, False),
    ("p_evil", "platzhalter:evilcraft", "Platz: Blood Infuser, Purifier", "#a3242a", False, False),
    ("p_evil_t", "platzhalter:evilcraft_technik", "Platz: Dark Tanks, Blood Extractor, Pattern Provider", "#d66a6a", False, False),
    ("p_lib", "platzhalter:apothic_bibliothek", "Platz: Library of Alexandria", "#c9a64a", False, False),
]

V = {}


def setze(x, y, z, m):
    V[(x, y, z)] = m


def loesche(x, y, z):
    V.pop((x, y, z), None)


# Sternform: Spitzen und Kerben, eine Kerbe zeigt genau zum Ring
ECKEN = []
for k in range(10):
    a = math.radians(ZUM_RING + 36 + k * 36)
    r = R_SPITZE if k % 2 == 0 else R_KERBE
    ECKEN.append((r * math.cos(a), r * math.sin(a)))
# ECKEN[9] liegt bei ZUM_RING + 360 = Kerbe zum Ring


def innen(px, pz):
    drin = False
    n = len(ECKEN)
    for i in range(n):
        x1, z1 = ECKEN[i]
        x2, z2 = ECKEN[(i + 1) % n]
        if (z1 > pz) != (z2 > pz):
            xs = x1 + (pz - z1) * (x2 - x1) / (z2 - z1)
            if px < xs:
                drin = not drin
    return drin


def randabstand(px, pz):
    best = 1e9
    n = len(ECKEN)
    for i in range(n):
        x1, z1 = ECKEN[i]
        x2, z2 = ECKEN[(i + 1) % n]
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((px - x1) * dx + (pz - z1) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(px - x1 - t * dx, pz - z1 - t * dz))
    return best


def winkel_rel(px, pz):
    """Winkel relativ zur Ringrichtung, 0..360."""
    return (math.degrees(math.atan2(pz, px)) - ZUM_RING) % 360


def fluegel_von(px, pz):
    """Index 0..4 des Flügels (Zacke bei ZUM_RING + 36 + i*72)."""
    w = (winkel_rel(px, pz) - 36 + 36) % 360
    return int(w // 72) % 5


B = 60
FELD = []
for x in range(-B, B + 1):
    for z in range(-B, B + 1):
        d = math.hypot(x, z)
        if d <= GRUND_R + 0.5:
            FELD.append((x, z, d, innen(x, z), randabstand(x, z)))


def baum(bx, bz, stamm, krone, blatt):
    for y in range(1, stamm + 1):
        setze(bx, y, bz, "log")
    my = stamm + krone * 0.6
    r = int(krone) + 1
    for x in range(bx - r, bx + r + 1):
        for z in range(bz - r, bz + r + 1):
            for y in range(int(my - krone), int(my + krone) + 1):
                if math.sqrt((x - bx) ** 2 + ((y - my) * 1.25) ** 2 + (z - bz) ** 2) <= krone and (x, y, z) not in V:
                    setze(x, y, z, blatt)


def baue():
    dach = ETAGEN * ETAGE
    ex, ez = math.cos(math.radians(ZUM_RING)), math.sin(math.radians(ZUM_RING))

    def im_eingang(x, z):
        laengs = x * ex + z * ez
        quer = -x * ez + z * ex
        return abs(quer) <= EINGANG_HALB and laengs > ATRIUM_R - 1

    # --- Boden: Gebäude, Gärten, Pentakel-Kreis
    for x, z, d, drin, rd in FELD:
        if drin:
            setze(x, 0, z, "quartz")
        elif PENTAKEL_R[0] <= d < PENTAKEL_R[1]:
            setze(x, 0, z, "quartz")
        elif PENTAKEL_R[0] - 1 <= d < PENTAKEL_R[0] or PENTAKEL_R[1] <= d < PENTAKEL_R[1] + 1:
            setze(x, 0, z, "purpur")
        else:
            setze(x, 0, z, "grass")
    # Lichtpunkte auf dem Kreis, einer gegenüber jeder Spitze
    for k in range(10):
        a = math.radians(ZUM_RING + 36 + k * 36)
        r = sum(PENTAKEL_R) / 2
        setze(round(r * math.cos(a)), 0, round(r * math.sin(a)), "amethyst")

    # --- Flügel: Glaswände, unten klar, oben lila
    for x, z, d, drin, rd in FELD:
        if not drin or d < ATRIUM_R:
            continue
        if rd < 1.3:
            for y in range(1, dach):
                setze(x, y, z, "glass" if y < ETAGE else "lila")
    # weiße Stützen an allen Ecken
    for cx, cz in ECKEN:
        for x, z, d, drin, rd in FELD:
            if drin and math.hypot(x - cx, z - cz) <= 2.2:
                for y in range(1, dach):
                    setze(x, y, z, "white")
    # Decken und umlaufende weiße Bänder (wie am Ring)
    for y in (ETAGE, dach):
        for x, z, d, drin, rd in FELD:
            if drin or rd <= 1.0:
                setze(x, y, z, "white")
    # Dach: leuchtende Mittellinie jeder Zacke
    for x, z, d, drin, rd in FELD:
        if not drin or d < ATRIUM_R + 1:
            continue
        w = winkel_rel(x, z)
        abw = abs((w - 36 + 36) % 72 - 36)          # Abstand zur Zackenmitte in Grad
        if d * math.radians(abw) <= 0.6 and rd > 1.5:
            setze(x, dach + 1, z, "amethyst")

    # --- Atrium: runder Turm in der Mitte, Glaskuppel
    for x, z, d, drin, rd in FELD:
        if d <= ATRIUM_R:
            for y in (ETAGE, dach):
                setze(x, y, z, "white")
        if ATRIUM_R - 1.3 < d <= ATRIUM_R:
            w = math.degrees(math.atan2(z, x))
            rippe = d * math.radians(abs((w + 9) % 18 - 9)) <= 0.7
            for y in range(1, ATRIUM_H):
                if y in (ETAGE, dach, 18):
                    setze(x, y, z, "white")
                elif y > dach:
                    setze(x, y, z, "white" if rippe else "lila")
                else:
                    setze(x, y, z, "glass" if not rippe else "white")
    # Galerie bei 18: Ring mit offenem Luftraum über der Verzauberungshalle
    for x, z, d, drin, rd in FELD:
        if 8 <= d <= ATRIUM_R:
            setze(x, 18, z, "white")
    # Kuppel
    a = ATRIUM_R
    rs = (a * a + KUPPEL_H * KUPPEL_H) / (2 * KUPPEL_H)
    mitte_y = ATRIUM_H + KUPPEL_H - rs
    for y in range(ATRIUM_H, ATRIUM_H + KUPPEL_H + 1):
        for x, z, d, drin, rd in FELD:
            if d > a + 1:
                continue
            r = math.sqrt(d * d + (y - mitte_y) ** 2)
            if abs(r - rs) < 0.6:
                w = math.degrees(math.atan2(z, x))
                rippe = d > 2 and d * math.radians(abs((w + 18) % 36 - 18)) <= 0.5
                setze(x, y, z, "white" if rippe or y == ATRIUM_H else "glass")
    setze(0, ATRIUM_H + KUPPEL_H, 0, "amethyst")
    setze(0, ATRIUM_H + KUPPEL_H + 1, 0, "amethyst")

    # Erdgeschoss Atrium: ME-Knoten in der Mitte
    for x in range(-1, 2):
        for z in range(-1, 2):
            for y in range(1, 4):
                setze(x, y, z, "me")
    for x, z, d, drin, rd in FELD:
        if 4.5 <= d < 5.5:
            setze(x, 0, z, "amethyst")
    # 2. Ebene (über y 12): Verzauberungshalle, Tisch mit Regalring, Bibliothek
    yt = dach + 1
    setze(0, yt, 0, "table")
    for x in range(-2, 3):
        for z in range(-2, 3):
            if max(abs(x), abs(z)) == 2 and not (x == 0 and z == 2):
                setze(x, yt, z, "shelf")
                setze(x, yt + 1, z, "shelf")
    for x, z, d, drin, rd in FELD:
        if 5.5 <= d < 6.5:
            setze(x, dach, z, "purpur")
    lx, lz = round(-9 * ex), round(-9 * ez)
    for y in (yt, yt + 1):
        setze(lx, y, lz, "p_lib")

    # --- Eingang zur Ringseite, Gang bis ins Atrium
    for x, z, d, drin, rd in FELD:
        if im_eingang(x, z) and d <= R_KERBE + 2:
            for y in range(1, 5):
                loesche(x, y, z)
            setze(x, 0, z, "quartz")
            quer = -x * ez + z * ex
            if abs(abs(quer) - EINGANG_HALB) < 0.6 and d > ATRIUM_R:
                for y in range(1, 5):
                    setze(x, y, z, "glass")

    # --- Flügel innen: Ritualsaal oben, Technik unten
    for i, (kurz, name, farbe) in enumerate(FLUEGEL):
        a = math.radians(ZUM_RING + 36 + i * 72)
        cx, cz = 30 * math.cos(a), 30 * math.sin(a)
        tx, tz = 22 * math.cos(a), 22 * math.sin(a)
        for x, z, d, drin, rd in FELD:
            if not drin:
                continue
            r = math.hypot(x - cx, z - cz)
            if r <= 5.5:                                   # Ritualboden oben
                setze(x, ETAGE, z, "deepslate" if r <= 4.5 else "purpur")
            if r <= 0.8:
                setze(x, ETAGE + 1, z, "p_" + {"ars": "ars", "occultism": "occ", "irons": "irons", "forbidden": "forb", "evilcraft": "evil"}[kurz])
            q = math.hypot(x - tx, z - tz)
            if q <= 3 and abs((x - tx) * math.sin(a) - (z - tz) * math.cos(a)) <= 3 and int(q * 2) % 2 == 0 and rd > 2:
                setze(x, 1, z, "p_" + {"ars": "ars", "occultism": "occ", "irons": "irons", "forbidden": "forb", "evilcraft": "evil"}[kurz] + "_t")
        # Deckenlicht in beiden Ebenen
        for x, z, d, drin, rd in FELD:
            if drin and d > ATRIUM_R + 1 and rd > 2 and x % 4 == 0 and z % 4 == 0:
                for y in (ETAGE - 1, dach - 1):
                    if (x, y, z) not in V:
                        setze(x, y, z, "lantern")

    # --- Gärten zwischen den Zacken: Archwood in vier Farben, Allium
    blaetter = ["l_purple", "l_blue", "l_red", "l_green"]
    s = 99
    for k in range(5):
        a = math.radians(ZUM_RING + k * 72)
        if k == 0:
            continue                                       # vor dem Eingang bleibt frei
        for j, (r, off) in enumerate(((33, 0), (40, -9), (40, 9))):
            aa = a + math.radians(off)
            bx, bz = round(r * math.cos(aa)), round(r * math.sin(aa))
            baum(bx, bz, 4 + j % 2, 2.6 if j else 3.2, blaetter[(k + j) % 4])
    for x, z, d, drin, rd in FELD:
        if V.get((x, 0, z)) == "grass" and (x, 1, z) not in V and d < PENTAKEL_R[0] - 1:
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            if s % 9 == 0:
                setze(x, 1, z, "flower")

    # --- Allee zum Ring-Tor: weißer Weg mit lila Kante und Lichtsäulen
    lang = ABSTAND - RING_GRUND
    for l in range(int(R_KERBE), lang + 1):
        for q in range(-4, 5):
            x = round(l * ex - q * ez)
            z = round(l * ez + q * ex)
            if (x, 1, z) in V and V[(x, 1, z)] not in ("flower",):
                continue
            loesche(x, 1, z)
            setze(x, 0, z, "quartz" if abs(q) <= 2 else "purpur" if abs(q) == 3 else "grass")
            if abs(q) == 4 and l % 6 == 0 and l > PENTAKEL_R[1]:
                for y in (1, 2):
                    setze(x, y, z, "white")
                setze(x, 3, z, "amethyst")


def schreibe(ziel):
    baue()
    minx = min(k[0] for k in V)
    minz = min(k[2] for k in V)
    p0 = (MITTE[0] + minx, 65, MITTE[1] + minz)
    reihenfolge = [b[0] for b in BLOECKE]
    benutzt = [k for k in reihenfolge if k in set(V.values())]
    index = {k: i for i, k in enumerate(benutzt)}
    info = {b[0]: b for b in BLOECKE}
    palette = [{"id": info[k][1], "name": info[k][2], "farbe": info[k][3], "transparent": info[k][4], "klein": info[k][5]} for k in benutzt]
    bloecke = sorted(([x - minx, y, z - minz, index[m]] for (x, y, z), m in V.items()), key=lambda b: (b[1], b[2], b[0]))
    groesse = [max(b[0] for b in bloecke) + 1, max(b[1] for b in bloecke) + 1, max(b[2] for b in bloecke) + 1]
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("w", encoding="utf-8") as f:
        f.write('{"quelle":"tools/modell-magiehaus.py","groesse":')
        json.dump(groesse, f)
        f.write(',"palette":')
        json.dump(palette, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")
    print(f"{ziel}: {len(bloecke)} Blöcke, Größe {groesse}, Mitte Welt {MITTE}, P0 {p0}, Mitte im Raster ({-minx}, 0, {-minz}), Ringrichtung {ZUM_RING:.1f}")
    return p0, (-minx, -minz)


if __name__ == "__main__":
    wurzel = Path(__file__).resolve().parent.parent
    schreibe(wurzel / "gebaeude" / "magiehaus" / "modell.json")
