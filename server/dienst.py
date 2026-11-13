"""Campus-Dienst: Login, Konten, Profile und Schreiben ins Repo.

Läuft hinter nginx und lauscht nur auf 127.0.0.1. nginx liefert die statischen Dateien
selbst aus und fragt vorher per auth_request bei /api/auth nach, ob der Login gültig ist.

Nutzung:  python3 server/dienst.py
Braucht:  Python ab 3.9 und git, keine Zusatzpakete

Einstellungen kommen aus Umgebungsvariablen (siehe server/campus-dienst.service):
  CAMPUS_REPO     Pfad zum Repo-Checkout            (Standard: Ordner über server/)
  CAMPUS_DATEN    Konten, Sitzungen, Sperrdatei     (Standard: /var/lib/campus)
  CAMPUS_ADRESSE  Adresse zum Lauschen              (Standard: 127.0.0.1)
  CAMPUS_PORT     Port                              (Standard: 8090)
  CAMPUS_BRANCH   Branch, auf den geschrieben wird  (Standard: main)
  CAMPUS_REMOTE   Remote für fetch und push         (Standard: origin, leer = ohne GitHub)

Konten und Passwort-Hashes liegen in CAMPUS_DATEN, nie im Repo. Ins Repo kommen nur
die öffentlichen Profilfelder unter team/.
"""
import fcntl
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HIER = Path(__file__).resolve().parent

# --- Einstellungen ---

REPO = Path(os.environ.get("CAMPUS_REPO") or HIER.parent).resolve()
DATEN = Path(os.environ.get("CAMPUS_DATEN") or "/var/lib/campus")
ADRESSE = os.environ.get("CAMPUS_ADRESSE") or "127.0.0.1"
PORT = int(os.environ.get("CAMPUS_PORT") or 8090)
BRANCH = os.environ.get("CAMPUS_BRANCH") or "main"
REMOTE = os.environ.get("CAMPUS_REMOTE", "origin")

COOKIE = "__Host-campus"            # __Host-: nur über HTTPS, nur für genau diese Domain
SITZUNG_TAGE = 30                   # so lange bleibt man eingeloggt, verlängert sich bei Nutzung
MAX_ANFRAGE = 64 * 1024             # größte erlaubte Anfrage an die API in Byte
FEHLVERSUCHE = 5                    # so viele falsche Passwörter ...
SPERRZEIT = 15 * 60                 # ... innerhalb dieser Sekunden, dann Pause
MIN_PASSWORT = 8

# scrypt: N = 2^14, r = 8, p = 1 braucht 16 MB Speicher und ca. 50 ms pro Versuch
SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1}

# Nur diese Ordner darf der Dienst im Repo beschreiben
SCHREIBBAR = ("team/", "kanban/")

ID_MUSTER = re.compile(r"^[a-z][a-z0-9-]{1,23}$")
MC_MUSTER = re.compile(r"^[A-Za-z0-9_]{3,16}$")
FARB_MUSTER = re.compile(r"^#[0-9a-f]{6}$")
FARBEN = ["#d9840b", "#3c7fc4", "#4f9a3a", "#b0457a", "#7a5cc4", "#c4553c", "#2f9a94", "#8a7a2a"]


def jetzt():
    return time.time()


