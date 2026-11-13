"""Campus-Dienst: Konten, Profile und Schreiben ins Repo.

Läuft hinter nginx und lauscht nur auf 127.0.0.1. nginx liefert die statischen Dateien
selbst aus und fragt vorher per auth_request bei /api/auth nach, ob die Person rein darf.

Den Login macht Authentik (Single Sign-on) über den Nginx Proxy Manager (NPM). NPM schickt
nach dem Login den Authentik-Benutzernamen und die Gruppen als Header mit. Der Dienst glaubt
diesen Headern nur, wenn auch das geheime Proxy-Passwort (CAMPUS_PROXY_GEHEIMNIS) mitkommt,
das nur NPM kennt. Wer welches Campus-Konto ist, steht in konten.json (Feld "authentik").
Admin ist, wer in Authentik in der Gruppe CAMPUS_ADMIN_GRUPPE ist.

Nutzung:  python3 server/dienst.py
Braucht:  Python ab 3.9 und git, keine Zusatzpakete

Einstellungen kommen aus Umgebungsvariablen (siehe server/campus-dienst.service):
  CAMPUS_REPO     Pfad zum Repo-Checkout            (Standard: Ordner über server/)
  CAMPUS_DATEN    Konten, Sperrdateien, Import     (Standard: /var/lib/campus)
  CAMPUS_ADRESSE  Adresse zum Lauschen              (Standard: 127.0.0.1)
  CAMPUS_PORT     Port                              (Standard: 8090)
  CAMPUS_BRANCH   Branch, auf den geschrieben wird  (Standard: main)
  CAMPUS_REMOTE   Remote für fetch und push         (Standard: origin, leer = ohne GitHub)
  CAMPUS_PROXY_GEHEIMNIS  muss im Header X-Campus-Proxy mitkommen (Pflicht, sonst kommt niemand rein)
  CAMPUS_ADMIN_GRUPPE     Authentik-Gruppe der Admins   (Standard: tofg-users)

Die Konten (Zuordnung Authentik-Name zu Campus-Konto) liegen in CAMPUS_DATEN, nie im Repo.
Ins Repo kommen nur die öffentlichen Profilfelder unter team/.
"""
import fcntl
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import karte as karte_modul
from fehler import Fehler

HIER = Path(__file__).resolve().parent

# --- Einstellungen ---

REPO = Path(os.environ.get("CAMPUS_REPO") or HIER.parent).resolve()
DATEN = Path(os.environ.get("CAMPUS_DATEN") or "/var/lib/campus")
ADRESSE = os.environ.get("CAMPUS_ADRESSE") or "127.0.0.1"
PORT = int(os.environ.get("CAMPUS_PORT") or 8090)
BRANCH = os.environ.get("CAMPUS_BRANCH") or "main"
REMOTE = os.environ.get("CAMPUS_REMOTE", "origin")
PROXY_GEHEIMNIS = os.environ.get("CAMPUS_PROXY_GEHEIMNIS") or ""
ADMIN_GRUPPE = os.environ.get("CAMPUS_ADMIN_GRUPPE") or "tofg-users"

MAX_ANFRAGE = 64 * 1024             # größte erlaubte Anfrage an die API in Byte

# Nur diese Ordner darf der Dienst im Repo beschreiben
SCHREIBBAR = ("team/", "kanban/", "gebaeude/", "schematics/", "download/")

ID_MUSTER = re.compile(r"^[a-z][a-z0-9-]{1,23}$")
AUTHENTIK_MUSTER = re.compile(r"^[A-Za-z0-9._@+-]{1,150}$")
MC_MUSTER = re.compile(r"^[A-Za-z0-9_]{3,16}$")
FARB_MUSTER = re.compile(r"^#[0-9a-f]{6}$")
FARBEN = ["#d9840b", "#3c7fc4", "#4f9a3a", "#b0457a", "#7a5cc4", "#c4553c", "#2f9a94", "#8a7a2a"]


def jetzt():
    return time.time()


