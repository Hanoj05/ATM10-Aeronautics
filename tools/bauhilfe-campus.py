"""Bauhilfe für den Campus-Plan: ein Datapack, das den Plan in der Welt baut.

Nutzung:  python3 tools/bauhilfe-campus.py
Ergebnis: download/campus-bau-datapack.zip    Datapack für Minecraft 1.21.1 (pack_format 48)
          gebaeude/aussenanlagen/bauhilfe.md  Anleitung, Abschnitte, geschützte Stellen
Braucht:  nur Python 3. Läuft etwa zwei Minuten.

Verglichen wird Block für Block: der Ist-Stand aus schematics/campus.nbt gegen den Plan
(campus/gelaende.json, die Modelle aus tools/plan-umgebung.py). Nur was sich ändert, kommt
ins Datapack. Für jeden Abschnitt gibt es eine Funktion zum Bauen und eine zum Zurückbauen.

Regeln:
- Innerhalb der Campus-Grenze wird jede Spalte bis Y 45 (Unterkante der Schematic) dicht
  gemacht: Luft, Wasser, Lava und Pflanzen unter der Oberfläche werden aufgefüllt (oben drei
  Blöcke Dirt, darunter Stone). Unter Gebäuden nur unterhalb des tiefsten Gebäudeblocks.
- Über der Oberfläche kommt alles Natürliche weg (Bäume, Hügel), dann stehen dort nur noch
  die geplanten Dinge.
- Steht in einer Spalte etwas, das nicht natürlich ist und nicht zum Plan gehört (Barrels,
  Kabel, Framed Blocks …), bleibt die ganze Spalte unberührt. Sie steht in der Anleitung.
- Im Datapack stehen nur Vanilla-Blöcke (plus beim Zurückbauen die Blöcke, die schon in eurer
  Welt sind). Die Mega Torches setzt ihr von Hand, ihre Plätze stehen in der Anleitung.
"""
import base64
import gzip
import importlib.util
import io
import json
import math
import struct
import sys
import zipfile
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
PLAN = modul("plan_umgebung", "tools/plan-umgebung.py")

NS = "campus"
KACHEL = 64                     # Abschnitte von 64 × 64 Blöcken
MAX_BEFEHLE = 50000             # pro Funktionsdatei (Minecraft erlaubt 65536 pro Aufruf)
UNTEN = None                    # Unterkante: kleinste Y der Schematic, wird gesetzt

# Natürlich: darf weg oder ersetzt werden (Teil des Namens hinter dem Doppelpunkt)
NATUR = PLAN.NATUR + ("air", "lava", "ice", "snow", "vine", "lichen", "litter", "branch", "sprouts", "mushroom",
                      "bubble", "dripstone", "amethyst", "bud", "cane", "lily", "berry", "wild_", "pumpkin", "melon",
                      "bamboo", "roots", "shrub", "basalt", "magma", "obsidian", "spore", "azalea", "cactus", "pebble",
                      "twig", "rock", "root", "coral", "sea_pickle", "barnacle", "hollow", "scoria", "ochrum",
                      "crimsite", "veridium", "orchid", "allium", "bluet", "daisy", "cornflower", "lilac", "peony",
                      "rose", "oak", "spruce", "birch", "maple", "cherry", "archwood", "quarried", "fruit", "sulfur",
                      "salt", "xychorium", "raw_", "fossil", "bone_block", "prismarine", "sponge", "clover", "fallen",
                      "sediment", "netherrack", "oil", "aura_bloom", "bee_nest", "geyser", "flax", "lootr_chest",
                      "invisible_light", "light_block", "black_concrete", "concrete_powder", "fire", "cobweb", "cattail", "trillium",
                      "sage", "thistle", "tassel", "blood_stain", "reed", "clover", "heather", "lupine", "hyssop", "daisy",
                      "dead", "tall_", "large_", "seagrass", "kelp", "pointed", "nylium", "soul", "cave_vines")
# Ohne festen Körper: wird unter der Oberfläche aufgefüllt
HOHL = ("air", "water", "lava", "short_grass", "tall_grass", "fern", "seagrass", "kelp", "flower", "tulip", "poppy",
        "dandelion", "bush", "sapling", "vine", "lichen", "bubble", "snow", "litter", "sprouts", "mushroom", "cane",
        "lily", "berry", "roots", "pointed", "fire", "cobweb", "cave_vines", "spore", "leaves", "oil", "light",
        "moss_carpet", "pebble", "twig", "torch")


def kurz(name):
    return name.split(":", 1)[-1]


def ist_natur(name):
    k = kurz(name)
    return any(t in k for t in NATUR)


