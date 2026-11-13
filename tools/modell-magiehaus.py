"""Erzeugt das Blockmodell des Magiehauses: ein Pentagramm im Pentakel-Kreis.

Fünf Flügel (Ars Nouveau, Occultism, Iron's Spells, Forbidden & Arcanus, EvilCraft)
um ein rundes Atrium. Drei Ebenen:

  Keller  (y 0–5)   Technik: P2P-Einspeisung aus dem ME-Gebäude in der Mitte,
                    Kabelwege zu jedem Flügel, Pattern Provider, Tanks, Mobfarm
  EG      (y 7–11)  Werkstätten mit den Maschinen jeder Mod, 5 Blöcke hoch
  OG      (y 13–20) Ritualsäle, 8 Blöcke hoch, lila Glas

Im Atrium: Eingangshalle mit Wasserbecken, darüber die Verzauberungshalle
(Apothic Enchanting) unter einer Glaskuppel. Es gibt KEINEN eigenen ME Controller,
das Netz kommt per P2P-Tunnel aus dem ME-Gebäude.

Blöcke mit der Kennung platzhalter:* markieren nur, wo eine Maschine, ein Ritual
oder ein Raum hinkommt. Sie sind keine echten Blöcke.

Nutzung:  python3 tools/modell-magiehaus.py
Ergebnis: gebaeude/magiehaus/modell.json
"""
import json
import math
from pathlib import Path

# ---------------------------------------------------------------- Lage
RING_MITTE = (263, -221)     # Mitte vom Hauptgebäude
RING_GRUND = 84              # bis hier reicht die Anlage vom Hauptgebäude
TOR_WINKEL = -31.94 + 180    # Ring-Tor nach Westsüdwest (Welt: 0 = Ost, 90 = Süd)
GRUND_R = 61                 # bis hier reicht die Anlage vom Magiehaus
MITTE = (88, -221)           # Mitte vom Magiehaus (Welt x, z), genau westlich vom Ring
# Ende der Ring-Zufahrt am Westsüdwest-Tor; dorthin zeigt der Eingang, dorthin führt die Allee
_t = math.radians(TOR_WINKEL)
TOR_PUNKT = (RING_MITTE[0] + RING_GRUND * math.cos(_t), RING_MITTE[1] + RING_GRUND * math.sin(_t))
ZUM_RING = math.degrees(math.atan2(TOR_PUNKT[1] - MITTE[1], TOR_PUNKT[0] - MITTE[0]))
ABSTAND = math.hypot(TOR_PUNKT[0] - MITTE[0], TOR_PUNKT[1] - MITTE[1])   # Länge Mitte bis Tor

# ---------------------------------------------------------------- Maße
R_SPITZE = 54                # Radius der Zackenspitzen
R_KERBE = 32                 # Radius der Innenecken
G = 6                        # Bodenhöhe (EG-Boden) im Modell; darunter der Keller
EG_DECKE = G + 6             # 5 Blöcke lichte Höhe im EG
DACH = EG_DECKE + 9          # 8 Blöcke lichte Höhe im OG
ATRIUM_R = 15.5
ATRIUM_H = DACH + 9          # Atriumwand über dem Dach, darüber die Kuppel
KUPPEL_H = 10
KELLER_R = 55                # Keller unter dem ganzen Pentakel
PENTAKEL_R = (56, 58.2)      # Kreisweg um das Pentagramm
EINGANG_HALB = 3
RITUAL_R = 27                # Abstand der Ritualmitte zur Gebäudemitte

FLUEGEL = [  # in Uhrzeigerrichtung ab der Zacke rechts vom Eingang
    "ars", "occultism", "irons", "forbidden", "evilcraft",
]

