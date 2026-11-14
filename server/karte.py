"""Karte aktualisieren: Schematic-Import mit Vorschau, Versionen und Zurücksetzen.

Ablauf beim Import:
  1. Hochladen: Größe begrenzt (gepackt und entpackt), die Datei wird nur gelesen und
     vollständig auf gültiges NBT geprüft, bevor irgendein Skript sie anfasst.
  2. Vorschau: In einem eigenen Git-Worktree unter DATEN/import/arbeit laufen die
     vorhandenen Skripte (tools/modell-aus-schematic.py und die Entwurfs-Skripte).
     Das Repo selbst bleibt unberührt. Verglichen wird pro Gebäude alt gegen neu.
  3. Übernehmen: Ist seit der Vorschau nichts dazwischengekommen, was die Karte betrifft,
     wird die Zip neu gebaut und alles als ein Commit geschrieben und gepusht.
Es läuft immer nur ein Import gleichzeitig. Eine liegen gelassene Vorschau verfällt nach
30 Minuten, dann darf jemand anderes.

Zurücksetzen stellt nur die Karte wieder her (Schematic, Modelle, Ausschnitte und Quelle
pro Gebäude, Zip), als neuer Commit. Kanban, Profile und Code bleiben, wie sie sind.
"""
import gzip
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import zlib
from pathlib import Path

from fehler import Fehler

MAX_UPLOAD = 20 * 1024 * 1024          # hochgeladene Datei (gepackt)
MAX_ENTPACKT = 256 * 1024 * 1024       # entpackte NBT-Daten
MAX_ELEMENTE = 20 * 1000 * 1000        # Werte im NBT insgesamt
MAX_TIEFE = 32                          # Verschachtelung im NBT
MAX_BLOECKE = 3 * 1000 * 1000           # Blöcke in der Schematic
MAX_KANTE = 2048                        # größte Kantenlänge der Schematic
ABLAUF = 30 * 60                        # so lange gehört eine Vorschau einer Person
SKRIPT_ZEIT = 300                       # Sekunden pro Skript
WARN_ANTEIL = 0.2                       # Warnung, wenn ein Gebäude mehr als 20 % verliert

SCHEMATIC = "schematics/campus.nbt"
AUSSEN_SKRIPT = "tools/modell-aussenanlagen.py"
GELAENDE = "campus/gelaende.json"          # Gelände für die Map, nur neu berechnet, wenn es die Datei schon gibt
GELAENDE_SKRIPT = "tools/modell-gelaende.py"
NICHT_AUF_DEM_SERVER = {"tools/modell-aus-bauplan.py"}   # braucht Playwright
DARF_AENDERN = ("gebaeude/", "schematics/", "download/", GELAENDE)
# Ändert sich davon etwas zwischen Vorschau und Übernehmen, muss die Vorschau neu
BETRIFFT_KARTE = ("gebaeude/", "schematics/", "campus/", "tools/", "texturen/", "download/", "website/js/voxel.js")
# Woran man in einer Schematic Gebautes von Natur unterscheidet
GEBAUT = re.compile(r"concrete|glass|planks|brick|quartz|terracotta|stairs|slab|wall|fence|lantern|lamp|"
                    r"iron_block|copper|smooth|polished|wool|carpet|door|chain|framed")


# --- NBT sicher lesen ---------------------------------------------------------

