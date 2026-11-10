"""Erzeugt modell.json (Blockmodell für die Website) aus einer Create-Schematic (.nbt).

Nutzung:  python3 tools/modell-aus-schematic.py gebaeude/me-zentrale
Braucht:  nur Python 3, keine Zusatzpakete

Liest die Schematic aus gebaeude.json (dateien.schematic, Pfad relativ zum Repo)
und schreibt modell.json in den Gebäudeordner. Koordinaten bleiben so, wie sie in
der Schematic stehen: (0, 0, 0) ist die Ecke der Auswahl mit dem kleinsten x, y und z,
also unten im Nordwesten. Create speichert ungedreht, die Schematic liegt also so wie in der Welt. Farben kommen aus der Tabelle FARBEN unten, unbekannte Blöcke bekommen
eine feste Ersatzfarbe aus ihrem Namen. Framed Blocks nehmen die Farbe ihres Camo-Blocks.
AE2-Kabel werden mit ihren Verbindungen gespeichert ([x, y, z, sorte, maske], Bits
in der Reihenfolge RICHTUNGEN), damit die Website sie als Stränge zeichnen kann.
"""
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Blöcke, die man nicht sieht und die deshalb nicht ins Modell kommen
UNSICHTBAR = {
    "minecraft:air", "minecraft:cave_air", "minecraft:void_air",
    "minecraft:light", "minecraft:structure_void", "minecraft:barrier",
    "ars_nouveau:light_block", "evilcraft:blood_stain",
}

# Kleine oder dünne Blöcke, die als schmaler Klotz gezeichnet werden
KLEIN = {"minecraft:chain"}

# AE2-Kabel: Dicke im Modell (1 = ganzer Block) und Farben je Kabelfarbe
KABEL_DICKE = {"dense": 0.5, "smart": 0.3, "covered": 0.3, "glass": 0.22}
KABEL_FARBE = {
    "white": "#e9ecec", "orange": "#f07613", "magenta": "#bd44b3", "light_blue": "#3aafd9",
    "yellow": "#f8c527", "lime": "#70b919", "pink": "#ed8dac", "gray": "#3e4447",
    "light_gray": "#8e8e86", "cyan": "#158991", "purple": "#792aac", "blue": "#3c4fc4",
    "brown": "#724728", "green": "#546d1b", "red": "#a12722", "black": "#1d1d21",
    "fluix": "#6b4fa3",
}
# Reihenfolge der Bits in der Verbindungsmaske (5. Wert im Block)
RICHTUNGEN = ["down", "up", "north", "south", "west", "east"]

# Schöne Namen, so wie sie im Spiel heißen
NAMEN = {
    "ae2:controller": "ME Controller",
    "extendedae:ex_drive": "ME Extended Drive",
    "extendedae:wireless_connect": "ME Wireless Connector",
    "extendedae:wireless_hub": "ME Wireless Hub",
    "powah:ender_gate_nitro": "Ender Gate (Nitro)",
}

FARBEN = {
    "minecraft:white_concrete": "#cfd5d6",
    "minecraft:light_gray_concrete": "#7d7d73",
    "minecraft:gray_concrete": "#36393d",
    "minecraft:black_concrete": "#08090e",
    "minecraft:light_blue_concrete": "#2389c6",
    "minecraft:blue_concrete": "#2c2e8f",
    "minecraft:black_stained_glass": "#191919",
    "minecraft:glass": "#c0d8de",
    "minecraft:stone": "#7e7e7e",
    "minecraft:grass_block": "#5d8f3a",
    "minecraft:dirt": "#866043",
    "minecraft:sandstone": "#d8cb9b",
    "minecraft:coal_ore": "#6a6a6a",
    "minecraft:chain": "#3c4150",
    "alltheores:cinnabar_ore": "#8e5a55",
    "chipped:blue_concrete_tiles": "#30338f",
    "chipped:light_gray_concrete_tiles": "#82827a",
    "chipped:cut_calcite_column": "#dfe0dc",
    "ae2:controller": "#8f7fc9",
    "extendedae:ex_drive": "#5b5f6b",
    "extendedae:wireless_connect": "#4fa3a0",
    "extendedae:wireless_hub": "#3fc4c0",
    "powah:ender_gate_nitro": "#2a6b5f",
}


# --- NBT lesen ---------------------------------------------------------------

def lies_nbt(daten):
    pos = 0

    def nimm(fmt):
        nonlocal pos
        werte = struct.unpack_from(">" + fmt, daten, pos)
        pos += struct.calcsize(">" + fmt)
        return werte[0]

    def text():
        nonlocal pos
        n = nimm("H")
        s = daten[pos:pos + n].decode("utf-8", "replace")
        pos += n
        return s

    def wert(typ):
        nonlocal pos
        if typ == 1: return nimm("b")
        if typ == 2: return nimm("h")
        if typ == 3: return nimm("i")
        if typ == 4: return nimm("q")
        if typ == 5: return nimm("f")
        if typ == 6: return nimm("d")
        if typ == 7:
            n = nimm("i"); pos += n; return None
        if typ == 8: return text()
        if typ == 9:
            t = nimm("b"); n = nimm("i")
            return [wert(t) for _ in range(n)]
        if typ == 10:
            d = {}
            while True:
                t = nimm("b")
                if t == 0: return d
                name = text()
                d[name] = wert(t)
        if typ == 11:
            n = nimm("i"); return [nimm("i") for _ in range(n)]
        if typ == 12:
            n = nimm("i"); pos += 8 * n; return None
        raise ValueError(f"Unbekannter NBT-Typ {typ}")

    if nimm("b") != 10:
        raise ValueError("Keine NBT-Datei")
    text()
    return wert(10)