BLOECKE = [
    ("white", "minecraft:white_concrete", "White Concrete", "#e4e8e8", False, False),
    ("glass", "minecraft:glass", "Glass", "#c0d8de", True, False),
    ("lila", "minecraft:purple_stained_glass", "Purple Stained Glass", "#8a4fc4", True, False),
    ("quartz", "minecraft:smooth_quartz", "Smooth Quartz", "#ece6df", False, False),
    ("deepslate", "minecraft:polished_deepslate", "Polished Deepslate", "#45454d", False, False),
    ("tiles", "minecraft:deepslate_tiles", "Deepslate Tiles", "#36363c", False, False),
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
    ("elev", "elevatorid:elevator_purple", "Elevator (Purple)", "#7a3fbf", False, False),
    # Platzhalter: nur Markierungen, keine echten Blöcke
    ("p_p2p", "platzhalter:p2p_einspeisung", "Platz: ME P2P Tunnels aus dem ME-Gebäude, Verteilung zu den Flügeln", "#2fb0a0", False, False),
    ("p_kabel", "platzhalter:kabelweg", "Kabelweg (ME Cable unter der Decke)", "#5ad1c2", False, True),
    ("p_treppe", "platzhalter:treppe", "Platz: Treppe Keller – EG – OG", "#c9c2b0", False, False),
    ("p_lib", "platzhalter:apothic_bibliothek", "Platz: Library of Alexandria", "#c9a64a", False, False),
    ("p_mob", "platzhalter:mobfarm", "Mobfarm: Spawnfläche (dunkel halten)", "#2b1d1d", False, False),
    ("p_kill", "platzhalter:mobfarm_kill", "Mobfarm: Tötungskammer mit Blood Extractor", "#7a1e1e", False, False),
    ("p_ars_og", "platzhalter:ars_ritual", "Platz: Ritual Brazier und Ritualfläche (Ars Nouveau)", "#3f8fd6", False, False),
    ("p_ars_eg", "platzhalter:ars_apparatus", "Platz: Wixie Enchanting Apparatus mit 8 Arcane Pedestals, Imbuement Chambers", "#3f8fd6", False, False),
    ("p_ars_k", "platzhalter:ars_technik", "Platz: Pattern Provider, Source Jars, Sourcelinks", "#7fb3e6", False, False),
    ("p_occ_og", "platzhalter:occultism_ritual", "Platz: großer Ritualkreis 21 × 21 (Golden Sacrificial Bowl in der Mitte)", "#7a3fbf", False, False),
    ("p_occ_eg", "platzhalter:occultism_werkstatt", "Platz: Spirit Fire, Dimensional Storage, Crusher-Spirits", "#7a3fbf", False, False),
    ("p_occ_k", "platzhalter:occultism_technik", "Platz: Pattern Provider, Ein- und Ausgabekisten der Spirits", "#a87fd6", False, False),
    ("p_irons_og", "platzhalter:irons_halle", "Platz: Spellbook-Ausstellung und Übungsfläche (Iron's Spells)", "#d6a33f", False, False),
    ("p_irons_eg", "platzhalter:irons_werkstatt", "Platz: Arcane Anvil, Scroll Forge, Inscription Table, Alchemist Cauldrons", "#d6a33f", False, False),
    ("p_irons_k", "platzhalter:irons_technik", "Platz: Pattern Provider, Tanks für die Cauldrons", "#e6c47f", False, False),
    ("p_forb_og", "platzhalter:hephaestus_forge", "Platz: Hephaestus Forge mit 8 Darkstone Pedestals und Enhancern", "#2e2a3a", False, False),
    ("p_forb_eg", "platzhalter:clibano", "Platz: Clibano (3 × 3 × 3)", "#4a4560", False, False),
    ("p_forb_k", "platzhalter:forbidden_technik", "Platz: Pattern Provider für die Clibano, Essenz-Lager", "#6a6680", False, False),
    ("p_evil_og", "platzhalter:evilcraft_halle", "Platz: Environmental Accumulator und Ausstellung (EvilCraft)", "#a3242a", False, False),
    ("p_evil_eg", "platzhalter:evilcraft_werkstatt", "Platz: Blood Infuser, Purifier, Dark Tanks", "#a3242a", False, False),
    ("p_evil_k", "platzhalter:evilcraft_technik", "Platz: Pattern Provider, Blut-Leitung von der Mobfarm", "#d66a6a", False, False),
]

V = {}
AUFZUEGE = []


def setze(x, y, z, m):
    V[(x, y, z)] = m


def loesche(x, y, z):
    V.pop((x, y, z), None)


ECKEN = []
for _k in range(10):
    _a = math.radians(ZUM_RING + 36 + _k * 36)
    _r = R_SPITZE if _k % 2 == 0 else R_KERBE
    ECKEN.append((_r * math.cos(_a), _r * math.sin(_a)))