def zeitstempel(t=None):
    return datetime.fromtimestamp(t if t is not None else jetzt(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(*teile):
    print(zeitstempel(), *teile, file=sys.stderr, flush=True)


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


# --- Konten ---

def authentik_pruefen(name):
    if not isinstance(name, str) or not AUTHENTIK_MUSTER.match(name):
        raise Fehler(400, "Authentik-Benutzername fehlt oder enthält ungültige Zeichen.")


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

    def anlegen(self, kid, authentik):
        if not ID_MUSTER.match(kid or ""):
            raise Fehler(400, "Kontoname: 2 bis 24 Zeichen, nur a-z, 0-9 und Bindestrich, vorne ein Buchstabe.")
        authentik_pruefen(authentik)
        with self.aendern() as k:
            if kid in k:
                raise Fehler(409, "Das Konto „%s“ gibt es schon." % kid)
            self._schon_vergeben(k, authentik, kid)
            k[kid] = dict(authentik=authentik, gesperrt=False, angelegt=zeitstempel(), letzter_login=None)

    def authentik_setzen(self, kid, authentik):
        authentik_pruefen(authentik)
        with self.aendern() as k:
            if kid not in k:
                raise Fehler(404, "Konto nicht gefunden.")
            self._schon_vergeben(k, authentik, kid)
            k[kid]["authentik"] = authentik

    @staticmethod
    def _schon_vergeben(k, authentik, kid):
        for andere, konto in k.items():
            if andere != kid and str(konto.get("authentik", "")).lower() == authentik.lower():
                raise Fehler(409, "Der Authentik-Name „%s“ gehört schon zum Konto „%s“." % (authentik, andere))

    def zu_authentik(self, name):
        """(Konto-ID, Konto) zum Authentik-Benutzernamen, Groß- und Kleinschreibung egal."""
        name = (name or "").lower()
        if not name:
            return None, None
        for kid, konto in self._lies().items():
            if str(konto.get("authentik", "")).lower() == name:
                return kid, konto
        return None, None

    def setze(self, kid, **felder):
        with self.aendern() as k:
            if kid not in k:
                raise Fehler(404, "Konto nicht gefunden.")
            k[kid].update(felder)


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
        with self.gesperrt():
            self.aktualisieren()
            for pfad, version in erwartet.items():
                if blob_version(self.repo / pfad) != version:
                    raise Fehler(409, "%s wurde inzwischen von jemand anderem geändert. Nichts gespeichert. "
                                      "Bitte die Seite neu laden und es noch einmal versuchen." % (bezeichnung or pfad))
            return self.schreibe_gesperrt(dateien, nachricht, autor)

    def schreibe_gesperrt(self, dateien, nachricht, autor):
        """Schreiben, committen, pushen. Nur innerhalb von gesperrt() nach aktualisieren() aufrufen."""
        for pfad in dateien:
            if ".." in pfad.split("/") or not pfad.startswith(SCHREIBBAR) or pfad.startswith("/"):
                raise Fehler(400, "Pfad nicht erlaubt: %s" % pfad)
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
    git = Git(REPO, DATEN / "git.lock")
    return {
        "konten": Konten(DATEN),
        "zuletzt": {},          # wann letzter_login zuletzt geschrieben wurde, pro Konto
        "git": git,
        "karte": karte_modul.Karte(git, DATEN, log),
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

    def vom_proxy(self):
        """Kommt die Anfrage wirklich über NPM? Nur dann zählen die Authentik-Header."""
        if not PROXY_GEHEIMNIS:
            return False
        return hmac.compare_digest((self.headers.get("X-Campus-Proxy") or "").encode(), PROXY_GEHEIMNIS.encode())

    def authentik(self):
        """(Benutzername, Gruppen) aus den Headern von Authentik, oder (None, []) ohne gültigen Proxy."""
        if not self.vom_proxy():
            return None, []
        name = (self.headers.get("X-authentik-username") or "").strip()
        gruppen = [g.strip() for g in (self.headers.get("X-authentik-groups") or "").split("|") if g.strip()]
        return (name or None), gruppen

    def wer(self):
        """(id, konto) der angemeldeten Person oder (None, None). konto["admin"] kommt aus der Gruppe."""
        name, gruppen = self.authentik()
        kid, konto = self.d["konten"].zu_authentik(name)
        if not kid or konto.get("gesperrt"):
            return None, None
        konto = dict(konto, admin=ADMIN_GRUPPE in gruppen)
        self.merke_login(kid)
        return kid, konto

    def merke_login(self, kid):
        """letzter_login höchstens alle 10 Minuten auf die Platte schreiben."""
        if jetzt() - self.d["zuletzt"].get(kid, 0) < 600:
            return
        self.d["zuletzt"][kid] = jetzt()
        try:
            self.d["konten"].setze(kid, letzter_login=zeitstempel())
        except (Fehler, OSError):
            pass

    def eingeloggt(self, admin=False):
        kid, konto = self.wer()
        if not kid:
            raise Fehler(401, "Nicht angemeldet oder kein Campus-Konto.")
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

    # -- Anmeldung --

    def auth(self):
        """Für nginx auth_request: 204 = darf rein, 401 = nicht über NPM, 403 = kein Campus-Konto."""
        name, _ = self.authentik()
        if not name:
            if not PROXY_GEHEIMNIS:
                log("CAMPUS_PROXY_GEHEIMNIS ist nicht gesetzt, niemand kommt rein.")
            return self.antwort(401)
        kid, _ = self.wer()
        if kid:
            return self.antwort(204, kopf={"X-Campus-Konto": kid})
        log("Kein aktives Campus-Konto für Authentik-Name", name)
        return self.antwort(403)

    def ich(self):
        kid, konto = self.wer()
        if not kid:
            raise Fehler(401, "Nicht angemeldet.")
        p = lies_profil(kid) or {}
        self.antwort(200, {"id": kid, "admin": bool(konto.get("admin")), "authentik": konto.get("authentik"),
                           "anzeigename": p.get("anzeigename") or kid, "farbe": p.get("farbe"),
                           "minecraft": p.get("minecraft")})

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
        felder = ("authentik", "gesperrt", "angelegt", "letzter_login")
        aus = []
        for kid, k in sorted(self.d["konten"].alle().items()):
            p = lies_profil(kid) or {}
            aus.append(dict({f: k.get(f) for f in felder}, id=kid, anzeigename=p.get("anzeigename") or kid))
        self.antwort(200, {"konten": aus, "adminGruppe": ADMIN_GRUPPE})

    def konto_anlegen(self):
        kid, _ = self.eingeloggt(admin=True)
        e = self.eingabe()
        neu = str(e.get("id", "")).strip().lower()
        profil_pruefen(neu if ID_MUSTER.match(neu) else "x", e)   # Eingaben vorab prüfen
        self.d["konten"].anlegen(neu, str(e.get("authentik", "")).strip())
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
        if ziel == kid and aktion in ("sperren", "authentik"):
            raise Fehler(400, "Das geht nicht beim eigenen Konto.")
        if aktion == "sperren":
            konten.setze(ziel, gesperrt=True)
        elif aktion == "entsperren":
            konten.setze(ziel, gesperrt=False)
        elif aktion == "authentik":
            konten.authentik_setzen(ziel, str(e.get("authentik", "")).strip())
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

    # -- Karte: Import und Versionen --

    def import_status(self):
        kid, _ = self.eingeloggt()
        k = self.d["karte"]
        s = k.status()
        self.antwort(200, {"import": dict(s, meins=s["wer"] == kid) if s else None,
                           "ecke": k.letzte_ecke(), "gebaeude": k.gebaeude(),
                           "maxUploadMB": karte_modul.MAX_UPLOAD // 1024 // 1024})

    def import_hochladen(self):
        kid, _ = self.eingeloggt()
        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge > karte_modul.MAX_UPLOAD:
            raise Fehler(413, "Die Datei ist größer als %d MB." % (karte_modul.MAX_UPLOAD // 1024 // 1024))
        if laenge <= 0:
            raise Fehler(400, "Keine Datei.")
        q = parse_qs(urlsplit(self.path).query)
        try:
            ecke = [int(v) for v in (q.get("ecke") or [""])[0].split(",")]
        except ValueError:
            raise Fehler(400, "Die Ecke bitte als drei ganze Zahlen x, y, z.")
        roh = self.rfile.read(laenge)
        k = self.d["karte"]
        k.hochladen(kid, autor_von(kid)[0], roh, (q.get("name") or ["Schematic"])[0])
        s = k.vorschau(kid, ecke, {})
        self.antwort(200, {"import": dict(s, meins=True)})

    def import_vorschau(self):
        kid, _ = self.eingeloggt()
        e = self.eingabe()
        s = self.d["karte"].vorschau(kid, e.get("ecke"), e.get("einstellungen") or {})
        self.antwort(200, {"import": dict(s, meins=True)})

    def import_modell(self, gid):
        kid, _ = self.eingeloggt()
        inhalt = self.d["karte"].modell(kid, gid)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(inhalt)

    def import_uebernehmen(self):
        kid, _ = self.eingeloggt()
        commit = self.d["karte"].uebernehmen(kid, autor_von(kid))
        self.antwort(200, {"ok": True, "commit": commit})

    def import_verwerfen(self):
        kid, konto = self.eingeloggt()
        self.d["karte"].verwerfen(kid, bool(konto.get("admin")))
        self.antwort(200, {"ok": True})

    def versionen(self):
        self.eingeloggt()
        q = parse_qs(urlsplit(self.path).query)
        try:
            ab = max(0, int((q.get("ab") or ["0"])[0]))
        except ValueError:
            ab = 0
        self.antwort(200, {"versionen": self.d["karte"].versionen(ab), "github": github_adresse(self.d["git"])})

    def wiederherstellen(self, commit):
        kid, _ = self.eingeloggt(admin=True)
        neu = self.d["karte"].wiederherstellen(commit, kid, autor_von(kid))
        log("Karte zurückgesetzt auf", commit, "von", kid)
        self.antwort(200, {"ok": True, "commit": neu})

    def stand(self):
        """Aktueller Commit, damit offene Seiten merken, dass es etwas Neues gibt."""
        self.eingeloggt()
        self.antwort(200, {"commit": self.d["git"].kopf()})


def github_adresse(git):
    """https://github.com/<besitzer>/<repo> aus der Remote-Adresse, sonst None."""
    url = git.git("remote", "get-url", git.remote, pruefen=False).stdout.strip() if git.remote else ""
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(\.git)?$", url)
    return "https://github.com/" + m.group(1) if m else None


def _r(methode, muster, funktion):
    return (methode, re.compile("^" + muster + "$"), funktion)


ROUTEN = [
    _r("GET", r"/api/auth", Handler.auth),
    _r("GET", r"/api/ich", Handler.ich),
    _r("GET", r"/api/stand", Handler.stand),
    _r("GET", r"/api/profil/([a-z][a-z0-9-]{1,23})", Handler.profil_lesen),
    _r("POST", r"/api/profil/([a-z][a-z0-9-]{1,23})", Handler.profil_speichern),
    _r("GET", r"/api/kanban", Handler.kanban),
    _r("POST", r"/api/karten", Handler.karte_neu),
    _r("POST", r"/api/karten/(" + KARTEN_ID + r")", Handler.karte_aendern),
    _r("POST", r"/api/karten/(" + KARTEN_ID + r")/loeschen", Handler.karte_loeschen),
    _r("GET", r"/api/import/status", Handler.import_status),
    _r("POST", r"/api/import/hochladen", Handler.import_hochladen),
    _r("POST", r"/api/import/vorschau", Handler.import_vorschau),
    _r("GET", r"/api/import/modell/([a-z0-9-]{1,48})", Handler.import_modell),
    _r("POST", r"/api/import/uebernehmen", Handler.import_uebernehmen),
    _r("POST", r"/api/import/verwerfen", Handler.import_verwerfen),
    _r("GET", r"/api/versionen", Handler.versionen),
    _r("POST", r"/api/versionen/([0-9a-f]{40})/wiederherstellen", Handler.wiederherstellen),
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
    if not PROXY_GEHEIMNIS:
        log("Achtung: CAMPUS_PROXY_GEHEIMNIS fehlt, so kommt niemand rein. Siehe README, Server einrichten.")
    log("Campus-Dienst läuft auf %s:%d, Repo %s, Daten %s, Admin-Gruppe %s" % (ADRESSE, PORT, REPO, DATEN, ADMIN_GRUPPE))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
