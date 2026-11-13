"""Konten für die Campus-Website verwalten, direkt auf dem Server.

Ein Konto verbindet einen Authentik-Benutzer mit einem Campus-Profil unter team/.
Passwörter gibt es hier nicht, den Login macht Authentik. Admin ist, wer in Authentik
in der Admin-Gruppe ist (Standard: campus-admins).

Nutzung (als Nutzer campus, damit die Dateien ihm gehören):
  sudo -u campus python3 server/konto.py liste
  sudo -u campus python3 server/konto.py anlegen jonah --authentik JOberascher --anzeigename Jonah --minecraft Informiert
  sudo -u campus python3 server/konto.py authentik felix FFoerster   (Authentik-Name ändern)
  sudo -u campus python3 server/konto.py sperren felix
  sudo -u campus python3 server/konto.py entsperren felix

Liest dieselben Umgebungsvariablen wie der Dienst (CAMPUS_DATEN, CAMPUS_REPO),
die Standardwerte passen für den Server.
"""
import argparse
import sys

sys.dont_write_bytecode = True      # kein __pycache__ im Repo
import dienst                       # noqa: E402
from fehler import Fehler      # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Konten der Campus-Website verwalten")
    ap.add_argument("aktion", choices=["liste", "anlegen", "authentik", "sperren", "entsperren"])
    ap.add_argument("id", nargs="?", help="Kontoname, z. B. felix")
    ap.add_argument("wert", nargs="?", help="bei authentik: der neue Authentik-Benutzername")
    ap.add_argument("--authentik", help="beim Anlegen: Benutzername in Authentik, z. B. FFoerster")
    ap.add_argument("--anzeigename", help="beim Anlegen: Name auf der Website")
    ap.add_argument("--minecraft", default="", help="beim Anlegen: Minecraft-Name")
    a = ap.parse_args()

    konten = dienst.Konten(dienst.DATEN)
    if a.aktion == "liste":
        alle = konten.alle()
        if not alle:
            print("Noch keine Konten.")
        for kid, k in sorted(alle.items()):
            print("%-20s Authentik: %-24s %-9s letzter Login: %s" % (
                kid, k.get("authentik") or "-", "gesperrt" if k.get("gesperrt") else "", k.get("letzter_login") or "nie"))
        print("Admin ist, wer in Authentik in der Gruppe „%s“ ist." % dienst.ADMIN_GRUPPE)
        return
    if not a.id:
        ap.error("Bitte einen Kontonamen angeben.")
    kid = a.id.strip().lower()

    try:
        if a.aktion == "anlegen":
            if not a.authentik:
                ap.error("Beim Anlegen bitte --authentik <Benutzername in Authentik> angeben.")
            eingabe = {"anzeigename": a.anzeigename or kid, "minecraft": a.minecraft}
            dienst.profil_pruefen(kid, eingabe)
            konten.anlegen(kid, a.authentik.strip())
            print("Konto %s angelegt, gehört zu Authentik-Benutzer %s." % (kid, a.authentik.strip()))
            git = dienst.Git(dienst.REPO, dienst.DATEN / "git.lock")
            if dienst.profil_anlegen(git, kid, eingabe, ("Campus-Website", "website@campus.invalid")):
                print("Profil team/%s.json angelegt und nach GitHub geschickt." % kid)
            else:
                print("Profil team/%s.json gab es schon." % kid)
        elif a.aktion == "authentik":
            if not a.wert:
                ap.error("Bitte den neuen Authentik-Benutzernamen angeben.")
            konten.authentik_setzen(kid, a.wert.strip())
            print("%s gehört jetzt zu Authentik-Benutzer %s." % (kid, a.wert.strip()))
        elif a.aktion == "sperren":
            konten.setze(kid, gesperrt=True)
            print("%s gesperrt." % kid)
        elif a.aktion == "entsperren":
            konten.setze(kid, gesperrt=False)
            print("%s entsperrt." % kid)
    except Fehler as f:
        print("Fehler:", f.text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