def innen(px, pz):
    drin = False
    for i in range(10):
        x1, z1 = ECKEN[i]
        x2, z2 = ECKEN[(i + 1) % 10]
        if (z1 > pz) != (z2 > pz) and px < x1 + (pz - z1) * (x2 - x1) / (z2 - z1):
            drin = not drin
    return drin


def randabstand(px, pz):
    best = 1e9
    for i in range(10):
        x1, z1 = ECKEN[i]
        x2, z2 = ECKEN[(i + 1) % 10]
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((px - x1) * dx + (pz - z1) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(px - x1 - t * dx, pz - z1 - t * dz))
    return best


def achse(i):
    """Einheitsvektor der Zacke i."""
    a = math.radians(ZUM_RING + 36 + i * 72)
    return math.cos(a), math.sin(a)


def lokal(x, z, i):
    """Koordinaten (u längs der Zacke, v quer) für Flügel i."""
    ax, az = achse(i)
    return x * ax + z * az, -x * az + z * ax


def fluegel_von(x, z):
    w = (math.degrees(math.atan2(z, x)) - ZUM_RING) % 360
    return int(w // 72) % 5


B = int(GRUND_R) + 1
FELD = []
for x in range(-B, B + 1):
    for z in range(-B, B + 1):
        d = math.hypot(x, z)
        if d <= GRUND_R + 0.5:
            FELD.append((x, z, d, innen(x, z), randabstand(x, z)))


def baum(bx, bz, stamm, krone, blatt):
    for y in range(G + 1, G + stamm + 1):
        setze(bx, y, bz, "log")
    my = G + stamm + krone * 0.6
    r = int(krone) + 1
    for x in range(bx - r, bx + r + 1):
        for z in range(bz - r, bz + r + 1):
            for y in range(int(my - krone), int(my + krone) + 1):
                if math.sqrt((x - bx) ** 2 + ((y - my) * 1.25) ** 2 + (z - bz) ** 2) <= krone and (x, y, z) not in V:
                    setze(x, y, z, blatt)


def flaeche(i, u0, v0, halb_u, halb_v, y, m, nur_innen=True):
    """Rechteck im Flügel i, Mitte (u0, v0), auf Höhe y."""
    for x, z, d, drin, rd in FELD:
        if nur_innen and (not drin or rd < 2):
            continue
        u, v = lokal(x, z, i)
        if abs(u - u0) <= halb_u and abs(v - v0) <= halb_v:
            setze(x, y, z, m)


def scheibe(i, u0, r, y, m, rand=None):
    ax, az = achse(i)
    cx, cz = u0 * ax, u0 * az
    for x, z, d, drin, rd in FELD:
        q = math.hypot(x - cx, z - cz)
        if q <= r:
            setze(x, y, z, m)
        elif rand and q <= r + 1:
            setze(x, y, z, rand)


def baue():
    ex, ez = math.cos(math.radians(ZUM_RING)), math.sin(math.radians(ZUM_RING))

    # ================================================================ Keller
    for x, z, d, drin, rd in FELD:
        if d <= KELLER_R:
            setze(x, 0, z, "deepslate")
            if d > KELLER_R - 1.3:
                for y in range(1, G):
                    setze(x, y, z, "tiles")
            elif x % 5 == 0 and z % 5 == 0:
                setze(x, G - 1, z, "lantern")
    # Kabelwege: von der Mitte sternförmig zu jedem Flügel
    for i in range(5):
        for x, z, d, drin, rd in FELD:
            u, v = lokal(x, z, i)
            if 2 < u < 40 and abs(v) <= 0.6:
                setze(x, G - 1, z, "p_kabel")
    for x, z, d, drin, rd in FELD:
        if abs(d - 9) < 0.6:
            setze(x, G - 1, z, "p_kabel")
    for y in range(1, 4):
        setze(0, y, 0, "p_p2p")
    # Technik je Flügel im Keller
    for i, k in enumerate(FLUEGEL):
        kurz = {"ars": "ars", "occultism": "occ", "irons": "irons", "forbidden": "forb", "evilcraft": "evil"}[k]
        if k == "evilcraft":
            continue
        for u in range(20, 40, 4):
            for v in (-5, 5):
                flaeche(i, u, v, 1, 1, 1, "p_%s_k" % kurz, nur_innen=False)
    # Mobfarm unter dem EvilCraft-Flügel: dunkle Spawnfläche, Tötungskammer zur Mitte hin
    ie = FLUEGEL.index("evilcraft")
    for x, z, d, drin, rd in FELD:
        u, v = lokal(x, z, ie)
        if 24 <= u <= 50 and abs(v) <= 13 and d <= KELLER_R - 2:
            setze(x, 0, z, "p_mob")
            if (u in (24, 50) or abs(v) == 13) and d < KELLER_R - 2:
                for y in range(1, G):
                    setze(x, y, z, "tiles")
            for y in (G - 1,):
                loesche(x, y, z)
        if 18 <= u < 24 and abs(v) <= 3:
            setze(x, 0, z, "p_kill")
    for x, z, d, drin, rd in FELD:
        u, v = lokal(x, z, ie)
        if 6 <= u < 18 and abs(v) <= 3:
            flaeche(ie, 14, 0, 2, 2, 1, "p_evil_k", nur_innen=False)
            break

    # ================================================================ Boden auf Höhe G
    for x, z, d, drin, rd in FELD:
        if drin:
            setze(x, G, z, "quartz")
        elif PENTAKEL_R[0] <= d < PENTAKEL_R[1]:
            setze(x, G, z, "quartz")
        elif PENTAKEL_R[0] - 1 <= d < PENTAKEL_R[0] or PENTAKEL_R[1] <= d < PENTAKEL_R[1] + 1:
            setze(x, G, z, "purpur")
        else:
            setze(x, G, z, "grass")
    for k in range(10):
        a = math.radians(ZUM_RING + 36 + k * 36)
        r = sum(PENTAKEL_R) / 2
        setze(round(r * math.cos(a)), G, round(r * math.sin(a)), "amethyst")

    # ================================================================ Flügel
    for x, z, d, drin, rd in FELD:
        if not drin or d < ATRIUM_R:
            continue
        if rd < 1.3:
            for y in range(G + 1, DACH):
                setze(x, y, z, "glass" if y < EG_DECKE else "lila")
    for cx, cz in ECKEN:
        for x, z, d, drin, rd in FELD:
            if drin and math.hypot(x - cx, z - cz) <= 2.2:
                for y in range(G + 1, DACH):
                    setze(x, y, z, "white")
    for y in (EG_DECKE, DACH):
        for x, z, d, drin, rd in FELD:
            if drin or rd <= 1.0:
                setze(x, y, z, "white")
    for x, z, d, drin, rd in FELD:
        if not drin or d < ATRIUM_R + 1:
            continue
        w = (math.degrees(math.atan2(z, x)) - ZUM_RING) % 360
        abw = abs((w - 36 + 36) % 72 - 36)
        if d * math.radians(abw) <= 0.6 and rd > 1.5:
            setze(x, DACH + 1, z, "amethyst")
    # Deckenlicht
    for x, z, d, drin, rd in FELD:
        if drin and d > ATRIUM_R + 1 and rd > 2 and x % 4 == 0 and z % 4 == 0:
            for y in (EG_DECKE - 1, DACH - 1):
                if (x, y, z) not in V:
                    setze(x, y, z, "lantern")

    # ---------------------------------------------------------------- Einrichtung je Flügel
    for i, k in enumerate(FLUEGEL):
        og, eg = G + 7 - 1 + 1, G + 1          # OG-Boden ist EG_DECKE, Dinge stehen eine Lage höher
        ogb = EG_DECKE
        if k == "occultism":
            scheibe(i, RITUAL_R - 1, 10.4, ogb, "deepslate", rand="purpur")
            scheibe(i, RITUAL_R - 1, 0.5, ogb + 1, "p_occ_og")
            flaeche(i, 26, 0, 2, 6, eg, "p_occ_eg")
            flaeche(i, 38, 0, 1, 2, eg, "p_occ_eg")
        elif k == "forbidden":
            scheibe(i, RITUAL_R, 6.5, ogb, "deepslate", rand="purpur")
            scheibe(i, RITUAL_R, 0.5, ogb + 1, "p_forb_og")
            for y in range(eg, eg + 3):
                flaeche(i, 27, 0, 1, 1, y, "p_forb_eg")
            flaeche(i, 37, 0, 1, 2, eg, "p_forb_eg")
        elif k == "ars":
            scheibe(i, RITUAL_R, 5.5, ogb, "deepslate", rand="purpur")
            scheibe(i, RITUAL_R, 0.5, ogb + 1, "p_ars_og")
            scheibe(i, 26, 3.5, eg - 1, "deepslate", rand="purpur")
            scheibe(i, 26, 0.5, eg, "p_ars_eg")
            for v in (-9, 9):
                flaeche(i, 26, v, 1, 1, eg, "p_ars_eg")
        elif k == "irons":
            scheibe(i, RITUAL_R, 7.5, ogb, "deepslate", rand="purpur")
            scheibe(i, RITUAL_R, 0.5, ogb + 1, "p_irons_og")
            flaeche(i, 26, -8, 1, 2, eg, "p_irons_eg")
            flaeche(i, 26, 8, 1, 2, eg, "p_irons_eg")
            flaeche(i, 34, 0, 1, 1, eg, "p_irons_eg")
        elif k == "evilcraft":
            scheibe(i, RITUAL_R, 5.5, ogb, "deepslate", rand="purpur")
            scheibe(i, RITUAL_R, 0.5, ogb + 1, "p_evil_og")
            flaeche(i, 24, 0, 1, 4, eg, "p_evil_eg")
            flaeche(i, 33, 0, 1, 1, eg, "p_evil_eg")

    # ================================================================ Atrium
    for x, z, d, drin, rd in FELD:
        if d <= ATRIUM_R:
            for y in (EG_DECKE, DACH):
                setze(x, y, z, "white")
        if ATRIUM_R - 1.3 < d <= ATRIUM_R:
            w = math.degrees(math.atan2(z, x))
            rippe = d * math.radians(abs((w + 9) % 18 - 9)) <= 0.7
            for y in range(G + 1, ATRIUM_H):
                if y in (EG_DECKE, DACH):
                    setze(x, y, z, "white")
                elif y > DACH:
                    setze(x, y, z, "white" if rippe else "lila")
                else:
                    setze(x, y, z, "white" if rippe else "glass")
    # Durchgänge in der Atriumwand: zu jedem Flügel und zum Eingang, in EG und OG
    richtungen = [ZUM_RING + 36 + i * 72 for i in range(5)] + [ZUM_RING]
    for w0 in richtungen:
        ax, az = math.cos(math.radians(w0)), math.sin(math.radians(w0))
        for x, z, d, drin, rd in FELD:
            if not (ATRIUM_R - 1.5 < d <= ATRIUM_R + 0.5):
                continue
            if x * ax + z * az > 0 and abs(-x * az + z * ax) <= 2.5:
                for y in list(range(G + 1, G + 5)) + list(range(EG_DECKE + 1, EG_DECKE + 6)):
                    loesche(x, y, z)
    # Galerie oben, darüber offener Luftraum
    for x, z, d, drin, rd in FELD:
        if 9 <= d <= ATRIUM_R:
            setze(x, DACH + 5, z, "white")
    # Kuppel
    rs = (ATRIUM_R ** 2 + KUPPEL_H ** 2) / (2 * KUPPEL_H)
    my = ATRIUM_H + KUPPEL_H - rs
    for y in range(ATRIUM_H, ATRIUM_H + KUPPEL_H + 1):
        for x, z, d, drin, rd in FELD:
            if d > ATRIUM_R + 1:
                continue
            r = math.sqrt(d * d + (y - my) ** 2)
            if abs(r - rs) < 0.6:
                w = math.degrees(math.atan2(z, x))
                rippe = d > 2 and d * math.radians(abs((w + 18) % 36 - 18)) <= 0.5
                setze(x, y, z, "white" if rippe or y == ATRIUM_H else "glass")
    for y in (ATRIUM_H + KUPPEL_H, ATRIUM_H + KUPPEL_H + 1):
        setze(0, y, 0, "amethyst")
    # EG: Eingangshalle mit Wasserbecken
    for x, z, d, drin, rd in FELD:
        if d <= 3.5:
            setze(x, G, z, "water")
        elif d <= 4.6:
            setze(x, G, z, "amethyst")
    # OG: Verzauberungshalle
    yt = EG_DECKE + 1
    setze(0, yt, 0, "table")
    for x in range(-2, 3):
        for z in range(-2, 3):
            if max(abs(x), abs(z)) == 2 and not (x == 0 and z == 2):
                setze(x, yt, z, "shelf")
                setze(x, yt + 1, z, "shelf")
    for x, z, d, drin, rd in FELD:
        if 5.5 <= d < 6.5:
            setze(x, EG_DECKE, z, "purpur")
    lx, lz = round(-10 * ex), round(-10 * ez)
    for y in (yt, yt + 1):
        setze(lx, y, lz, "p_lib")
    # Treppe vom Keller bis ins OG, gegenüber vom Eingang neben dem Atrium
    tx, tz = round(-12.5 * ex + 2 * ez), round(-12.5 * ez - 2 * ex)
    for y in range(1, DACH):
        setze(tx, y, tz, "p_treppe")
    for y in (G, EG_DECKE):
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                loesche(tx + ox, y, tz + oz)

    # ================================================================ Aufzüge (Elevator Mod)
    # Je eine Spalte Keller – EG – OG: eine am Atrium neben der Treppe, eine in jedem Flügel.
    # Die Aufzüge müssen genau übereinander stehen, darüber jeweils 2 Blöcke Luft.
    spalten = [(tx + round(2 * ez), tz - round(2 * ex))]
    for i in range(5):
        ax, az = achse(i)
        spalten.append((round(19 * ax + 6 * az), round(19 * az - 6 * ax)))
    AUFZUEGE.clear()
    for sx, sz in spalten:
        for y in (0, G, EG_DECKE):
            setze(sx, y, sz, "elev")
            for h in (1, 2):
                loesche(sx, y + h, sz)
        AUFZUEGE.append((sx, sz))

    # ================================================================ Eingang und Allee
    for x, z, d, drin, rd in FELD:
        laengs = x * ex + z * ez
        quer = -x * ez + z * ex
        if abs(quer) <= EINGANG_HALB and laengs > ATRIUM_R - 1 and d <= R_KERBE + 2:
            for y in range(G + 1, G + 5):
                loesche(x, y, z)
            setze(x, G, z, "quartz")
            if abs(abs(quer) - EINGANG_HALB) < 0.6 and d > ATRIUM_R:
                for y in range(G + 1, G + 5):
                    setze(x, y, z, "glass")
    blaetter = ["l_purple", "l_blue", "l_red", "l_green"]
    for k in range(1, 5):
        a = math.radians(ZUM_RING + k * 72)
        for j, (r, off) in enumerate(((42, 0), (50, -8), (50, 8))):
            aa = a + math.radians(off)
            baum(round(r * math.cos(aa)), round(r * math.sin(aa)), 4 + j % 2, 2.6 if j else 3.4, blaetter[(k + j) % 4])
    s = 99
    for x, z, d, drin, rd in FELD:
        if V.get((x, G, z)) == "grass" and (x, G + 1, z) not in V and d < PENTAKEL_R[0] - 1:
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            if s % 9 == 0:
                setze(x, G + 1, z, "flower")
    lang = int(ABSTAND) + 1
    for l in range(int(R_KERBE), lang + 1):
        for q in range(-4, 5):
            x = round(l * ex - q * ez)
            z = round(l * ez + q * ex)
            loesche(x, G + 1, z)
            setze(x, G, z, "quartz" if abs(q) <= 2 else "purpur" if abs(q) == 3 else "grass")
            if abs(q) == 4 and l % 6 == 0 and l > PENTAKEL_R[1]:
                for y in (G + 1, G + 2):
                    setze(x, y, z, "white")
                setze(x, G + 3, z, "amethyst")


def schreibe(ziel):
    baue()
    minx = min(k[0] for k in V)
    minz = min(k[2] for k in V)
    p0 = (MITTE[0] + minx, 65 - G, MITTE[1] + minz)
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
    print(f"{ziel}: {len(bloecke)} Blöcke, Größe {groesse}, Mitte Welt {MITTE}, P0 {p0}, Mitte im Raster ({-minx}, {G}, {-minz}), Ringrichtung {ZUM_RING:.1f}")
    return p0, (-minx, -minz)


if __name__ == "__main__":
    wurzel = Path(__file__).resolve().parent.parent
    schreibe(wurzel / "gebaeude" / "magiehaus" / "modell.json")