def zeitstempel(t=None):
    return datetime.fromtimestamp(t if t is not None else jetzt(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(*teile):
    print(zeitstempel(), *teile, file=sys.stderr, flush=True)


class Fehler(Exception):
    """Wird als JSON {"fehler": text} mit HTTP-Status an den Browser gegeben."""

    def __init__(self, status, text):
        super().__init__(text)
        self.status = status
        self.text = text


# --- Dateien sicher schreiben ---

def schreibe_atomar(pfad, inhalt, modus=0o600):
    """Erst in eine Nachbardatei schreiben, dann umbenennen: nie eine halbe Datei."""
    pfad = Path(pfad)
    neu = pfad.with_name(pfad.name + ".neu")
    with open(neu, "wb") as f:
        f.write(inhalt)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(neu, modus)
    os.replace(neu, pfad)


@contextmanager
def dateisperre(pfad):
    """Sperre über flock. Dieselbe Datei nutzt der Timer mit flock(1), daher nie gleichzeitig."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


# --- Passwörter ---

def passwort_hash(passwort, salz=None, n=SCRYPT["n"], r=SCRYPT["r"], p=SCRYPT["p"]):
    salz = salz if salz is not None else secrets.token_bytes(16)
    h = hashlib.scrypt(passwort.encode("utf-8"), salt=salz, n=n, r=r, p=p, maxmem=64 * 1024 * 1024, dklen=32)
    return {"salz": salz.hex(), "hash": h.hex(), "n": n, "r": r, "p": p}


def passwort_passt(passwort, eintrag):
    h = passwort_hash(passwort, bytes.fromhex(eintrag["salz"]), eintrag["n"], eintrag["r"], eintrag["p"])
    return hmac.compare_digest(h["hash"], eintrag["hash"])


def passwort_pruefen(passwort):
    if not isinstance(passwort, str) or len(passwort) < MIN_PASSWORT:
        raise Fehler(400, "Das Passwort braucht mindestens %d Zeichen." % MIN_PASSWORT)
    if len(passwort) > 200:
        raise Fehler(400, "Das Passwort ist zu lang.")


# Vergleichswert für unbekannte Namen: so dauert ein Fehlversuch immer gleich lang
_ATTRAPPE = passwort_hash(secrets.token_hex(8))


# --- Konten ---

class Konten:
    """Konten in DATEN/konten.json. Lesen mit Zwischenspeicher, Schreiben immer frisch
    unter Sperre, damit konto.py und der laufende Dienst sich nicht überschreiben."""

    def __init__(self, ordner):
        self.datei = Path(ordner) / "konten.json"
        self.sperre = Path(ordner) / "konten.lock"
        self._stand = None
        self._daten = {}

    def _lies(self):
        try:
            st = self.datei.stat()
        except FileNotFoundError:
            return {}
        stand = (st.st_mtime_ns, st.st_size)
        if stand != self._stand:
            self._daten = json.loads(self.datei.read_text(encoding="utf-8")).get("konten", {})
            self._stand = stand
        return self._daten

    def alle(self):
        return dict(self._lies())

    def hole(self, kid):
        return self._lies().get(kid)

    @contextmanager
    def aendern(self):
        """with konten.aendern() as k: k["id"] = {...}  speichert am Ende."""
        with dateisperre(self.sperre):
            self._stand = None
            daten = json.loads(json.dumps(self._lies()))
            yield daten
            inhalt = json.dumps({"konten": daten}, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
            self.datei.parent.mkdir(parents=True, exist_ok=True)
            schreibe_atomar(self.datei, inhalt.encode("utf-8"))
            self._stand = None

    def anlegen(self, kid, passwort, admin=False):
        if not ID_MUSTER.match(kid or ""):
            raise Fehler(400, "Kontoname: 2 bis 24 Zeichen, nur a-z, 0-9 und Bindestrich, vorne ein Buchstabe.")
        passwort_pruefen(passwort)
        with self.aendern() as k:
            if kid in k:
                raise Fehler(409, "Das Konto „%s“ gibt es schon." % kid)
            k[kid] = dict(passwort_hash(passwort), admin=bool(admin), gesperrt=False, muss_aendern=True,
                          angelegt=zeitstempel(), sitzungen_ab=jetzt(), letzter_login=None)

    def passwort_setzen(self, kid, passwort, muss_aendern):
        passwort_pruefen(passwort)
        with self.aendern() as k:
            if kid not in k:
                raise Fehler(404, "Konto nicht gefunden.")
            k[kid].update(passwort_hash(passwort))
            k[kid]["muss_aendern"] = bool(muss_aendern)
            k[kid]["sitzungen_ab"] = jetzt()      # alle bisherigen Logins werden ungültig

    def setze(self, kid, **felder):
        with self.aendern() as k:
            if kid not in k:
                raise Fehler(404, "Konto nicht gefunden.")
            k[kid].update(felder)


# --- Sitzungen ---

class Sitzungen:
    """Sitzungen in DATEN/sitzungen.json. Gespeichert ist nur der SHA-256 des Tokens:
    wer die Datei liest, kann sich damit nicht einloggen."""

    def __init__(self, ordner):
        self.datei = Path(ordner) / "sitzungen.json"
        self.lock = threading.Lock()
        try:
            self.daten = json.loads(self.datei.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            self.daten = {}

    @staticmethod
    def _schluessel(token):
        return hashlib.sha256(token.encode("ascii", "replace")).hexdigest()

    def _speichern(self):
        t = jetzt()
        self.daten = {k: v for k, v in self.daten.items() if v["ablauf"] > t}
        self.datei.parent.mkdir(parents=True, exist_ok=True)
        schreibe_atomar(self.datei, (json.dumps(self.daten, indent=1, sort_keys=True) + "\n").encode("utf-8"))

    def neu(self, kid):
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.daten[self._schluessel(token)] = {"konto": kid, "beginn": jetzt(), "ablauf": jetzt() + SITZUNG_TAGE * 86400}
            self._speichern()
        return token

    def pruefe(self, token, konten):
        """Gibt (Konto-ID, Konto) zurück oder (None, None)."""
        if not token or len(token) > 100:
            return None, None
        s = self._schluessel(token)
        with self.lock:
            e = self.daten.get(s)
            if not e or e["ablauf"] < jetzt():
                return None, None
            konto = konten.hole(e["konto"])
            if not konto or konto.get("gesperrt") or e["beginn"] < konto.get("sitzungen_ab", 0):
                return None, None
            # Gleitend verlängern, aber höchstens einmal pro Stunde auf die Platte schreiben
            neu_ablauf = jetzt() + SITZUNG_TAGE * 86400
            if neu_ablauf - e["ablauf"] > 3600:
                e["ablauf"] = neu_ablauf
                self._speichern()
            return e["konto"], konto

    def beenden(self, token):
        with self.lock:
            if self.daten.pop(self._schluessel(token or ""), None):
                self._speichern()


# --- Bremse gegen Passwort-Raten ---

class Bremse:
    def __init__(self):
        self.lock = threading.Lock()
        self.versuche = {}

    def _liste(self, schluessel):
        grenze = jetzt() - SPERRZEIT
        liste = [t for t in self.versuche.get(schluessel, []) if t > grenze]
        self.versuche[schluessel] = liste
        return liste

    def gesperrt(self, *schluessel):
        with self.lock:
            return any(len(self._liste(s)) >= FEHLVERSUCHE * (4 if s.startswith("ip:") else 1) for s in schluessel)

    def fehlschlag(self, *schluessel):
        with self.lock:
            for s in schluessel:
                self._liste(s).append(jetzt())

    def erfolg(self, schluessel):
        with self.lock:
            self.versuche.pop(schluessel, None)


# --- Git ---

def blob_version(pfad):
    """Git-Blob-Hash einer Datei (wie git hash-object), None wenn es sie nicht gibt.
    Damit merkt der Dienst, ob eine Datei seit dem Laden im Browser geändert wurde."""
    try:
        daten = Path(pfad).read_bytes()
    except FileNotFoundError:
        return None
    return hashlib.sha1(b"blob %d\0" % len(daten) + daten).hexdigest()


class Git:
    """Alle Schreibzugriffe aufs Repo laufen hier durch, einer nach dem anderen."""

    def __init__(self, repo, sperrdatei, branch=BRANCH, remote=REMOTE):
        self.repo = Path(repo)
        self.sperrdatei = Path(sperrdatei)
        self.branch = branch
        self.remote = remote
        self.lock = threading.Lock()

    def git(self, *args, env=None, pruefen=True):
        umgebung = dict(os.environ, GIT_TERMINAL_PROMPT="0", LC_ALL="C")
        if env:
            umgebung.update(env)
        r = subprocess.run(["git", "-C", str(self.repo)] + list(args), capture_output=True, text=True,
                           env=umgebung, timeout=120)
        if pruefen and r.returncode != 0:
            raise Fehler(500, "git %s ist fehlgeschlagen: %s" % (args[0], (r.stderr or r.stdout).strip()[:400]))
        return r

    @contextmanager
    def gesperrt(self):
        with self.lock, dateisperre(self.sperrdatei):
            yield

    def hat_remote(self):
        if not self.remote:
            return False
        return self.git("remote", pruefen=False).stdout.split().count(self.remote) > 0

    def aktualisieren(self):
        """Neuesten Stand holen und vorspulen. Nur innerhalb von gesperrt() aufrufen."""
        if self.git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            raise Fehler(500, "Im Repo auf dem Server gibt es ungespeicherte Änderungen. Bitte den Admin fragen.")
        if not self.hat_remote():
            return
        self.git("fetch", "--quiet", self.remote, self.branch)
        r = self.git("merge", "--ff-only", "--quiet", "%s/%s" % (self.remote, self.branch), pruefen=False)
        if r.returncode != 0:
            raise Fehler(409, "Der Stand auf dem Server passt nicht mehr zu GitHub (jemand hat die Geschichte "
                              "umgeschrieben). Nichts gespeichert, bitte den Admin fragen.")

    def schreibe(self, dateien, nachricht, autor, erwartet, bezeichnung=None):
        """dateien: {pfad im Repo: bytes, None zum Löschen, oder eine Funktion, die aus dem
                    aktuellen Inhalt (bytes oder None) unter der Sperre den neuen macht}
        erwartet: {pfad: Blob-Version, die der Browser gesehen hat (None = darf noch nicht existieren)}
        autor: (Name, E-Mail). bezeichnung: wie die Datei in Meldungen heißt. Gibt den neuen Commit-Hash zurück, oder None ohne Änderung."""
        for pfad in list(dateien) + list(erwartet):
            if ".." in pfad.split("/") or not pfad.startswith(SCHREIBBAR) or pfad.startswith("/"):
                raise Fehler(400, "Pfad nicht erlaubt: %s" % pfad)
        with self.gesperrt():
            self.aktualisieren()
            for pfad, version in erwartet.items():
                if blob_version(self.repo / pfad) != version:
                    raise Fehler(409, "%s wurde inzwischen von jemand anderem geändert. Nichts gespeichert. "
                                      "Bitte die Seite neu laden und es noch einmal versuchen." % (bezeichnung or pfad))
            vorher = self.git("rev-parse", "HEAD").stdout.strip()
            for pfad, inhalt in dateien.items():
                ziel = self.repo / pfad
                if callable(inhalt):
                    inhalt = inhalt(ziel.read_bytes() if ziel.exists() else None)
                if inhalt is None:
                    if ziel.exists():
                        ziel.unlink()
                else:
                    ziel.parent.mkdir(parents=True, exist_ok=True)
                    schreibe_atomar(ziel, inhalt, 0o644)
            self.git("add", "--all", "--", *dateien.keys())
            if self.git("diff", "--cached", "--quiet", pruefen=False).returncode == 0:
                return None
            env = {"GIT_AUTHOR_NAME": autor[0], "GIT_AUTHOR_EMAIL": autor[1],
                   "GIT_COMMITTER_NAME": "Campus-Website", "GIT_COMMITTER_EMAIL": "website@campus.invalid"}
            try:
                self.git("commit", "--quiet", "-m", nachricht, env=env)
            except Fehler:
                self.git("reset", "--hard", "--quiet", vorher, pruefen=False)
                raise
            if self.hat_remote():
                r = self.git("push", "--quiet", self.remote, "HEAD:" + self.branch, pruefen=False)
                if r.returncode != 0:
                    self.git("reset", "--hard", "--quiet", vorher, pruefen=False)
                    log("push abgelehnt:", r.stderr.strip())
                    raise Fehler(409, "GitHub hat die Änderung nicht angenommen, vermutlich kam gerade etwas "
                                      "von außen dazu. Nichts gespeichert. Bitte neu laden und noch einmal versuchen.")
            return self.git("rev-parse", "HEAD").stdout.strip()

    def kopf(self):
        return self.git("rev-parse", "HEAD").stdout.strip()


# --- Profile (öffentlich, im Repo unter team/) ---

def profil_pfad(kid):
    return "team/%s.json" % kid


def lies_profil(kid):
    try:
        return json.loads((REPO / profil_pfad(kid)).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def profil_bytes(p):
    return (json.dumps(p, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def profil_pruefen(kid, eingabe, alt=None):
    p = dict(alt or {})
    p["id"] = kid
    name = str(eingabe.get("anzeigename", p.get("anzeigename") or kid)).strip()
    if not 1 <= len(name) <= 40:
        raise Fehler(400, "Anzeigename: 1 bis 40 Zeichen.")
    mc = str(eingabe.get("minecraft", p.get("minecraft") or "")).strip()
    if mc and not MC_MUSTER.match(mc):
        raise Fehler(400, "Minecraft-Name: 3 bis 16 Zeichen, nur Buchstaben, Ziffern und _.")
    farbe = str(eingabe.get("farbe", p.get("farbe") or FARBEN[sum(map(ord, kid)) % len(FARBEN)])).strip().lower()
    if not FARB_MUSTER.match(farbe):
        raise Fehler(400, "Farbe bitte als #rrggbb.")
    info = str(eingabe.get("info", p.get("info") or "")).strip()
    if len(info) > 500:
        raise Fehler(400, "Info: höchstens 500 Zeichen.")
    p.update(anzeigename=name, minecraft=mc, farbe=farbe, info=info)
    return {k: p[k] for k in ("id", "anzeigename", "minecraft", "farbe", "info")}


def autor_von(kid):
    p = lies_profil(kid) or {}
    return (p.get("anzeigename") or kid, "%s@campus.invalid" % kid)


def liste_aendern(dazu=None, weg=None):
    """Funktion für Git.schreibe: fügt eine ID in eine liste.json ein oder nimmt sie raus.
    Läuft unter der Sperre auf dem frischen Stand, deshalb gibt es hier keinen Konflikt."""
    def neu(alt):
        try:
            ids = json.loads(alt.decode("utf-8")) if alt else []
        except ValueError:
            ids = []
        ids = [i for i in ids if i != weg]
        if dazu and dazu not in ids:
            ids.append(dazu)
        return (json.dumps(sorted(ids), ensure_ascii=False) + "\n").encode("utf-8")
    return neu


def in_liste(pfad, kid):
    try:
        return kid in json.loads((REPO / pfad).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return False


def profil_anlegen(git, kid, eingabe, autor):
    """Legt team/<id>.json an, falls es noch fehlt, und trägt die ID in team/liste.json ein."""
    if lies_profil(kid) is not None and in_liste("team/liste.json", kid):
        return None
    dateien, erwartet = {"team/liste.json": liste_aendern(dazu=kid)}, {}
    if lies_profil(kid) is None:
        dateien[profil_pfad(kid)] = profil_bytes(profil_pruefen(kid, eingabe))
        erwartet[profil_pfad(kid)] = None
    name = profil_pruefen(kid, eingabe)["anzeigename"]
    return git.schreibe(dateien, "Team: %s dazu" % name, autor, erwartet)


# --- Kanban (im Repo unter kanban/) ---

STATUS = ["offen", "in Arbeit", "erledigt"]
WO = ["Minecraft", "Website"]
BEREICHE = ["Gebäude", "3D", "Doku", "Website", "Betrieb"]
TABS = ["ansicht", "konfig", "bauplan"]
KARTEN_ID = r"[a-z0-9][a-z0-9-]{0,47}"
DATUM_MUSTER = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def karten_pfad(kid):
    return "kanban/karten/%s.json" % kid


def lies_json(pfad, ersatz=None):
    try:
        return json.loads((REPO / pfad).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return ersatz


def karten_kurzname(titel):
    """Lesbare ID aus dem Titel, wie in tools/migriere-roadmap.py."""
    t = titel.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > 40:
        t = t[:41].rsplit("-", 1)[0]
    t = t or "karte"
    kid, n = t, 2
    while (REPO / karten_pfad(kid)).exists():
        kid, n = "%s-%d" % (t, n), n + 1
    return kid


def karte_pruefen(eingabe, alt):
    """Neue Karte aus alter Karte plus Eingabe. Nur bekannte Felder, alle geprüft."""
    k = dict(alt)
    for feld in ("titel", "beschreibung", "status", "phase", "wo", "bereich", "gebaeude", "tab", "zustaendig", "faellig", "rang"):
        if feld in eingabe:
            k[feld] = eingabe[feld]
    k["titel"] = str(k.get("titel") or "").strip()
    if not 1 <= len(k["titel"]) <= 120:
        raise Fehler(400, "Titel: 1 bis 120 Zeichen.")
    k["beschreibung"] = str(k.get("beschreibung") or "").strip()
    if len(k["beschreibung"]) > 4000:
        raise Fehler(400, "Beschreibung: höchstens 4000 Zeichen.")
    if k.get("status") not in STATUS:
        raise Fehler(400, "Unbekannter Status.")
    if k.get("wo") not in WO:
        raise Fehler(400, "Wo: Minecraft oder Website.")
    if k.get("bereich") not in BEREICHE:
        raise Fehler(400, "Unbekannter Bereich.")
    phasen = [p["id"] for p in lies_json("kanban/phasen.json", [])]
    if k.get("phase") not in phasen:
        raise Fehler(400, "Unbekannte Phase.")
    gebaeude = [g["id"] for g in lies_json("campus/campus.json", {}).get("gebaeude", [])]
    if k.get("gebaeude") in ("", None):
        k["gebaeude"] = None
    elif k["gebaeude"] not in gebaeude:
        raise Fehler(400, "Unbekanntes Gebäude.")
    if k.get("tab") in ("", None) or not k["gebaeude"]:
        k["tab"] = None
    elif k["tab"] not in TABS:
        raise Fehler(400, "Unbekannter Tab.")
    leute = lies_json("team/liste.json", [])
    z = k.get("zustaendig") or []
    if not isinstance(z, list) or any(p not in leute for p in z):
        raise Fehler(400, "Zuständig: nur Leute aus dem Team.")
    k["zustaendig"] = sorted(set(z))
    if k.get("faellig") in ("", None):
        k["faellig"] = None
    elif not DATUM_MUSTER.match(str(k["faellig"])):
        raise Fehler(400, "Fällig bitte als Datum.")
    try:
        k["rang"] = float(k.get("rang") or 0)
    except (TypeError, ValueError):
        raise Fehler(400, "Ungültiger Rang.")
    if k["rang"] == int(k["rang"]):
        k["rang"] = int(k["rang"])
    reihenfolge = ("id", "titel", "beschreibung", "status", "phase", "wo", "bereich", "gebaeude", "tab", "zustaendig", "faellig", "rang")
    return {f: k.get(f) for f in reihenfolge}


def karte_bytes(k):
    return (json.dumps(k, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def kurz(titel):
    return titel if len(titel) <= 60 else titel[:57] + "…"


# --- Webserver ---

def dienst_bauen():
    DATEN.mkdir(parents=True, exist_ok=True)
    return {
        "konten": Konten(DATEN),
        "sitzungen": Sitzungen(DATEN),
        "bremse": Bremse(),
        "git": Git(REPO, DATEN / "git.lock"),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "Campus"
    sys_version = ""
    d = None                    # wird in main() gesetzt

    # -- Hilfen --

    def log_message(self, fmt, *args):
        pass                    # kein Zugriffslog, das macht nginx

    def ip(self):
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def cookie(self):
        for teil in (self.headers.get("Cookie") or "").split(";"):
            name, _, wert = teil.strip().partition("=")
            if name == COOKIE:
                return wert
        return None

    def antwort(self, status, daten=None, kopf=None):
        inhalt = b"" if daten is None else json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        if daten is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (kopf or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(inhalt)

    def setze_cookie(self, token, sekunden):
        return {"Set-Cookie": "%s=%s; Path=/; Max-Age=%d; HttpOnly; Secure; SameSite=Strict" % (COOKIE, token, sekunden)}

    def eingabe(self):
        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge > MAX_ANFRAGE:
            raise Fehler(413, "Anfrage zu groß.")
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise Fehler(415, "Bitte JSON schicken.")
        try:
            daten = json.loads(self.rfile.read(laenge) or b"{}")
        except ValueError:
            raise Fehler(400, "Ungültiges JSON.")
        if not isinstance(daten, dict):
            raise Fehler(400, "Ungültige Anfrage.")
        return daten

    def gleicher_ursprung(self):
        """Schutz gegen fremde Seiten, die im Namen eines eingeloggten Nutzers etwas abschicken."""
        herkunft = self.headers.get("Origin")
        host = self.headers.get("Host")
        return bool(herkunft and host and urlsplit(herkunft).netloc == host)

    def wer(self):
        """(id, konto) des eingeloggten Nutzers oder (None, None)."""
        return self.d["sitzungen"].pruefe(self.cookie(), self.d["konten"])

    def eingeloggt(self, admin=False, auch_ohne_neues_passwort=False):
        kid, konto = self.wer()
        if not kid:
            raise Fehler(401, "Nicht eingeloggt.")
        if konto.get("muss_aendern") and not auch_ohne_neues_passwort:
            raise Fehler(403, "Bitte zuerst ein eigenes Passwort setzen.")
        if admin and not konto.get("admin"):
            raise Fehler(403, "Nur für Admins.")
        return kid, konto

    # -- Verteilung --

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.verteile("GET")

    def do_POST(self):
        self.verteile("POST")

    def verteile(self, methode):
        pfad = urlsplit(self.path).path
        try:
            if methode == "POST" and not self.gleicher_ursprung():
                raise Fehler(403, "Anfrage von fremder Seite abgelehnt.")
            for m, muster, funktion in ROUTEN:
                treffer = muster.match(pfad)
                if m == methode and treffer:
                    return funktion(self, *treffer.groups())
            raise Fehler(404, "Gibt es nicht.")
        except Fehler as f:
            self.antwort(f.status, {"fehler": f.text})
        except Exception as e:      # noqa: BLE001 – nie den Dienst sterben lassen
            log("Fehler bei", methode, pfad, repr(e))
            self.antwort(500, {"fehler": "Interner Fehler im Dienst."})

    # -- Login --

    def auth(self):
        """Für nginx auth_request: 204 = darf rein, 401 = zum Login."""
        kid, konto = self.wer()
        if kid and not konto.get("muss_aendern"):
            return self.antwort(204, kopf={"X-Campus-Konto": kid})
        return self.antwort(401)

    def login_seite(self):
        inhalt = (HIER / "login.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(inhalt)

    def login(self):
        e = self.eingabe()
        kid = str(e.get("name", "")).strip().lower()[:40]
        passwort = str(e.get("passwort", ""))
        bremse = self.d["bremse"]
        schluessel = ("ip:" + self.ip(), "konto:%s|%s" % (kid, self.ip()))
        if bremse.gesperrt(*schluessel):
            raise Fehler(429, "Zu viele Fehlversuche. Bitte in 15 Minuten noch einmal probieren.")
        konto = self.d["konten"].hole(kid)
        ok = passwort_passt(passwort, konto or _ATTRAPPE) and konto is not None
        if not ok or konto.get("gesperrt"):
            bremse.fehlschlag(*schluessel)
            log("Login fehlgeschlagen:", kid or "-", "von", self.ip())
            raise Fehler(401, "Name oder Passwort falsch.")
        bremse.erfolg(schluessel[1])
        self.d["konten"].setze(kid, letzter_login=zeitstempel())
        token = self.d["sitzungen"].neu(kid)
        log("Login:", kid, "von", self.ip())
        self.antwort(200, {"ok": True, "muss_aendern": bool(konto.get("muss_aendern"))},
                     self.setze_cookie(token, SITZUNG_TAGE * 86400))

    def abmelden(self):
        self.d["sitzungen"].beenden(self.cookie())
        self.antwort(200, {"ok": True}, self.setze_cookie("", 0))

    def passwort(self):
        kid, konto = self.eingeloggt(auch_ohne_neues_passwort=True)
        e = self.eingabe()
        if not passwort_passt(str(e.get("alt", "")), konto):
            raise Fehler(400, "Das bisherige Passwort stimmt nicht.")
        neu = str(e.get("neu", ""))
        if neu == str(e.get("alt", "")):
            raise Fehler(400, "Das neue Passwort muss anders sein als das alte.")
        self.d["konten"].passwort_setzen(kid, neu, muss_aendern=False)
        token = self.d["sitzungen"].neu(kid)     # alte Sitzungen sind jetzt ungültig, diese bleibt
        log("Passwort geändert:", kid)
        self.antwort(200, {"ok": True}, self.setze_cookie(token, SITZUNG_TAGE * 86400))

    def ich(self):
        kid, konto = self.wer()
        if not kid:
            raise Fehler(401, "Nicht eingeloggt.")
        p = lies_profil(kid) or {}
        self.antwort(200, {"id": kid, "admin": bool(konto.get("admin")), "muss_aendern": bool(konto.get("muss_aendern")),
                           "anzeigename": p.get("anzeigename") or kid, "farbe": p.get("farbe")})

    # -- Profile --

    def profil_lesen(self, pid):
        self.eingeloggt()
        p = lies_profil(pid)
        if p is None:
            raise Fehler(404, "Profil nicht gefunden.")
        self.antwort(200, {"profil": p, "version": blob_version(REPO / profil_pfad(pid))})

    def profil_speichern(self, pid):
        kid, konto = self.eingeloggt()
        if pid != kid and not konto.get("admin"):
            raise Fehler(403, "Du kannst nur dein eigenes Profil ändern.")
        e = self.eingabe()
        alt = lies_profil(pid)
        if alt is None:
            raise Fehler(404, "Profil nicht gefunden.")
        neu = profil_pruefen(pid, e, alt)
        wer = "" if pid == kid else " (von %s)" % autor_von(kid)[0]
        commit = self.d["git"].schreibe({profil_pfad(pid): profil_bytes(neu)}, "Profil von %s geändert%s" % (neu["anzeigename"], wer),
                                        autor_von(kid), {profil_pfad(pid): e.get("version")}, "Das Profil")
        self.antwort(200, {"ok": True, "commit": commit, "profil": neu, "version": blob_version(REPO / profil_pfad(pid))})

    # -- Admin --

    def konten_liste(self):
        self.eingeloggt(admin=True)
        felder = ("admin", "gesperrt", "muss_aendern", "angelegt", "letzter_login")
        aus = []
        for kid, k in sorted(self.d["konten"].alle().items()):
            p = lies_profil(kid) or {}
            aus.append(dict({f: k.get(f) for f in felder}, id=kid, anzeigename=p.get("anzeigename") or kid))
        self.antwort(200, {"konten": aus})

    def konto_anlegen(self):
        kid, _ = self.eingeloggt(admin=True)
        e = self.eingabe()
        neu = str(e.get("id", "")).strip().lower()
        profil_pruefen(neu if ID_MUSTER.match(neu) else "x", e)   # Eingaben vorab prüfen
        self.d["konten"].anlegen(neu, str(e.get("passwort", "")), bool(e.get("admin")))
        log("Konto angelegt:", neu, "von", kid)
        try:
            profil_anlegen(self.d["git"], neu, e, autor_von(kid))
        except Fehler as f:
            self.antwort(200, {"ok": True, "warnung": "Konto angelegt, aber das Profil konnte nicht gespeichert werden: " + f.text})
            return
        self.antwort(200, {"ok": True})

    def konto_aendern(self, ziel):
        kid, _ = self.eingeloggt(admin=True)
        e = self.eingabe()
        aktion = e.get("aktion")
        konten = self.d["konten"]
        if not konten.hole(ziel):
            raise Fehler(404, "Konto nicht gefunden.")
        if ziel == kid and aktion in ("sperren", "admin_weg"):
            raise Fehler(400, "Das geht nicht beim eigenen Konto.")
        if aktion == "zuruecksetzen":
            konten.passwort_setzen(ziel, str(e.get("passwort", "")), muss_aendern=True)
        elif aktion == "sperren":
            konten.setze(ziel, gesperrt=True, sitzungen_ab=jetzt())
        elif aktion == "entsperren":
            konten.setze(ziel, gesperrt=False)
        elif aktion == "admin":
            konten.setze(ziel, admin=True)
        elif aktion == "admin_weg":
            konten.setze(ziel, admin=False)
        else:
            raise Fehler(400, "Unbekannte Aktion.")
        log("Konto", ziel, aktion, "von", kid)
        self.antwort(200, {"ok": True})

    # -- Kanban --

    def kanban(self):
        self.eingeloggt()
        karten = []
        for kid in lies_json("kanban/liste.json", []):
            k = lies_json(karten_pfad(kid))
            if k:
                k["version"] = blob_version(REPO / karten_pfad(kid))
                karten.append(k)
        self.antwort(200, {"commit": self.d["git"].kopf(), "phasen": lies_json("kanban/phasen.json", []), "karten": karten})

    def karte_neu(self):
        kid, _ = self.eingeloggt()
        e = self.eingabe()
        vorlage = {"status": "offen", "wo": "Minecraft", "bereich": "Gebäude", "zustaendig": [], "rang": 0}
        k = karte_pruefen(e, vorlage)
        k["id"] = karten_kurzname(k["titel"])
        commit = self.d["git"].schreibe(
            {karten_pfad(k["id"]): karte_bytes(k), "kanban/liste.json": liste_aendern(dazu=k["id"])},
            "Kanban: neue Karte „%s“" % kurz(k["titel"]), autor_von(kid), {karten_pfad(k["id"]): None})
        k["version"] = blob_version(REPO / karten_pfad(k["id"]))
        self.antwort(200, {"ok": True, "commit": commit, "karte": k})

    def karte_aendern(self, karte_id):
        kid, _ = self.eingeloggt()
        e = self.eingabe()
        alt = lies_json(karten_pfad(karte_id))
        if alt is None:
            raise Fehler(409, "Die Karte gibt es nicht mehr, vermutlich hat sie jemand gelöscht. Bitte neu laden.")
        k = karte_pruefen(e, alt)
        k["id"] = karte_id
        if k["status"] != alt.get("status"):
            nachricht = "Kanban: „%s“ nach %s" % (kurz(k["titel"]), k["status"])
        elif set(e) <= {"rang", "version", "phase"}:
            nachricht = "Kanban: „%s“ verschoben" % kurz(k["titel"])
        else:
            nachricht = "Kanban: „%s“ geändert" % kurz(k["titel"])
        commit = self.d["git"].schreibe({karten_pfad(karte_id): karte_bytes(k)}, nachricht, autor_von(kid),
                                        {karten_pfad(karte_id): e.get("version")}, "Die Karte „%s“" % kurz(alt.get("titel", "")))
        k["version"] = blob_version(REPO / karten_pfad(karte_id))
        self.antwort(200, {"ok": True, "commit": commit, "karte": k})

    def karte_loeschen(self, karte_id):
        kid, _ = self.eingeloggt()
        e = self.eingabe()
        alt = lies_json(karten_pfad(karte_id))
        if alt is None:
            raise Fehler(409, "Die Karte gibt es schon nicht mehr. Bitte neu laden.")
        commit = self.d["git"].schreibe(
            {karten_pfad(karte_id): None, "kanban/liste.json": liste_aendern(weg=karte_id)},
            "Kanban: „%s“ gelöscht" % kurz(alt.get("titel", karte_id)), autor_von(kid),
            {karten_pfad(karte_id): e.get("version")}, "Die Karte „%s“" % kurz(alt.get("titel", "")))
        self.antwort(200, {"ok": True, "commit": commit})

    def stand(self):
        """Aktueller Commit, damit offene Seiten merken, dass es etwas Neues gibt."""
        self.eingeloggt()
        self.antwort(200, {"commit": self.d["git"].kopf()})


def _r(methode, muster, funktion):
    return (methode, re.compile("^" + muster + "$"), funktion)


ROUTEN = [
    _r("GET", r"/api/auth", Handler.auth),
    _r("GET", r"/login", Handler.login_seite),
    _r("POST", r"/api/login", Handler.login),
    _r("POST", r"/api/abmelden", Handler.abmelden),
    _r("POST", r"/api/passwort", Handler.passwort),
    _r("GET", r"/api/ich", Handler.ich),
    _r("GET", r"/api/stand", Handler.stand),
    _r("GET", r"/api/profil/([a-z][a-z0-9-]{1,23})", Handler.profil_lesen),
    _r("POST", r"/api/profil/([a-z][a-z0-9-]{1,23})", Handler.profil_speichern),
    _r("GET", r"/api/kanban", Handler.kanban),
    _r("POST", r"/api/karten", Handler.karte_neu),
    _r("POST", r"/api/karten/(" + KARTEN_ID + r")", Handler.karte_aendern),
    _r("POST", r"/api/karten/(" + KARTEN_ID + r")/loeschen", Handler.karte_loeschen),
    _r("GET", r"/api/konten", Handler.konten_liste),
    _r("POST", r"/api/konten", Handler.konto_anlegen),
    _r("POST", r"/api/konten/([a-z][a-z0-9-]{1,23})", Handler.konto_aendern),
]


def beobachte_code():
    """Holt der Timer neuen Code für den Dienst von GitHub, beendet er sich mit Code 75.
    systemd startet ihn dann sofort neu (Restart=on-failure), und der neue Code läuft."""
    def stand():
        return [p.stat().st_mtime_ns for p in sorted(HIER.glob("*.py"))]
    alt = stand()
    while True:
        time.sleep(20)
        try:
            if stand() != alt:
                log("Code des Dienstes hat sich geändert, starte neu.")
                os._exit(75)
        except OSError:
            pass


def main():
    os.umask(0o022)
    threading.Thread(target=beobachte_code, daemon=True).start()
    Handler.d = dienst_bauen()
    if not (REPO / ".git").exists():
        log("Achtung:", REPO, "ist kein Git-Repo, Speichern geht nicht.")
    server = ThreadingHTTPServer((ADRESSE, PORT), Handler)
    server.daemon_threads = True
    log("Campus-Dienst läuft auf %s:%d, Repo %s, Daten %s" % (ADRESSE, PORT, REPO, DATEN))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