def lade_schematic(pfad):
    roh = Path(pfad).read_bytes()
    if roh[:2] == b"\x1f\x8b":
        roh = gzip.decompress(roh)
    return lies_nbt(roh)


# --- Farben und Namen ---------------------------------------------------------

def ersatzfarbe(name):
    h = hashlib.md5(name.encode()).digest()
    return "#%02x%02x%02x" % (90 + h[0] % 120, 90 + h[1] % 120, 90 + h[2] % 120)


def schoener_name(name):
    if name in NAMEN:
        return NAMEN[name]
    return name.split(":", 1)[-1].replace("_", " ").title()


def camo_von(block):
    nbt = block.get("nbt") or {}
    for schluessel in sorted(nbt):
        if schluessel.startswith("camo") and isinstance(nbt[schluessel], dict):
            state = nbt[schluessel].get("state") or {}
            if state.get("Name"):
                return state["Name"]
    return None


def kabel_von(block):
    """Kabelsorte und Verbindungsmaske eines ae2:cable_bus, oder None ohne Kabel."""
    kabel = (block.get("nbt") or {}).get("cable")
    if not isinstance(kabel, dict) or not kabel.get("id"):
        return None
    kid = kabel["id"]
    rest = kid.split(":", 1)[-1].replace("_cable", "")
    dicke = 0.3
    for art, d in KABEL_DICKE.items():
        if art in rest:
            dicke = d
            rest = rest.replace("_" + art, "").replace(art, "")
            break
    if "dense" in kid:
        dicke = KABEL_DICKE["dense"]
        rest = rest.replace("_dense", "").replace("dense", "")
    farbe = KABEL_FARBE.get(rest.strip("_") or "fluix", KABEL_FARBE["fluix"])
    verb = (kabel.get("visual") or {}).get("connections") or []
    maske = sum(1 << i for i, r in enumerate(RICHTUNGEN) if r in verb)
    return kid, dicke, farbe, maske


def main():
    ordner = Path(sys.argv[1] if len(sys.argv) > 1 else "gebaeude/me-zentrale")
    geb = json.loads((ordner / "gebaeude.json").read_text(encoding="utf-8"))
    quelle = geb["dateien"].get("schematic")
    if not quelle:
        sys.exit(f"In {ordner}/gebaeude.json fehlt dateien.schematic")
    nbt = lade_schematic(REPO / quelle)

    palette = nbt.get("palette") or nbt["palettes"][0]
    sorten, index, bloecke = [], {}, []
    for b in nbt["blocks"]:
        name = palette[b["state"]]["Name"]
        if name in UNSICHTBAR:
            continue
        x, y, z = b["pos"]
        if name == "ae2:cable_bus":
            k = kabel_von(b)
            if not k:
                continue
            kid, dicke, farbe, maske = k
            if kid not in index:
                index[kid] = len(sorten)
                sorten.append({"id": kid, "name": schoener_name(kid), "farbe": farbe,
                               "transparent": False, "klein": False, "form": "kabel", "dicke": dicke})
            bloecke.append([x, y, z, index[kid], maske])
            continue
        camo = camo_von(b) if name.startswith("framedblocks:") else None
        sid = name + ("|" + camo if camo else "")
        if sid not in index:
            index[sid] = len(sorten)
            anzeige = schoener_name(name) + (f" ({schoener_name(camo)})" if camo else "")
            farbquelle = camo or name
            sorten.append({
                "id": sid,
                "name": anzeige,
                "farbe": FARBEN.get(farbquelle) or ersatzfarbe(farbquelle),
                "transparent": "glass" in farbquelle and "pane" not in farbquelle,
                "klein": name in KLEIN,
            })
        bloecke.append([x, y, z, index[sid]])
    bloecke.sort(key=lambda b: (b[1], b[2], b[0]))

    ziel = ordner / "modell.json"
    with ziel.open("w", encoding="utf-8") as f:
        f.write('{"quelle":' + json.dumps(quelle) + ',"groesse":' + json.dumps(nbt.get("size")) + ',"palette":')
        json.dump(sorten, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")
    print(f"{ziel}: {len(bloecke)} Blöcke, {len(sorten)} Sorten, Größe {nbt.get('size')}")
    unbekannt = sorted({s["id"].split("|")[-1] for s in sorten if s.get("form") != "kabel"} - set(FARBEN))
    if unbekannt:
        print("Ohne eigene Farbe (Ersatzfarbe benutzt):", ", ".join(unbekannt))


if __name__ == "__main__":
    main()