def ist_hohl(name):
    k = kurz(name)
    return any(t in k for t in HOHL)


def zustand(eintrag):
    """Palette-Eintrag als Block-Zustand für Befehle, z. B. minecraft:oak_log[axis=y]."""
    props = eintrag.get("Properties") or {}
    if not props:
        return eintrag["Name"]
    return "%s[%s]" % (eintrag["Name"], ",".join("%s=%s" % (k, v) for k, v in sorted(props.items())))


# Plan-Blöcke als Zustand (nur Vanilla)
PLAN_ZUSTAND = {
    "minecraft:oak_leaves": "minecraft:oak_leaves[persistent=true]",
    "minecraft:birch_leaves": "minecraft:birch_leaves[persistent=true]",
    "minecraft:cherry_leaves": "minecraft:cherry_leaves[persistent=true]",
    "minecraft:smooth_quartz_slab": "minecraft:smooth_quartz_slab[type=top]",
    "minecraft:lantern": "minecraft:lantern[hanging=false]",
}


def plan_zustand(sid):
    sid = sid.split("|")[0]
    if not sid.startswith("minecraft:"):
        return None
    return PLAN_ZUSTAND.get(sid, sid)


# --- Ist-Stand: die ganze Schematic als 3D-Feld -----------------------------------------

class Ist:
    def __init__(self, p0):
        groesse, palette, xs, ys, zs, st = GEL.lies_schematic(REPO / GEL.SCHEMATIC)
        self.nx, self.ny, self.nz = groesse
        self.p0 = p0
        self.namen = [b.get("Name", "?") for b in palette] + ["minecraft:air"]
        self.zustaende = [zustand(b) for b in palette] + ["minecraft:air"]
        self.luft = len(palette)
        self.feld = array("H", [self.luft]) * (self.nx * self.ny * self.nz)
        for x, y, z, s in zip(xs, ys, zs, st):
            self.feld[(x * self.ny + y) * self.nz + z] = s
        self.natur = [ist_natur(n) for n in self.namen]
        self.hohl = [ist_hohl(n) for n in self.namen]
        self.void = [n == "minecraft:void_air" for n in self.namen]

    def s(self, wx, wy, wz):
        x, y, z = wx - self.p0[0], wy - self.p0[1], wz - self.p0[2]
        if not (0 <= x < self.nx and 0 <= y < self.ny and 0 <= z < self.nz):
            return None
        return self.feld[(x * self.ny + y) * self.nz + z]


# --- Plan: Gelände und Modelle in Weltkoordinaten ---------------------------------------

def plan_bloecke():
    """{(x, y, z): id} aller Plan-Modellblöcke (Gebäude und Außenanlagen) in Weltkoordinaten,
    dazu {(x, z): tiefste y} der Gebäude (ohne Außenanlagen)."""
    campus = json.loads((REPO / "campus/campus.json").read_text(encoding="utf-8"))
    bl, gebaeude_unten, aussen = {}, {}, {}
    for g in campus["gebaeude"]:
        if not g.get("ordner") or not g.get("position") or g.get("karte") is False:
            continue
        m = json.loads((REPO / g["ordner"] / "modell.json").read_text(encoding="utf-8"))
        pal = m["palette"]
        for b in m["bloecke"]:
            w = GEL.welt_von(g["position"], g.get("drehung"), b[0], b[1], b[2])
            sid = pal[b[3]]["id"]
            if g.get("aussparen") is False:
                aussen[w] = sid
            else:
                bl[w] = sid
                k = (w[0], w[2])
                if k not in gebaeude_unten or w[1] < gebaeude_unten[k]:
                    gebaeude_unten[k] = w[1]
    return bl, gebaeude_unten, aussen


def lade_gelaende():
    d = json.loads((REPO / "campus/gelaende.json").read_text(encoding="utf-8"))
    h = base64.b64decode(d["hoehe"])
    b = array("H"); b.frombytes(base64.b64decode(d["block"]))
    if sys.byteorder != "little":
        b.byteswap()
    nz = d["groesse"][1]
    ox, oz, yb = d["ursprung"][0], d["ursprung"][1], d["ybasis"]
    pal = [p["id"] for p in d["palette"]]

    def oben(x, z):
        i = (x - ox) * nz + (z - oz)
        if not (0 <= x - ox < d["groesse"][0] and 0 <= z - oz < nz) or not h[i]:
            return None, None
        return yb + h[i] - 1, pal[b[i]]
    return oben


# --- Vergleich ----------------------------------------------------------------------------

