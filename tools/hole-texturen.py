"""Holt die Blocktexturen für die 3D-Ansicht aus der Minecraft-Instanz.

Nutzung:  python3 tools/hole-texturen.py [INSTANZ-ORDNER]
Ergebnis: texturen/atlas.png und texturen/texturen.json

Das Skript sammelt alle Block-IDs aus gebaeude/*/modell.json und sucht nur deren
Texturen: Vanilla aus der Minecraft-Client-Jar (Prism legt sie unter libraries/ ab),
alles andere aus den Mod-Jars in minecraft/mods/. Der Weg ist derselbe wie im Spiel:
Blockstate -> Blockmodell (mit Parent-Kette) -> Textur je Seite. So bekommen Logs,
Grass Block und Co. oben, unten und an der Seite die richtige Textur.

- IDs mit "platzhalter:" werden übersprungen, die bleiben einfarbig.
- Framed Blocks wie "framedblocks:framed_panel|minecraft:white_concrete" bekommen
  die Textur der Tarnung hinter dem "|".
- Texturen, die im Spiel nach Biom eingefärbt werden (Gras, Laub, Wasser), werden
  mit der Ebenen-Farbe eingefärbt gespeichert.
- Animierte Texturen: nur das erste Bild.

Ohne Zusatzpakete, PNG lesen und schreiben läuft über zlib aus der Standardbibliothek.
"""
import json
import struct
import sys
import zipfile
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZIEL = REPO / "texturen"
STANDARD_INSTANZ = Path.home() / ".var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/All the Mods 10 Aeronautics ATM10A"

KACHEL = 16          # jede Textur wird auf 16 x 16 Pixel gebracht
RAND = 8             # Rand um jede Kachel (Textur wiederholt), gegen Farbbluten bei Mipmaps
ZELLE = KACHEL + 2 * RAND
SEITEN = ["up", "down", "north", "south", "west", "east"]

# Biomfarben wie in den Plains
FARBE_GRAS = (0x91, 0xBD, 0x59)
FARBE_LAUB = (0x77, 0xAB, 0x2F)
FARBE_WASSER = (0x3F, 0x76, 0xE4)


# ---------------------------------------------------------------- PNG

