"""Erzeugt modell.json (Blockmodell für die Website) aus einer Create-Schematic (.nbt).

Nutzung:  python3 tools/modell-aus-schematic.py gebaeude/me-zentrale
Braucht:  nur Python 3, keine Zusatzpakete

Liest die Schematic aus gebaeude.json (dateien.schematic, Pfad relativ zum Repo)
und schreibt modell.json in den Gebäudeordner. Koordinaten bleiben so, wie sie in
der Schematic stehen: die Ecke, die beim Speichern als erste angeklickt wurde, ist
(0, 0, 0). Farben kommen aus der Tabelle FARBEN unten, unbekannte Blöcke bekommen
eine feste Ersatzfarbe aus ihrem Namen. Framed Blocks nehmen die Farbe ihres Camo-Blocks.
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
KLEIN = {"ae2:cable_bus", "minecraft:chain"}

# Schöne Namen, so wie sie im Spiel heißen
NAMEN = {
    "ae2:cable_bus": "ME Cable / Parts",
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
    "ae2:cable_bus": "#6b4fa3",
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
        x, y, z = b["pos"]
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
    unbekannt = sorted({s["id"].split("|")[-1] for s in sorten} - set(FARBEN))
    if unbekannt:
        print("Ohne eigene Farbe (Ersatzfarbe benutzt):", ", ".join(unbekannt))


if __name__ == "__main__":
    main()