def main():
    campus = json.loads((REPO / "campus/campus.json").read_text(encoding="utf-8"))
    p0 = GEL.ecke_aus_gebaeuden(campus)
    print("Lese Ist-Stand …", flush=True)
    ist = Ist(p0)
    unten = p0[1]
    oben_y = p0[1] + ist.ny - 1
    print("Lese Plan …", flush=True)
    plan, geb_unten, aussen = plan_bloecke()
    gel_oben = lade_gelaende()

    x0, x1, z0, z1, _ = PLAN.GRENZE
    aenderung = {}          # (x, y, z) -> (neu, alt)
    geschuetzt = []         # (x, z, was)
    hohl_gefuellt = 0

    def setze(x, y, z, neu):
        s = ist.s(x, y, z)
        if s is None:
            return
        alt = ist.zustaende[s]
        if neu != alt and not (neu == "minecraft:air" and ist.namen[s] in ("minecraft:air", "minecraft:cave_air")):
            aenderung[(x, y, z)] = (neu, alt)

    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not PLAN.in_grenze(x, z):
                continue
            spalte = [ist.s(x, y, z) for y in range(unten, oben_y + 1)]
            if any(s is None or ist.void[s] for s in spalte):
                continue            # außerhalb der Schematic oder nicht geladen
            gu = geb_unten.get((x, z))
            # Fremdes in der Spalte? (nicht natürlich und nicht Teil des Plans)
            fremd = None
            for y, s in zip(range(unten, oben_y + 1), spalte):
                if ist.natur[s]:
                    continue
                if gu is not None and y >= gu:
                    continue        # gehört zum Gebäude
                if plan.get((x, y, z)) == ist.namen[s] or aussen.get((x, y, z)) == ist.namen[s]:
                    continue
                fremd = ist.namen[s]
                break
            if fremd:
                geschuetzt.append((x, z, fremd))
                continue
            if gu is not None:
                # Gebäude-Spalte: unter dem Gebäude (und nie über Bodenhöhe) Hohlräume füllen,
                # im Gebäude nur die Plan-Änderungen; über dem Boden nur Wildnis entfernen.
                grenze_y = min(gu, PLAN.BODEN_Y)
                for y in range(unten, grenze_y):
                    s = spalte[y - unten]
                    if ist.hohl[s]:
                        setze(x, y, z, "minecraft:dirt" if y >= grenze_y - 3 else "minecraft:stone"); hohl_gefuellt += 1
                for y in range(gu, oben_y + 1):
                    s = spalte[y - unten]
                    p = plan.get((x, y, z))
                    if p is not None:
                        if kurz(p.split("|")[0]) != kurz(ist.namen[s]):
                            z_ = plan_zustand(p)
                            if z_:
                                setze(x, y, z, z_)
                    elif y > PLAN.BODEN_Y and any(t in kurz(ist.namen[s]) for t in PLAN.WILDNIS):
                        setze(x, y, z, "minecraft:air")
                    a = aussen.get((x, y, z))
                    if a and p is None and plan_zustand(a):
                        setze(x, y, z, plan_zustand(a))
                continue
            # Gelände-Spalte
            oy, ob = gel_oben(x, z)
            if oy is None:
                continue
            for y in range(unten, oben_y + 1):
                s = spalte[y - unten]
                a = aussen.get((x, y, z))
                if y < oy:
                    if ist.hohl[s]:
                        setze(x, y, z, "minecraft:dirt" if y >= oy - 3 else "minecraft:stone"); hohl_gefuellt += 1
                elif y == oy:
                    z_ = plan_zustand(ob) or "minecraft:grass_block"
                    if kurz(ob) != kurz(ist.namen[s]):
                        setze(x, y, z, z_)
                elif a and plan_zustand(a):
                    setze(x, y, z, plan_zustand(a))
                elif not ist.namen[s].endswith("air"):
                    setze(x, y, z, "minecraft:air")

    print("Änderungen: %d Blöcke, davon %d Hohlräume gefüllt, %d Spalten geschützt" % (len(aenderung), hohl_gefuellt, len(geschuetzt)), flush=True)
    baue_datapack(aenderung, geschuetzt)


# --- Datapack -----------------------------------------------------------------------------