def entpacken(roh):
    """gzip entpacken, aber nie mehr als MAX_ENTPACKT Byte (Schutz vor Zip-Bomben)."""
    if roh[:2] != b"\x1f\x8b":
        if len(roh) > MAX_ENTPACKT:
            raise Fehler(413, "Die Datei ist zu groß.")
        return roh
    teile, n = [], 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(roh)) as f:
            while True:
                stueck = f.read(1024 * 1024)
                if not stueck:
                    break
                n += len(stueck)
                if n > MAX_ENTPACKT:
                    raise Fehler(413, "Entpackt ist die Schematic größer als %d MB, das nehmen wir nicht an." % (MAX_ENTPACKT // 1024 // 1024))
                teile.append(stueck)
    except (OSError, EOFError, zlib.error):
        raise Fehler(400, "Die Datei ist kein gültiges gzip, also keine Create-Schematic.")
    return b"".join(teile)


_MINDEST = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8, 7: 4, 8: 2, 9: 5, 10: 1, 11: 4, 12: 4}


def lies_nbt_sicher(daten):
    """NBT lesen wie tools/modell-aus-schematic.py, aber mit Grenzen für Tiefe, Längen und
    Gesamtzahl. Byte- und Long-Arrays werden übersprungen. Wirft Fehler(400) bei Unsinn."""
    pos = 0
    ende = len(daten)
    budget = [MAX_ELEMENTE]

    def nimm(fmt, groesse):
        nonlocal pos
        if pos + groesse > ende:
            raise ValueError("Datei endet zu früh")
        w = struct.unpack_from(">" + fmt, daten, pos)[0]
        pos += groesse
        return w

    def zaehle(n):
        budget[0] -= n
        if budget[0] < 0:
            raise ValueError("zu viele Werte")

    def laenge(n, typ):
        if n < 0 or n * _MINDEST.get(typ, 1) > ende - pos:
            raise ValueError("ungültige Länge")
        zaehle(n)

    def text():
        nonlocal pos
        n = nimm("H", 2)
        if pos + n > ende:
            raise ValueError("Datei endet zu früh")
        s = daten[pos:pos + n].decode("utf-8", "replace")
        pos += n
        return s

    def wert(typ, tiefe):
        nonlocal pos
        if tiefe > MAX_TIEFE:
            raise ValueError("zu tief verschachtelt")
        zaehle(1)
        if typ == 1: return nimm("b", 1)
        if typ == 2: return nimm("h", 2)
        if typ == 3: return nimm("i", 4)
        if typ == 4: return nimm("q", 8)
        if typ == 5: return nimm("f", 4)
        if typ == 6: return nimm("d", 8)
        if typ == 7:
            n = nimm("i", 4); laenge(n, 1); pos += n; return None
        if typ == 8: return text()
        if typ == 9:
            t = nimm("b", 1); n = nimm("i", 4)
            if t == 0 and n > 0 or not 0 <= t <= 12:
                raise ValueError("ungültige Liste")
            laenge(n, t)
            return [wert(t, tiefe + 1) for _ in range(n)]
        if typ == 10:
            d = {}
            while True:
                t = nimm("b", 1)
                if t == 0:
                    return d
                if not 1 <= t <= 12:
                    raise ValueError("unbekannter Typ")
                name = text()
                d[name] = wert(t, tiefe + 1)
        if typ == 11:
            n = nimm("i", 4); laenge(n, 3); return [nimm("i", 4) for _ in range(n)]
        if typ == 12:
            n = nimm("i", 4); laenge(n, 4); pos += 8 * n; return None
        raise ValueError("unbekannter Typ")

    try:
        if nimm("b", 1) != 10:
            raise ValueError("keine NBT-Datei")
        text()
        return wert(10, 0)
    except (ValueError, struct.error, RecursionError) as e:
        raise Fehler(400, "Die Datei ist keine gültige Schematic (%s)." % e)


def pruefe_schematic(nbt):
    """Prüft den Aufbau einer Create-Schematic. Gibt (Größe, Palette, Blöcke) zurück."""
    if not isinstance(nbt, dict):
        raise Fehler(400, "Die Datei ist keine Create-Schematic.")
    groesse = nbt.get("size")
    palette = nbt.get("palette")
    if palette is None and isinstance(nbt.get("palettes"), list) and nbt["palettes"]:
        palette = nbt["palettes"][0]
    bloecke = nbt.get("blocks")
    if not (isinstance(groesse, list) and len(groesse) == 3 and all(isinstance(v, int) for v in groesse)
            and isinstance(palette, list) and isinstance(bloecke, list)):
        raise Fehler(400, "Die Datei ist keine Create-Schematic (size, palette oder blocks fehlen).")
    if any(not 0 < v <= MAX_KANTE for v in groesse):
        raise Fehler(413, "Die Schematic ist zu groß (höchstens %d Blöcke pro Richtung)." % MAX_KANTE)
    if len(bloecke) > MAX_BLOECKE:
        raise Fehler(413, "Die Schematic hat zu viele Blöcke (höchstens %d)." % MAX_BLOECKE)
    for p in palette:
        if not isinstance(p, dict) or not isinstance(p.get("Name"), str):
            raise Fehler(400, "Die Palette der Schematic ist kaputt.")
    for b in bloecke:
        pos, st = b.get("pos") if isinstance(b, dict) else None, b.get("state") if isinstance(b, dict) else None
        if not (isinstance(pos, list) and len(pos) == 3 and all(isinstance(v, int) for v in pos)
                and isinstance(st, int) and 0 <= st < len(palette)):
            raise Fehler(400, "Ein Block in der Schematic ist kaputt.")
    return groesse, palette, bloecke


# --- Helfer --------------------------------------------------------------------

def lies_json(pfad, ersatz=None):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return ersatz


def schreibe_json(pfad, daten):
    Path(pfad).write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def welt_von(p0, drehung, x, y, z):
    """Wie weltVon() in website/js/voxel.js."""
    d = (drehung or 0) % 360
    dx, dz = x, z
    if d == 90:
        dx, dz = -z, x
    elif d == 180:
        dx, dz = -x, -z
    elif d == 270:
        dx, dz = z, -x
    return [p0[0] + dx, p0[1] + y, p0[2] + dz]


def modell_schluessel(modell):
    """Menge (x, y, z, Block-ID) eines Modells, plus Zählung pro Block-ID."""
    if not modell:
        return set()
    pal = modell.get("palette") or []
    aus = set()
    for b in modell.get("bloecke") or []:
        sid = pal[b[3]]["id"] if b[3] < len(pal) and pal[b[3]].get("id") else str(b[3])
        aus.add((b[0], b[1], b[2], sid))
    return aus


def welt_box(geb, modell):
    """Weltkoordinaten-Quader [von, bis] eines Modells, mit 2 Blöcken Rand."""
    p0, dreh = geb["welt"]["p0"], geb["welt"].get("drehung")
    bl = (modell or {}).get("bloecke") or []
    if not bl:
        return None
    ecken = [welt_von(p0, dreh, b[0], b[1], b[2]) for b in bl]
    von = [min(e[i] for e in ecken) for i in range(3)]
    bis = [max(e[i] for e in ecken) for i in range(3)]
    return [[von[0] - 2, von[1], von[2] - 2], [bis[0] + 2, bis[1] + 2, bis[2] + 2]]


class Karte:
    def __init__(self, git, daten, log):
        self.git = git
        self.repo = Path(git.repo)
        self.ordner = Path(daten) / "import"
        self.arbeit = self.ordner / "arbeit"
        self.upload = self.ordner / "upload.nbt"
        self.statusdatei = self.ordner / "status.json"
        self.lock = threading.Lock()
        self.log = log
        self.ordner.mkdir(parents=True, exist_ok=True)

    # -- Zustand --

    def status(self):
        s = lies_json(self.statusdatei)
        if s and time.time() - s.get("aktiv", 0) > ABLAUF:
            return None
        return s

    def _speichere(self, s):
        s["aktiv"] = time.time()
        schreibe_json(self.statusdatei, s)

    def _frei_fuer(self, kid):
        s = self.status()
        if s and s["wer"] != kid:
            minuten = max(1, int((time.time() - s["seit"]) // 60))
            raise Fehler(409, "%s importiert gerade (seit %d Minuten). Es geht immer nur ein Import gleichzeitig." % (s["name"], minuten))
        return s

    @staticmethod
    def _arbeitet():
        raise Fehler(409, "Gerade wird schon gerechnet, bitte einen Moment warten.")

    def _aufraeumen(self, pfad=None):
        pfad = pfad or self.arbeit
        self.git.git("worktree", "remove", "--force", str(pfad), pruefen=False)
        if pfad.exists():
            shutil.rmtree(pfad, ignore_errors=True)
        self.git.git("worktree", "prune", pruefen=False)

    def _worktree(self, pfad):
        self._aufraeumen(pfad)
        with self.git.gesperrt():
            basis = self.git.kopf()
            self.git.git("worktree", "add", "--detach", "--force", str(pfad), basis)
        return basis

    def _skript(self, arbeit, *args):
        r = subprocess.run([sys.executable, "-I", "-B"] + list(args), cwd=str(arbeit), capture_output=True,
                           text=True, timeout=SKRIPT_ZEIT)
        if r.returncode != 0:
            self.log("Skript fehlgeschlagen:", args, r.stderr[-800:])
            raise Fehler(500, "%s ist fehlgeschlagen: %s" % (args[0], (r.stderr.strip().splitlines() or ["?"])[-1][:300]))
        return r.stdout

    # -- Gebäude --

    def gebaeude(self, wurzel=None):
        """Alle Gebäude mit Modell aus campus.json, mit ihrer Einstellung für den Import."""
        wurzel = Path(wurzel or self.repo)
        campus = lies_json(wurzel / "campus/campus.json", {"gebaeude": []})
        aus = []
        for g in campus["gebaeude"]:
            if not g.get("ordner"):
                continue
            geb = lies_json(wurzel / g["ordner"] / "gebaeude.json")
            if not geb or not geb.get("welt", {}).get("p0"):
                continue
            dateien = geb.get("dateien") or {}
            gen = dateien.get("generator")
            kann_entwurf = bool(gen and gen not in NICHT_AUF_DEM_SERVER and (wurzel / gen).exists())
            quelle = geb.get("modellquelle") or ("schematic" if geb.get("ausschnitt") and dateien.get("schematic") else "entwurf")
            if quelle == "entwurf" and not kann_entwurf:
                quelle = "schematic"
            aus_ = geb.get("ausschnitt") or {}
            vorschlag = None if aus_.get("von") else welt_box(geb, lies_json(wurzel / g["ordner"] / "modell.json"))
            aus.append({
                "id": g["id"], "name": g["name"], "ordner": g["ordner"], "generator": gen if kann_entwurf else None,
                "quelle": quelle, "kannEntwurf": kann_entwurf,
                "von": aus_.get("von") or (vorschlag[0] if vorschlag else None),
                "bis": aus_.get("bis") or (vorschlag[1] if vorschlag else None),
                "aussen": gen == AUSSEN_SKRIPT,
            })
        return aus

    def letzte_ecke(self):
        for g in self.gebaeude():
            geb = lies_json(self.repo / g["ordner"] / "gebaeude.json") or {}
            sp = (geb.get("ausschnitt") or {}).get("schematicP0")
            if sp:
                return sp
        return None

    # -- Import --

    def hochladen(self, kid, name, roh, dateiname):
        with self._exklusiv():
            self._frei_fuer(kid)
            if len(roh) > MAX_UPLOAD:
                raise Fehler(413, "Die Datei ist größer als %d MB." % (MAX_UPLOAD // 1024 // 1024))
            groesse, palette, bloecke = pruefe_schematic(lies_nbt_sicher(entpacken(roh)))
            with open(self.upload, "wb") as f:
                f.write(roh)
            s = {"wer": kid, "name": name, "seit": time.time(), "dateiname": dateiname[:120], "bytes": len(roh),
                 "groesse": groesse, "anzahl": len(bloecke), "ergebnis": None}
            self._speichere(s)
            self.log("Import: %s hat %s hochgeladen (%d Blöcke)" % (kid, dateiname, len(bloecke)))
            return s

    class _Exklusiv:
        def __init__(self, k):
            self.k = k

        def __enter__(self):
            if not self.k.lock.acquire(blocking=False):
                Karte._arbeitet()

        def __exit__(self, *a):
            self.k.lock.release()

    def _exklusiv(self):
        return Karte._Exklusiv(self)

    def vorschau(self, kid, ecke, einstellungen):
        """Rechnet die Vorschau im Worktree. einstellungen: {id: {"quelle", "von", "bis"}}."""
        with self._exklusiv():
            s = self._frei_fuer(kid)
            if not s or not self.upload.exists():
                raise Fehler(409, "Bitte zuerst eine Schematic hochladen.")
            if not (isinstance(ecke, list) and len(ecke) == 3 and all(isinstance(v, int) and abs(v) < 30000000 for v in ecke)):
                raise Fehler(400, "Die Ecke bitte als drei ganze Zahlen x, y, z.")
            basis = self._worktree(self.arbeit)
            try:
                ergebnis = self._rechnen(self.arbeit, ecke, einstellungen or {})
            except Exception:
                self._aufraeumen()
                raise
            ergebnis["basis"] = basis
            s.update(ecke=ecke, einstellungen=einstellungen, ergebnis=ergebnis, basis=basis)
            self._speichere(s)
            return s

    def _rechnen(self, arbeit, ecke, einstellungen):
        shutil.copyfile(self.upload, arbeit / SCHEMATIC)
        liste = self.gebaeude(arbeit)
        # Einstellungen pro Gebäude in gebaeude.json übernehmen
        for g in liste:
            e = einstellungen.get(g["id"]) or {}
            quelle = e.get("quelle") or g["quelle"]
            if quelle not in ("schematic", "entwurf") or (quelle == "entwurf" and not g["kannEntwurf"]):
                raise Fehler(400, "%s: diese Quelle geht nicht." % g["name"])
            von, bis = e.get("von") or g["von"], e.get("bis") or g["bis"]
            pfad = arbeit / g["ordner"] / "gebaeude.json"
            geb = lies_json(pfad)
            geb["modellquelle"] = quelle
            if quelle == "schematic":
                if not (isinstance(von, list) and isinstance(bis, list) and len(von) == 3 and len(bis) == 3
                        and all(isinstance(v, int) for v in von + bis)):
                    raise Fehler(400, "%s: Bereich von/bis fehlt." % g["name"])
                geb.setdefault("dateien", {})["schematic"] = SCHEMATIC
                geb["ausschnitt"] = {"schematicP0": ecke, "von": [min(a, b) for a, b in zip(von, bis)],
                                     "bis": [max(a, b) for a, b in zip(von, bis)]}
            elif geb.get("ausschnitt"):
                geb["ausschnitt"]["schematicP0"] = ecke
            g["quelle"] = quelle
            schreibe_json(pfad, geb)
        # Skripte: erst die Gebäude, Außenanlagen zuletzt (sie sparen die Gebäude aus)
        for g in sorted(liste, key=lambda g: g["aussen"]):
            if g["quelle"] == "schematic":
                self._skript(arbeit, "tools/modell-aus-schematic.py", g["ordner"])
            else:
                self._skript(arbeit, g["generator"])
        # Gelände zuletzt, es spart die fertigen Gebäude aus
        if (arbeit / GELAENDE).exists() and (arbeit / GELAENDE_SKRIPT).exists():
            self._skript(arbeit, GELAENDE_SKRIPT, "--p0", *[str(v) for v in ecke])
        return self._vergleich(arbeit, liste, ecke)

    def _vergleich(self, arbeit, liste, ecke):
        texturen = (lies_json(self.repo / "texturen/texturen.json", {}) or {}).get("bloecke", {})
        alle_alt, neu_ids = set(), {}
        gebaeude = []
        for g in liste:
            alt = modell_schluessel(lies_json(self.repo / g["ordner"] / "modell.json"))
            neu_modell = lies_json(arbeit / g["ordner"] / "modell.json")
            neu = modell_schluessel(neu_modell)
            alle_alt |= {b[3] for b in alt}
            for b in neu:
                neu_ids.setdefault(b[3], {}).setdefault(g["name"], 0)
                neu_ids[b[3]][g["name"]] += 1
            dazu, weg = len(neu - alt), len(alt - neu)
            warnung = None
            if alt and not neu:
                warnung = "verliert alle Blöcke"
            elif alt and weg > WARN_ANTEIL * len(alt) and len(neu) < len(alt):
                warnung = "verliert %d %% der Blöcke" % round(100 * (len(alt) - len(neu)) / len(alt))
            elif alt and weg > WARN_ANTEIL * len(alt):
                warnung = "%d %% der Blöcke ändern sich" % round(100 * weg / len(alt))
            gebaeude.append({"id": g["id"], "name": g["name"], "quelle": g["quelle"], "kannEntwurf": g["kannEntwurf"],
                             "von": g["von"], "bis": g["bis"], "vorher": len(alt), "nachher": len(neu),
                             "dazu": dazu, "weg": weg, "warnung": warnung})
        ohne = []
        for sid, wo in sorted(neu_ids.items()):
            if sid in alle_alt or sid in texturen or sid.split("|")[0] in texturen or sid.startswith("platzhalter:"):
                continue
            ohne.append({"id": sid, "wo": wo})
        return {"gebaeude": gebaeude, "ohneTextur": ohne, "aussen": self._aussen(arbeit, liste, ecke)}

    def _aussen(self, arbeit, liste, ecke):
        """Gebautes in der Schematic, das in keinem Gebäude liegt: Hinweis auf neue Gebäude."""
        roh = self.upload.read_bytes()
        _, palette, bloecke = pruefe_schematic(lies_nbt_sicher(entpacken(roh)))
        kisten = []
        for g in liste:
            geb = lies_json(arbeit / g["ordner"] / "gebaeude.json") or {}
            a = geb.get("ausschnitt")
            if g["quelle"] == "schematic" and a:
                kisten.append((a["von"], a["bis"]))
            else:
                box = welt_box(geb, lies_json(arbeit / g["ordner"] / "modell.json"))
                if box and not g["aussen"]:
                    kisten.append(box)
        ignorieren = self._boden_und_unsichtbar(arbeit)
        zellen = {}
        for b in bloecke:
            name = palette[b["state"]]["Name"]
            if name in ignorieren or name.startswith("minecraft:") and not GEBAUT.search(name):
                continue
            w = [ecke[i] + b["pos"][i] for i in range(3)]
            if any(all(k[0][i] <= w[i] <= k[1][i] for i in range(3)) for k in kisten):
                continue
            z = zellen.setdefault((w[0] // 8, w[2] // 8), {"n": 0, "von": list(w), "bis": list(w), "namen": {}})
            z["n"] += 1
            for i in range(3):
                z["von"][i] = min(z["von"][i], w[i]); z["bis"][i] = max(z["bis"][i], w[i])
            z["namen"][name] = z["namen"].get(name, 0) + 1
        # Nachbarzellen zu Gruppen zusammenfassen
        gruppen, gesehen = [], set()
        for start in zellen:
            if start in gesehen:
                continue
            gruppe, stapel = [], [start]
            while stapel:
                c = stapel.pop()
                if c in gesehen or c not in zellen:
                    continue
                gesehen.add(c)
                gruppe.append(zellen[c])
                stapel.extend((c[0] + dx, c[1] + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1))
            n = sum(z["n"] for z in gruppe)
            if n < 30:
                continue
            namen = {}
            for z in gruppe:
                for k, v in z["namen"].items():
                    namen[k] = namen.get(k, 0) + v
            gruppen.append({"bloecke": n,
                            "von": [min(z["von"][i] for z in gruppe) for i in range(3)],
                            "bis": [max(z["bis"][i] for z in gruppe) for i in range(3)],
                            "haeufig": [k for k, _ in sorted(namen.items(), key=lambda kv: -kv[1])[:3]]})
        return sorted(gruppen, key=lambda g: -g["bloecke"])[:10]

    @staticmethod
    def _boden_und_unsichtbar(arbeit):
        """Boden- und unsichtbare Blöcke aus tools/modell-aus-schematic.py (BODEN, UNSICHTBAR)."""
        quelle = (Path(arbeit) / "tools/modell-aus-schematic.py").read_text(encoding="utf-8")
        namen = set()
        for liste in ("BODEN", "UNSICHTBAR"):
            m = re.search(r"^" + liste + r" = \{(.*?)\}", quelle, re.S | re.M)
            if m:
                namen |= set(re.findall(r'"([a-z0-9_.:-]+)"', m.group(1)))
        return namen

    def modell(self, kid, gid):
        """Neues Modell eines Gebäudes aus der Vorschau, für die 3D-Ansicht."""
        s = self.status()
        if not s or not s.get("ergebnis"):
            raise Fehler(404, "Keine Vorschau.")
        for g in self.gebaeude(self.arbeit):
            if g["id"] == gid:
                pfad = self.arbeit / g["ordner"] / "modell.json"
                if pfad.exists():
                    return pfad.read_bytes()
        raise Fehler(404, "Kein Modell.")

    def verwerfen(self, kid, admin=False):
        with self._exklusiv():
            s = self.status()
            if s and s["wer"] != kid and not admin:
                raise Fehler(403, "Das ist der Import von %s." % s["name"])
            self._aufraeumen()
            for p in (self.statusdatei, self.upload):
                if p.exists():
                    p.unlink()

    def uebernehmen(self, kid, autor):
        with self._exklusiv():
            s = self.status()
            if not s or s["wer"] != kid or not s.get("ergebnis"):
                raise Fehler(409, "Keine Vorschau zum Übernehmen, oder sie ist abgelaufen.")
            teile = []
            for g in s["ergebnis"]["gebaeude"]:
                if g["dazu"] or g["weg"]:
                    teile.append("%s +%d −%d" % (g["name"], g["dazu"], g["weg"]))
            nachricht = "Karte aktualisiert aus %s: %s" % (s["dateiname"] or "Schematic", ", ".join(teile) or "keine Blockänderung")
            commit = self._schreiben(self.arbeit, s["basis"], nachricht, autor)
            self._aufraeumen()
            for p in (self.statusdatei, self.upload):
                if p.exists():
                    p.unlink()
            self.log("Import übernommen von", kid, commit)
            return commit

    def _schreiben(self, arbeit, basis, nachricht, autor):
        """Zip im Worktree bauen und alle Änderungen als ein Commit ins Repo."""
        self._skript(arbeit, "tools/baue-ansicht-zip.py")
        r = subprocess.run(["git", "-C", str(arbeit), "status", "--porcelain", "--untracked-files=all"],
                           capture_output=True, text=True, check=True)
        dateien = {}
        for zeile in r.stdout.splitlines():
            pfad = zeile[3:].strip().strip('"')
            if " -> " in pfad:
                pfad = pfad.split(" -> ")[-1]
            if not pfad.startswith(DARF_AENDERN):
                raise Fehler(500, "Ein Skript hat %s geändert, das darf der Import nicht. Nichts gespeichert." % pfad)
            ziel = arbeit / pfad
            dateien[pfad] = ziel.read_bytes() if ziel.exists() else None
        with self.git.gesperrt():
            self.git.aktualisieren()
            kopf = self.git.kopf()
            if kopf != basis:
                geaendert = self.git.git("diff", "--name-only", basis, kopf).stdout.split()
                stoert = [p for p in geaendert if p.startswith(BETRIFFT_KARTE)]
                if stoert:
                    raise Fehler(409, "Seit der Vorschau hat jemand %s geändert. Nichts gespeichert. "
                                      "Bitte die Vorschau neu berechnen." % stoert[0])
            if not dateien:
                return None
            return self.git.schreibe_gesperrt(dateien, nachricht, autor)

    # -- Versionen --

    def versionen(self, ab=0, anzahl=40):
        trenner = "\x1e"
        r = self.git.git("log", "--skip=%d" % ab, "-n", str(anzahl), "--name-only",
                         "--format=" + trenner + "%H%x1f%an%x1f%ae%x1f%aI%x1f%cn%x1f%s")
        aus = []
        for block in r.stdout.split(trenner)[1:]:
            zeilen = block.strip("\n").split("\n")
            h, an, ae, datum, cn, betreff = zeilen[0].split("\x1f")
            pfade = [p for p in zeilen[1:] if p.strip()]
            bereiche = []
            for p in pfade:
                b = ("Karte" if p in (SCHEMATIC, GELAENDE) or p.endswith("/modell.json") or p.startswith("download/") else "Kanban" if p.startswith("kanban/")
                     else "Team" if p.startswith("team/") else "Gebäude" if p.startswith(("gebaeude/", "campus/"))
                     else "Website" if p.startswith(("website/", "server/", "tools/", "texturen/")) else "Doku")
                if b not in bereiche:
                    bereiche.append(b)
            aus.append({"commit": h, "autor": an, "mail": ae, "datum": datum, "ueber": cn, "betreff": betreff,
                        "bereiche": bereiche, "karte": "Karte" in bereiche, "dateien": len(pfade)})
        return aus

    def wiederherstellen(self, commit, kid, autor):
        """Karte auf den Stand eines früheren Commits, als neuer Commit."""
        if not re.match(r"^[0-9a-f]{40}$", commit or ""):
            raise Fehler(400, "Ungültiger Commit.")
        with self._exklusiv():
            s = self.status()
            if s:
                raise Fehler(409, "%s hat gerade einen Import offen. Bitte erst übernehmen oder verwerfen." % s["name"])
            if self.git.git("merge-base", "--is-ancestor", commit, "HEAD", pruefen=False).returncode != 0:
                raise Fehler(400, "Diesen Stand gibt es im Verlauf nicht.")
            ziel = self.ordner / "zurueck"
            basis = self._worktree(ziel)
            try:
                def alt(pfad):
                    r = subprocess.run(["git", "-C", str(ziel), "show", "%s:%s" % (commit, pfad)], capture_output=True)
                    return r.stdout if r.returncode == 0 else None
                schem = alt(SCHEMATIC)
                if schem is not None:
                    (ziel / SCHEMATIC).write_bytes(schem)
                gelaende = alt(GELAENDE)
                if gelaende is not None and (ziel / GELAENDE).exists():
                    (ziel / GELAENDE).write_bytes(gelaende)
                for g in self.gebaeude(ziel):
                    for datei in ("modell.json", "bauanleitung.json"):
                        inhalt = alt("%s/%s" % (g["ordner"], datei))
                        if inhalt is not None and (ziel / g["ordner"] / datei).exists():
                            (ziel / g["ordner"] / datei).write_bytes(inhalt)
                    alt_geb = alt("%s/gebaeude.json" % g["ordner"])
                    if alt_geb is None:
                        continue
                    alt_geb = json.loads(alt_geb.decode("utf-8"))
                    pfad = ziel / g["ordner"] / "gebaeude.json"
                    geb = lies_json(pfad)
                    for feld in ("ausschnitt", "modellquelle"):
                        if feld in alt_geb:
                            geb[feld] = alt_geb[feld]
                        else:
                            geb.pop(feld, None)
                    alt_dateien = alt_geb.get("dateien") or {}
                    if "schematic" in alt_dateien:
                        geb.setdefault("dateien", {})["schematic"] = alt_dateien["schematic"]
                    else:
                        (geb.get("dateien") or {}).pop("schematic", None)
                    schreibe_json(pfad, geb)
                betreff = self.git.git("log", "-1", "--format=%s", commit).stdout.strip()
                datum = self.git.git("log", "-1", "--format=%ad", "--date=format:%d.%m.%Y %H:%M", commit).stdout.strip()
                nachricht = "Karte zurückgesetzt auf den Stand vom %s (%s, „%s“)" % (datum, commit[:7], betreff[:60])
                return self._schreiben(ziel, basis, nachricht, autor)
            finally:
                self._aufraeumen(ziel)
