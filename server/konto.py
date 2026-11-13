"""Konten für die Campus-Website verwalten, direkt auf dem Server.

Nutzung (als Nutzer campus, damit die Dateien ihm gehören):
  sudo -u campus python3 server/konto.py liste
  sudo -u campus python3 server/konto.py anlegen jonah --admin --anzeigename Jonah --minecraft Informiert
  sudo -u campus python3 server/konto.py zuruecksetzen felix
  sudo -u campus python3 server/konto.py sperren felix
  sudo -u campus python3 server/konto.py entsperren felix
  sudo -u campus python3 server/konto.py admin felix        (Admin-Recht geben)
  sudo -u campus python3 server/konto.py kein-admin felix   (Admin-Recht wegnehmen)

Das Startpasswort wird abgefragt und nicht angezeigt. Beim ersten Login muss die Person
ein eigenes setzen. Liest dieselben Umgebungsvariablen wie der Dienst (CAMPUS_DATEN, CAMPUS_REPO),
die Standardwerte passen für den Server.
"""
import argparse
import getpass
import sys
import time

sys.dont_write_bytecode = True      # kein __pycache__ im Repo
import dienst                       # noqa: E402
from fehler import Fehler      # noqa: E402


def startpasswort():
    while True:
        eins = getpass.getpass("Startpasswort: ")
        zwei = getpass.getpass("Noch einmal: ")
        if eins != zwei:
            print("Die beiden Eingaben sind verschieden, bitte noch einmal.")
            continue
        try:
            dienst.passwort_pruefen(eins)
        except Fehler as f:
            print(f.text)
            continue
        return eins


def main():
    ap = argparse.ArgumentParser(description="Konten der Campus-Website verwalten")
    ap.add_argument("aktion", choices=["liste", "anlegen", "zuruecksetzen", "sperren", "entsperren", "admin", "kein-admin"])
    ap.add_argument("id", nargs="?", help="Kontoname, z. B. felix")
    ap.add_argument("--admin", action="store_true", help="beim Anlegen: Admin-Recht geben")
    ap.add_argument("--anzeigename", help="beim Anlegen: Name auf der Website")
    ap.add_argument("--minecraft", default="", help="beim Anlegen: Minecraft-Name")
    a = ap.parse_args()

    konten = dienst.Konten(dienst.DATEN)
    if a.aktion == "liste":
        alle = konten.alle()
        if not alle:
            print("Noch keine Konten.")
        for kid, k in sorted(alle.items()):
            merkmale = [m for m, an in (("Admin", k.get("admin")), ("gesperrt", k.get("gesperrt")),
                                       ("Startpasswort", k.get("muss_aendern"))) if an]
            print("%-24s %-40s letzter Login: %s" % (kid, ", ".join(merkmale) or "Mitglied", k.get("letzter_login") or "nie"))
        return
    if not a.id:
        ap.error("Bitte einen Kontonamen angeben.")
    kid = a.id.strip().lower()

    try:
        if a.aktion == "anlegen":
            eingabe = {"anzeigename": a.anzeigename or kid, "minecraft": a.minecraft}
            dienst.profil_pruefen(kid, eingabe)
            konten.anlegen(kid, startpasswort(), a.admin)
            print("Konto %s angelegt%s." % (kid, " (Admin)" if a.admin else ""))
            git = dienst.Git(dienst.REPO, dienst.DATEN / "git.lock")
            if dienst.profil_anlegen(git, kid, eingabe, ("Campus-Website", "website@campus.invalid")):
                print("Profil team/%s.json angelegt und nach GitHub geschickt." % kid)
            else:
                print("Profil team/%s.json gab es schon." % kid)
        elif a.aktion == "zuruecksetzen":
            konten.passwort_setzen(kid, startpasswort(), muss_aendern=True)
            print("Passwort von %s zurückgesetzt, alle Logins beendet. Beim nächsten Login muss ein neues her." % kid)
        elif a.aktion == "sperren":
            konten.setze(kid, gesperrt=True, sitzungen_ab=time.time())
            print("%s gesperrt und ausgeloggt." % kid)
        elif a.aktion == "entsperren":
            konten.setze(kid, gesperrt=False)
            print("%s entsperrt." % kid)
        elif a.aktion == "admin":
            konten.setze(kid, admin=True)
            print("%s ist jetzt Admin." % kid)
        elif a.aktion == "kein-admin":
            konten.setze(kid, admin=False)
            print("%s ist jetzt Mitglied." % kid)
    except Fehler as f:
        print("Fehler:", f.text, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