def befehle(eintraege, welcher):
    """Aus {(x, y, z): (neu, alt)} Befehle machen: von unten nach oben, gleiche Blöcke in einer
    Reihe entlang x zu einem fill zusammengefasst. welcher = 0 (bauen) oder 1 (zurück)."""
    reihen = {}
    for (x, y, z), na in eintraege.items():
        reihen.setdefault((y, z), []).append((x, na[welcher]))
    aus = []
    for (y, z) in sorted(reihen, reverse=(welcher == 1)):
        punkte = sorted(reihen[(y, z)])
        i = 0
        while i < len(punkte):
            j = i
            while j + 1 < len(punkte) and punkte[j + 1][0] == punkte[j][0] + 1 and punkte[j + 1][1] == punkte[i][1]:
                j += 1
            xa, xb, blk = punkte[i][0], punkte[j][0], punkte[i][1]
            if xa == xb:
                aus.append("setblock %d %d %d %s" % (xa, y, z, blk))
            else:
                aus.append("fill %d %d %d %d %d %d %s" % (xa, y, z, xb, y, z, blk))
            i = j + 1
    return aus


def baue_datapack(aenderung, geschuetzt):
    kacheln = {}
    for (x, y, z), na in aenderung.items():
        kacheln.setdefault(((x - PLAN.GRENZE[0]) // KACHEL, (z - PLAN.GRENZE[2]) // KACHEL), {})[(x, y, z)] = na
    namen = sorted(kacheln, key=lambda k: (k[1], k[0]))
    dateien = {}
    liste = []
    for nr, k in enumerate(namen, 1):
        e = kacheln[k]
        kx0 = PLAN.GRENZE[0] + k[0] * KACHEL; kz0 = PLAN.GRENZE[2] + k[1] * KACHEL
        kx1, kz1 = kx0 + KACHEL - 1, kz0 + KACHEL - 1
        name = "a%02d" % nr
        for richtung, w in (("bau", 0), ("zurueck", 1)):
            b = befehle(e, w)
            teile = [b[i:i + MAX_BEFEHLE] for i in range(0, len(b), MAX_BEFEHLE)] or [[]]
            pfad = "data/%s/function/%s/%s" % (NS, richtung, name)
            start = ["# Abschnitt %s: x %d..%d, z %d..%d (%d Blöcke)" % (name, kx0, kx1, kz0, kz1, len(e)),
                     "forceload add %d %d %d %d" % (kx0, kz0, kx1, kz1),
                     "tellraw @a {\"text\":\"Campus %s %s: Chunks werden geladen …\",\"color\":\"gray\"}" % (richtung, name),
                     "schedule function %s:%s/%s_1 2s" % (NS, richtung, name)]
            dateien[pfad + ".mcfunction"] = "\n".join(start) + "\n"
            for t, teil in enumerate(teile, 1):
                naechste = ("schedule function %s:%s/%s_%d 1s" % (NS, richtung, name, t + 1)) if t < len(teile) else \
                    "forceload remove %d %d %d %d\ntellraw @a {\"text\":\"Campus %s %s fertig.\",\"color\":\"green\"}" % (kx0, kz0, kx1, kz1, richtung, name)
                dateien[pfad + "_%d.mcfunction" % t] = "\n".join(teil + [naechste]) + "\n"
        liste.append((name, kx0, kx1, kz0, kz1, len(e)))
    # Alles nacheinander, mit Pausen, damit der Server nicht stockt
    for richtung in ("bau", "zurueck"):
        reihe = liste if richtung == "bau" else list(reversed(liste))
        for i, (name, *_r) in enumerate(reihe):
            weiter = "schedule function %s:%s_alles/%02d 20s" % (NS, richtung, i + 2) if i + 1 < len(reihe) else \
                "tellraw @a {\"text\":\"Campus: alle Abschnitte fertig (%s).\",\"color\":\"green\"}" % richtung
            dateien["data/%s/function/%s_alles/%02d.mcfunction" % (NS, richtung, i + 1)] = \
                "function %s:%s/%s\n%s\n" % (NS, richtung, name, weiter)
        dateien["data/%s/function/%s_alles.mcfunction" % (NS, richtung)] = "function %s:%s_alles/01\n" % (NS, richtung)
    dateien["data/%s/function/hilfe.mcfunction" % NS] = (
        "tellraw @s {\"text\":\"Campus-Bauhilfe: /function campus:bau/a01 … baut einen Abschnitt, "
        "/function campus:bau_alles baut alle nacheinander (20 s Pause). Rückgängig: campus:zurueck/aNN "
        "oder campus:zurueck_alles. Vorher ein Backup machen!\",\"color\":\"yellow\"}\n")
    dateien["pack.mcmeta"] = json.dumps({"pack": {"pack_format": 48, "description": "Tech-Campus: Bauhilfe für den Plan (umgebung-plan)"}}, ensure_ascii=False, indent=2) + "\n"

    ziel = REPO / "download/campus-bau-datapack.zip"
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as zf:
        for pfad in sorted(dateien):
            info = zipfile.ZipInfo(pfad, date_time=(2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, dateien[pfad])
    print("%s: %d Abschnitte, %.1f MB" % (ziel.relative_to(REPO), len(liste), ziel.stat().st_size / 1e6))
    schreibe_anleitung(liste, geschuetzt, sum(len(kacheln[k]) for k in kacheln))


def schreibe_anleitung(liste, geschuetzt, gesamt):
    gruppen = {}
    for x, z, was in geschuetzt:
        k = (x // 8 * 8, z // 8 * 8, was)
        gruppen[k] = gruppen.get(k, 0) + 1
    zeilen = ["# Bauhilfe Campus-Plan", "",
              "Erzeugt mit `tools/bauhilfe-campus.py` aus dem Plan im Branch `umgebung-plan`. "
              "Das Datapack baut den Plan Block für Block in eurer Welt: planieren, Hohlräume füllen, Wege, Plätze, "
              "Becken, Bäume, Blumen und die Lichter an den Gebäuden. Insgesamt %d Blöcke in %d Abschnitten." % (gesamt, len(liste)), "",
              "## Vorher", "",
              "1. **Backup der Welt machen.** Das Datapack kann zwar alles zurückbauen, aber Inhalte von Kisten und "
              "Maschinen in geänderten Blöcken kommen nicht zurück (es werden nur natürliche Blöcke ersetzt).",
              "2. Die Truhen der Unterwasser-Ruine im Südosten (bei 400–423 / −192 bis −168, Y 48–63) ausräumen, "
              "sie werden zugeschüttet.",
              "3. Ihr braucht OP-Rechte (oder Cheats in der Einzelspieler-Kopie zum Testen).", "",
              "## So geht's", "",
              "1. `download/campus-bau-datapack.zip` in den Ordner `world/datapacks` vom Server legen (die Zip, nicht entpacken).",
              "2. Im Spiel `/reload`, dann `/datapack list` zeigt `file/campus-bau-datapack.zip`.",
              "3. Erst einen Abschnitt testen: `/function campus:bau/a01`. Er lädt die Chunks selbst, baut und meldet „fertig“.",
              "4. Passt alles: `/function campus:bau_alles` baut alle Abschnitte nacheinander, mit 20 Sekunden Pause dazwischen.",
              "5. Gefällt etwas nicht: `/function campus:zurueck/aNN` für einen Abschnitt oder `/function campus:zurueck_alles`.",
              "6. Danach das Datapack wieder rausnehmen (`/datapack disable \"file/campus-bau-datapack.zip\"`).", "",
              "Die Mega Torches stehen nicht im Datapack, die setzt ihr von Hand (je etwa auf Y 64, unter der Oberfläche):", "",
              "| | X | Z | Versteck |", "| --- | --- | --- | --- |"]
    for name, x, z, wo in PLAN.MEGA_TORCHES:
        zeilen.append("| %s | %d | %d | %s |" % (name, x, z, wo))
    zeilen += ["", "## Abschnitte", "", "| Funktion | x | z | Blöcke |", "| --- | --- | --- | --- |"]
    for name, kx0, kx1, kz0, kz1, n in liste:
        zeilen.append("| `campus:bau/%s` | %d … %d | %d … %d | %d |" % (name, kx0, kx1, kz0, kz1, n))
    zeilen += ["", "## Geschützte Stellen", "",
               "Hier steht etwas von euch, das nicht zum Plan gehört. Diese Spalten fasst das Datapack nicht an, "
               "dort bleibt es so, wie es ist. Entweder von Hand angleichen oder abbauen und das Skript neu laufen lassen.", "",
               "| Bereich (x, z, je 8 × 8) | Block | Spalten |", "| --- | --- | --- |"]
    for (x, z, was), n in sorted(gruppen.items()):
        zeilen.append("| %d, %d | %s | %d |" % (x, z, was, n))
    zeilen += ["", "## Grenzen", "",
               "- Die Schematic reicht nur bis Y 45. Höhlen tiefer als Y 45 bleiben, wie sie sind.",
               "- Gefüllt wird mit Dirt (die drei Blöcke unter der Oberfläche) und Stone darunter.",
               "- Die Bäume sind einfache Vorlagen mit Blättern, die nicht verwelken (persistent).", ""]
    (REPO / "gebaeude/aussenanlagen/bauhilfe.md").write_text("\n".join(zeilen), encoding="utf-8")
    print("gebaeude/aussenanlagen/bauhilfe.md geschrieben, %d geschützte Spalten" % len(geschuetzt))


if __name__ == "__main__":
    main()