def png_lesen(daten):
    """PNG-Bytes -> (breite, hoehe, [r,g,b,a, ...]). Kann alle üblichen Farbtypen ohne Interlace."""
    if daten[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("keine PNG")
    pos, idat, plte, trns = 8, b"", None, None
    while pos < len(daten):
        laenge, art = struct.unpack(">I4s", daten[pos:pos + 8])
        inhalt = daten[pos + 8:pos + 8 + laenge]
        pos += 12 + laenge
        if art == b"IHDR":
            w, h, tiefe, typ, _, _, interlace = struct.unpack(">IIBBBBB", inhalt)
        elif art == b"PLTE":
            plte = inhalt
        elif art == b"tRNS":
            trns = inhalt
        elif art == b"IDAT":
            idat += inhalt
        elif art == b"IEND":
            break
    if interlace:
        raise ValueError("Interlace nicht unterstützt")
    kanaele = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[typ]
    bits = kanaele * tiefe
    bpp = max(1, bits // 8)
    zeile = (w * bits + 7) // 8
    roh = zlib.decompress(idat)
    zeilen, vorher, p = [], bytearray(zeile), 0
    for _ in range(h):
        f = roh[p]
        z = bytearray(roh[p + 1:p + 1 + zeile])
        p += 1 + zeile
        for i in range(zeile):
            a = z[i - bpp] if i >= bpp else 0
            b = vorher[i]
            c = vorher[i - bpp] if i >= bpp else 0
            if f == 1:
                z[i] = (z[i] + a) & 255
            elif f == 2:
                z[i] = (z[i] + b) & 255
            elif f == 3:
                z[i] = (z[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                z[i] = (z[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        zeilen.append(z)
        vorher = z

    def werte(z):
        """Zeile in Kanalwerte 0..255 (bzw. Palettenindex) zerlegen."""
        if tiefe == 8:
            return list(z)
        if tiefe == 16:
            return [z[i] for i in range(0, len(z), 2)]
        maske, out = (1 << tiefe) - 1, []
        for byte in z:
            for s in range(8 - tiefe, -1, -tiefe):
                out.append((byte >> s) & maske)
        return out

    px = []
    for z in zeilen:
        v = werte(z)[:w * kanaele]
        for x in range(w):
            if typ == 3:
                i = v[x]
                r, g, b = plte[i * 3:i * 3 + 3]
                a = trns[i] if trns and i < len(trns) else 255
            elif typ == 0:
                g0 = v[x] * 255 // ((1 << tiefe) - 1) if tiefe < 8 else v[x]
                r = g = b = g0
                a = 255
            elif typ == 4:
                r = g = b = v[x * 2]
                a = v[x * 2 + 1]
            elif typ == 2:
                r, g, b = v[x * 3:x * 3 + 3]
                a = 255
            else:
                r, g, b, a = v[x * 4:x * 4 + 4]
            px += [r, g, b, a]
    return w, h, px


def png_schreiben(w, h, px):
    roh = bytearray()
    for y in range(h):
        roh.append(0)
        roh += bytes(px[y * w * 4:(y + 1) * w * 4])

    def chunk(art, inhalt):
        return struct.pack(">I", len(inhalt)) + art + inhalt + struct.pack(">I", zlib.crc32(art + inhalt) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(roh), 9)) + chunk(b"IEND", b""))


def auf_kachel(w, h, px):
    """Erstes Animationsbild nehmen und per Nearest auf KACHEL x KACHEL bringen."""
    h = min(h, w)  # animierte Texturen: Bilder stehen untereinander
    out = []
    for y in range(KACHEL):
        sy = y * h // KACHEL
        for x in range(KACHEL):
            sx = x * w // KACHEL
            out += px[(sy * w + sx) * 4:(sy * w + sx) * 4 + 4]
    return out


# ---------------------------------------------------------------- Ressourcen

class Ressourcen:
    """Findet assets/... in Client-Jar und Mod-Jars. Vanilla hat Vorrang für minecraft:."""

    def __init__(self, instanz):
        self.jars = []
        self.wo = {}
        client = self.client_jar(instanz)
        print(f"Client-Jar: {client}")
        jars = [client] + sorted((instanz / "minecraft" / "mods").glob("*.jar"))
        for j in jars:
            try:
                z = zipfile.ZipFile(j)
            except zipfile.BadZipFile:
                continue
            self.jars.append(z)
            for name in z.namelist():
                if name.startswith("assets/") and name not in self.wo:
                    self.wo[name] = z
        print(f"{len(jars)} Jars durchsucht, {len(self.wo)} Dateien unter assets/")

    @staticmethod
    def client_jar(instanz):
        version = "1.21.1"
        pack = instanz / "mmc-pack.json"
        if pack.exists():
            for k in json.loads(pack.read_text(encoding="utf-8"))["components"]:
                if k.get("uid") == "net.minecraft":
                    version = k["version"]
        libs = instanz.parent.parent / "libraries"
        jar = libs / "com" / "mojang" / "minecraft" / version / f"minecraft-{version}-client.jar"
        if jar.exists():
            return jar
        treffer = sorted(libs.rglob(f"minecraft-{version}-client.jar"))
        if not treffer:
            sys.exit(f"Minecraft-Client-Jar {version} nicht unter {libs} gefunden. Spiel einmal in Prism starten.")
        return treffer[0]

    def lies(self, pfad):
        z = self.wo.get(pfad)
        return z.read(pfad) if z else None

    def json(self, pfad):
        d = self.lies(pfad)
        return json.loads(d.decode("utf-8-sig")) if d else None


def ns_pfad(name, standard="minecraft"):
    if ":" in name:
        ns, p = name.split(":", 1)
    else:
        ns, p = standard, name
    return ns, p


# ---------------------------------------------------------------- Blockstate -> Modell -> Textur

DREH_Y = {"north": "east", "east": "south", "south": "west", "west": "north", "up": "up", "down": "down"}
DREH_X = {"up": "north", "north": "down", "down": "south", "south": "up", "east": "east", "west": "west"}


NAMEN_JE_SEITE = {
    "up": ["up", "top", "end", "all"],
    "down": ["down", "bottom", "end", "all"],
    "north": ["north", "front", "sides", "side", "all"],
    "south": ["south", "sides", "side", "all"],
    "west": ["west", "sides", "side", "all"],
    "east": ["east", "sides", "side", "all"],
}

# Blöcke, deren Modell erst im Spiel per Code entsteht. Werte: Textur für alle Seiten
# oder {seite: textur}, "seite" steht für alle vier Seitenflächen.
SONDERFAELLE = {
    "extendedae:ex_drive": {"up": "extendedae:block/extended_drive/ex_drive_top",
                            "down": "extendedae:block/extended_drive/ex_drive_bottom",
                            "seite": "extendedae:block/extended_drive/ex_drive_side"},
}
for _farbe in ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray",
               "cyan", "purple", "blue", "brown", "green", "red", "black", "fluix"):
    # AE2-Kabel sind Parts ohne Blockmodell
    SONDERFAELLE[f"ae2:{_farbe}_smart_cable"] = f"ae2:part/cable/smart/{_farbe}"
    SONDERFAELLE[f"ae2:{_farbe}_smart_dense_cable"] = f"ae2:part/cable/dense_smart/{_farbe}"
    SONDERFAELLE[f"ae2:{_farbe}_covered_cable"] = f"ae2:part/cable/covered/{_farbe}"
    SONDERFAELLE[f"ae2:{_farbe}_covered_dense_cable"] = f"ae2:part/cable/dense_covered/{_farbe}"
    SONDERFAELLE[f"ae2:{_farbe}_glass_cable"] = f"ae2:part/cable/glass/{_farbe}"


def variante_waehlen(blockstate):
    """Eine Variante aus dem Blockstate: am liebsten senkrecht, unten, ungedreht."""
    if "variants" in blockstate:
        vorlieben = ["axis=y", "half=lower", "half=bottom", "type=bottom", "facing=north", "facing=up", "open=false", "powered=false", "lit=false"]
        def punkte(paar):
            k, v = paar
            v = v[0] if isinstance(v, list) else v
            s = sum(2 for t in vorlieben if t in k.split(","))
            return s - (1 if v.get("x") or v.get("y") else 0)
        k, v = max(blockstate["variants"].items(), key=punkte)
        return [v[0] if isinstance(v, list) else v]
    if "multipart" in blockstate:
        teile = [t["apply"] for t in blockstate["multipart"] if "when" not in t]
        if not teile:
            teile = [blockstate["multipart"][0]["apply"]]
        return [t[0] if isinstance(t, list) else t for t in teile]
    return []


def modell_laden(res, name):
    """Modell mit aufgelöster Parent-Kette: (texturen, elemente)."""
    texturen, elemente, gesehen = {}, None, set()
    while name and name not in gesehen:
        gesehen.add(name)
        if name.startswith("builtin/"):
            break
        ns, p = ns_pfad(name)
        m = res.json(f"assets/{ns}/models/{p}.json")
        if m is None:
            break
        for k, v in (m.get("textures") or {}).items():
            texturen.setdefault(k, v)
        if m.get("loader") and not m.get("textures"):
            # eigene Loader (z. B. Modular Bees) haben die Texturen direkt im Modell
            for k, v in m.items():
                if k not in ("loader", "parent") and isinstance(v, str) and ":" in v:
                    texturen.setdefault(k, v)
        if elemente is None and m.get("elements"):
            elemente = m["elements"]
        name = m.get("parent")
    return texturen, elemente or []


def textur_aufloesen(texturen, ref):
    for _ in range(10):
        if ref is None:
            return None
        if not ref.startswith("#"):
            return ref
        ref = texturen.get(ref[1:])
    return None


def seiten_aus_modell(res, ref):
    """{seite: (texturname, getönt)} für ein Modell aus einer Blockstate-Variante."""
    texturen, elemente = modell_laden(res, ref["model"])
    seiten = {}
    for s in SEITEN:
        best, flaeche = None, -1
        for e in elemente:
            f = (e.get("faces") or {}).get(s)
            if not f:
                continue
            a, b = e.get("from", [0, 0, 0]), e.get("to", [16, 16, 16])
            d = [abs(b[i] - a[i]) for i in range(3)]
            fl = d[0] * d[2] if s in ("up", "down") else d[0] * d[1] if s in ("north", "south") else d[1] * d[2]
            if fl > flaeche:
                best, flaeche = f, fl
        if best:
            t = textur_aufloesen(texturen, best.get("texture"))
            if t:
                seiten[s] = (t, "tintindex" in best)
    # Modelle ohne Elemente: erst Texturnamen wie "up", "top", "side" ...
    if not elemente:
        for s in SEITEN:
            for k in NAMEN_JE_SEITE[s]:
                t = textur_aufloesen(texturen, "#" + k)
                if t:
                    seiten[s] = (t, False)
                    break
    # ... sonst (Wasser, BER, OBJ) Partikel oder irgendeine Textur
    rest = textur_aufloesen(texturen, "#particle") or next((textur_aufloesen(texturen, v) for v in texturen.values() if textur_aufloesen(texturen, v)), None)
    for s in SEITEN:
        if s not in seiten and rest:
            seiten[s] = (rest, False)
    # Drehung der Variante: erst x, dann y
    for _ in range((ref.get("x", 0) // 90) % 4):
        seiten = {DREH_X[s]: v for s, v in seiten.items()}
    for _ in range((ref.get("y", 0) // 90) % 4):
        seiten = {DREH_Y[s]: v for s, v in seiten.items()}
    return seiten


def seiten_fuer_block(res, block_id):
    sonder = SONDERFAELLE.get(block_id)
    if sonder:
        if isinstance(sonder, str):
            return {s: (sonder, False) for s in SEITEN}
        return {s: (sonder.get(s) or sonder["seite"], False) for s in SEITEN}
    ns, p = ns_pfad(block_id)
    bs = res.json(f"assets/{ns}/blockstates/{p}.json")
    seiten = {}
    if bs:
        for ref in variante_waehlen(bs):
            if "model" in ref:
                for s, v in seiten_aus_modell(res, ref).items():
                    seiten.setdefault(s, v)
    if not seiten:
        # ohne Blockstate: Blockmodell oder Textur gleichen Namens
        texturen, _ = modell_laden(res, f"{ns}:block/{p}")
        if texturen:
            seiten = seiten_aus_modell(res, {"model": f"{ns}:block/{p}"})
        elif res.lies(f"assets/{ns}/textures/block/{p}.png"):
            seiten = {s: (f"{ns}:block/{p}", False) for s in SEITEN}
    return seiten


HOLZ = ["dark_oak", "oak", "spruce", "birch", "jungle", "acacia", "mangrove", "cherry", "bamboo", "crimson", "warped"]


def mittelfarbe(res, textur):
    ns, p = ns_pfad(textur)
    daten = res.lies(f"assets/{ns}/textures/{p}.png")
    if not daten:
        return None
    _, _, px = png_lesen(daten)
    n = len(px) // 4
    farbe = [sum(px[i::4]) / n for i in range(3)]
    hell = max(farbe) or 1
    return tuple(int(c * 255 / hell) for c in farbe)


def toenung(res, block_id, textur):
    # Productive Bees färbt seine grauen Bienenstöcke in der Holzfarbe ein
    if "tinted/" in textur:
        for holz in HOLZ:
            if f"/{holz}/" in textur or f"_{holz}" in block_id:
                f = mittelfarbe(res, f"minecraft:block/{holz}_planks")
                if f:
                    return f
    if "water" in block_id or "water" in textur:
        return FARBE_WASSER
    if "leaves" in block_id or "leaves" in textur or "vine" in textur:
        return FARBE_LAUB
    return FARBE_GRAS


# ---------------------------------------------------------------- Hauptteil

def block_ids():
    ids = set()
    for datei in sorted((REPO / "gebaeude").glob("*/modell.json")):
        for p in json.loads(datei.read_text(encoding="utf-8"))["palette"]:
            ids.add(p["id"])
    return sorted(ids)


def main():
    instanz = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else STANDARD_INSTANZ
    if not (instanz / "minecraft" / "mods").is_dir():
        sys.exit(f"Kein Instanzordner mit minecraft/mods: {instanz}")
    res = Ressourcen(instanz)

    kacheln = {}        # schluessel -> (pixel, alpha)
    bloecke, fehlt = {}, []
    for pid in block_ids():
        if pid.startswith("platzhalter:"):
            continue
        quelle = pid.split("|")[-1]  # Framed Blocks: Textur der Tarnung
        seiten = seiten_fuer_block(res, quelle)
        eintrag = {}
        for s in SEITEN:
            if s not in seiten:
                continue
            name, getoent = seiten[s]
            ns, p = ns_pfad(name)
            schluessel = f"{ns}:{p}" + ("#getoent" if getoent else "")
            if schluessel not in kacheln:
                daten = res.lies(f"assets/{ns}/textures/{p}.png")
                if daten is None:
                    continue
                try:
                    px = auf_kachel(*png_lesen(daten))
                except Exception as e:  # kaputte oder exotische PNG
                    print(f"  {name}: {e}")
                    continue
                if getoent:
                    f = toenung(res, quelle, p)
                    for i in range(0, len(px), 4):
                        px[i], px[i + 1], px[i + 2] = (px[i] * f[0] // 255, px[i + 1] * f[1] // 255, px[i + 2] * f[2] // 255)
                alphas = set(px[3::4])
                alpha = "halb" if any(0 < a < 255 for a in alphas) else "loch" if 0 in alphas else "voll"
                kacheln[schluessel] = (px, alpha)
            eintrag[s] = schluessel
        if len(eintrag) == len(SEITEN):
            bloecke[pid] = eintrag
        else:
            fehlt.append(pid)

    # Atlas: Zellen mit wiederholtem Rand, Kantenlänge Zweierpotenz
    namen = sorted(kacheln)
    spalten = 1
    while spalten * spalten < len(namen):
        spalten *= 2
    breite = spalten * ZELLE
    zeilen = (len(namen) + spalten - 1) // spalten
    hoehe = 1
    while hoehe < zeilen * ZELLE:
        hoehe *= 2
    atlas = bytearray(breite * hoehe * 4)
    for i, n in enumerate(namen):
        px = kacheln[n][0]
        ox, oy = (i % spalten) * ZELLE, (i // spalten) * ZELLE
        for y in range(ZELLE):
            sy = (y - RAND) % KACHEL
            for x in range(ZELLE):
                sx = (x - RAND) % KACHEL
                q, z = (sy * KACHEL + sx) * 4, ((oy + y) * breite + ox + x) * 4
                atlas[z:z + 4] = bytes(px[q:q + 4])

    ZIEL.mkdir(exist_ok=True)
    (ZIEL / "atlas.png").write_bytes(png_schreiben(breite, hoehe, atlas))
    zuordnung = {
        "quelle": "tools/hole-texturen.py aus der Instanz All the Mods 10 Aeronautics (Minecraft 1.21.1)",
        "atlas": "atlas.png",
        "groesse": [breite, hoehe],
        "kachel": KACHEL,
        "rand": RAND,
        "spalten": spalten,
        "texturen": {n: {"nr": i, "alpha": kacheln[n][1]} for i, n in enumerate(namen)},
        "bloecke": bloecke,
    }
    (ZIEL / "texturen.json").write_text(json.dumps(zuordnung, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"texturen/atlas.png: {breite} x {hoehe}, {len(namen)} Texturen, {len(bloecke)} Blöcke")
    if fehlt:
        print("Ohne Textur (bleiben einfarbig): " + ", ".join(fehlt))


if __name__ == "__main__":
    main()
