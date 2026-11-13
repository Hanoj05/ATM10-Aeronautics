# ATM10 Aeronautics – Campus

Doku zu unserem Tech-Campus in der ATM10-Aeronautics-Welt. Jedes Gebäude hat eine Aufgabe (Bienen, ME, …) und einen eigenen Ordner mit Modell und Konfiguration. Daraus soll später eine Website werden: eine 3D-Ansicht vom ganzen Campus, in der man jedes Gebäude anklicken kann und dann dessen Übersicht bekommt.

## Aufbau

```
campus/
  campus.json          Liste aller Gebäude mit Lage in der Welt
gebaeude/
  vorlage/             Kopiervorlage für ein neues Gebäude
  wabenhaus/           Bienengebäude
    gebaeude.json      Steckbrief: Zellen, Maße, P0, Drehung, Dateien
    bauplan.html       Bauanleitung Block für Block
    modell.json        Blockmodell für die 3D-Ansicht
    konfig.json        Teile mit Position, Nodes und Kanälen (für die Website)
    konfig.md          Technik und Konfiguration zum Lesen
  me-zentrale/         ME-Gebäude
  hauptgebaeude/       Glasring mit Park und Energy Core
  magiehaus/           Pentagramm mit fünf Magie-Flügeln
  aussenanlagen/       Wege, Bäume, Teiche, Laternen zwischen den Gebäuden
schematics/
  campus.nbt           die ganze Campus-Fläche, daraus werden alle Modelle ausgeschnitten
kanban/                Kanban-Board: Phasen und eine Datei pro Karte, angezeigt auf website/kanban.html
team/                  Öffentliche Profile (Anzeigename, Minecraft-Name, Farbe, Info), keine Login-Daten
texturen/              Blocktexturen für die 3D-Ansicht (Atlas plus Zuordnung), erzeugt mit tools/hole-texturen.py
tools/                 Hilfsskripte: modell.json aus Bauplan oder Schematic, Texturen holen, Zip bauen
website/               Die Campus-Website
server/                Campus-Dienst (Login, Speichern), nginx-Konfiguration, systemd-Units
download/              campus-ansicht.zip: nur Map und 3D-Ansicht, offline per Doppelklick
```

## Website ansehen

```
python3 -m http.server 8000
```

im Repo-Ordner starten und `http://localhost:8000` öffnen. Details in [website/README.md](website/README.md). Lokal gibt es keinen Login, die Team-Seite ist dann nur zum Lesen und die Admin-Seite geht nicht.

Online läuft die Seite auf unserem Server hinter einem Login, siehe [Server einrichten](#server-einrichten).

Ohne Server und ohne Technik: [download/campus-ansicht.zip](download/campus-ansicht.zip) entpacken und `index.html` öffnen.

## Neues Gebäude anlegen

1. Ordner `gebaeude/vorlage` kopieren und umbenennen, zum Beispiel `gebaeude/me-zentrale`.
2. `gebaeude.json` ausfüllen, vor allem `id`, `name` und `zweck`.
3. Das Gebäude in `campus/campus.json` eintragen.
4. `konfig.json` und `konfig.md` nach und nach füllen, dann erscheinen die Teile auf der Website.

## Gebäude

| Gebäude | Zweck | Status |
| --- | --- | --- |
| [Wabenhaus](gebaeude/wabenhaus/) | Bienen: Modular Beehive, Modular Centrifuge | gebaut |
| [ME-Gebäude](gebaeude/me-zentrale/) | AE2-Hauptsystem: ME Controller, 64 Extended Drives | im Bau |
| [Hauptgebäude](gebaeude/hauptgebaeude/) | Glasring mit Park und Energy Core | geplant |
| [Magiehaus](gebaeude/magiehaus/) | Ars Nouveau, Occultism, Iron's Spells, Forbidden & Arcanus, EvilCraft, Apothic Enchanting | geplant |
| [Außenanlagen](gebaeude/aussenanlagen/) | Wege, Haine, Wiesen, Teiche, Laternen zwischen den Gebäuden | geplant |

## Konventionen

- Block- und Itemnamen auf Englisch, so wie sie im Spiel und im JEI heißen.
- Koordinaten im Bauplan sind relativ zum Punkt P0 des Gebäudes. Die Weltkoordinate von P0 steht in `gebaeude.json` unter `welt.p0`.
- Keine versteckten Dateien. Leere Ordner bekommen eine `README.md`.

## Server einrichten

So läuft die Website auf dem eigenen Server: nginx liefert die Dateien direkt aus dem Repo aus, fragt aber bei jedem Aufruf den Campus-Dienst (`server/dienst.py`), ob der Login gültig ist. Ohne Login gibt es nur die Login-Seite. Änderungen über die Website (zum Beispiel ein Profil) schreibt der Dienst als Commit ins Repo und pusht sie nach GitHub. Ein Timer holt alle 2 Minuten den Stand von GitHub, damit auch Pushes vom eigenen PC online ankommen.

| Was | Wo auf dem Server |
| --- | --- |
| Repo-Checkout | `/srv/campus/repo`, gehört dem Nutzer `campus` |
| Konten, Passwort-Hashes, Sitzungen | `/var/lib/campus/` (nie im Repo) |
| Deploy-Key und `known_hosts` für GitHub | `/etc/campus/` |
| nginx-Konfiguration | `/etc/nginx/conf.d/campus.conf`, Vorlage `server/nginx-campus.conf` |
| Dienst und Timer | `/etc/systemd/system/`, Vorlagen `server/campus-dienst.service`, `server/campus-pull.service`, `server/campus-pull.timer` |

Die Anleitung ist für CentOS Stream 9 oder 10. Alle Befehle als normaler Nutzer mit `sudo`. Wo `campus.example.org` steht, kommt deine Domain hin.

### 1. Voraussetzungen prüfen

- Die Domain zeigt per DNS (A-Record, bei IPv6 auch AAAA) auf den Server.
- `cat /etc/os-release` zeigt CentOS Stream 9 oder 10.

### 2. Pakete

```
sudo dnf install -y python3 git nginx policycoreutils-python-utils
sudo dnf config-manager --set-enabled crb
sudo dnf install -y epel-release
sudo dnf install -y certbot python3-certbot-nginx
python3 --version
```

`python3 --version` muss 3.9 oder neuer zeigen. Der Dienst braucht keine Zusatzpakete aus pip.

### 3. Nutzer `campus`

Ein Systemnutzer ohne Login, dem das Repo gehört. Der Home-Ordner wird von Hand angelegt, so landen keine versteckten Vorlage-Dateien darin.

```
sudo useradd --system --no-create-home --home-dir /srv/campus --shell /usr/sbin/nologin campus
sudo mkdir -p /srv/campus
sudo chown campus:campus /srv/campus
sudo chmod 755 /srv/campus
```

### 4. Deploy-Key für GitHub

Der Server bekommt einen eigenen Schlüssel, der nur für dieses eine Repo gilt und schreiben darf.

```
sudo mkdir -p /etc/campus
sudo ssh-keygen -t ed25519 -N "" -C "campus-server" -f /etc/campus/deploy-key
ssh-keyscan -t ed25519 github.com | sudo tee /etc/campus/known_hosts
sudo chown -R campus:campus /etc/campus
sudo chmod 700 /etc/campus
sudo chmod 600 /etc/campus/deploy-key
ssh-keygen -lf /etc/campus/known_hosts
```

Der letzte Befehl muss `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU` zeigen, so steht es bei GitHub unter „GitHub's SSH key fingerprints“. Wenn nicht: abbrechen, dann redet der Server nicht mit dem echten GitHub.

Dann den öffentlichen Schlüssel anzeigen:

```
sudo cat /etc/campus/deploy-key.pub
```

Auf GitHub im Repo unter **Settings → Deploy keys → Add deploy key** einfügen, Titel zum Beispiel `campus-server`, Haken bei **Allow write access** setzen, speichern.

### 5. Repo klonen

```
SSH_BEFEHL="ssh -i /etc/campus/deploy-key -o UserKnownHostsFile=/etc/campus/known_hosts -o IdentitiesOnly=yes"
sudo -u campus env GIT_SSH_COMMAND="$SSH_BEFEHL" git clone git@github.com:Hanoj05/ATM10-Aeronautics.git /srv/campus/repo
sudo -u campus git -C /srv/campus/repo config core.sshCommand "$SSH_BEFEHL"
sudo -u campus git -C /srv/campus/repo config pull.ff only
```

Ab jetzt nimmt Git in diesem Repo immer den Deploy-Key, auch für den Timer und den Dienst.

### 6. SELinux

CentOS lässt nginx sonst weder ins Repo schauen noch mit dem Dienst reden.

```
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/campus/repo(/.*)?"
sudo restorecon -R /srv/campus/repo
sudo setsebool -P httpd_can_network_connect 1
```

### 7. Dienst und Timer starten

```
sudo cp /srv/campus/repo/server/campus-dienst.service /srv/campus/repo/server/campus-pull.service /srv/campus/repo/server/campus-pull.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campus-dienst.service
sudo systemctl enable --now campus-pull.timer
systemctl status campus-dienst.service
```

Der Status muss `active (running)` zeigen. Der Dienst lauscht nur auf `127.0.0.1:8090`, von außen ist er nur über nginx erreichbar.

### 8. nginx

```
sudo cp /srv/campus/repo/server/nginx-campus.conf /etc/nginx/conf.d/campus.conf
sudo sed -i 's/campus.example.org/DEINE-DOMAIN/' /etc/nginx/conf.d/campus.conf
sudo nginx -t
sudo systemctl enable --now nginx
sudo firewall-cmd --permanent --add-service=http --add-service=https
sudo firewall-cmd --reload
```

`nginx -t` muss `syntax is ok` und `test is successful` melden.

### 9. HTTPS

```
sudo certbot --nginx -d DEINE-DOMAIN
sudo systemctl enable --now certbot-renew.timer
sudo certbot renew --dry-run
```

certbot fragt nach einer E-Mail-Adresse und trägt das Zertifikat selbst in `/etc/nginx/conf.d/campus.conf` ein. Wenn es fragt, ob http auf https umgeleitet werden soll: ja. Der Login geht nur über HTTPS, weil das Cookie mit `Secure` gesetzt wird.

### 10. Erste Konten

```
cd /srv/campus/repo
sudo -u campus python3 server/konto.py anlegen jonah --admin --anzeigename Jonah --minecraft Informiert
sudo -u campus python3 server/konto.py anlegen felix --anzeigename Felix --minecraft MultiBilliardaer
sudo -u campus python3 server/konto.py liste
```

Das Skript fragt jeweils nach dem Startpasswort. Beim ersten Login muss jeder ein eigenes setzen. Bis dahin kommt jeder mit Name und Startpasswort rein, also Konten erst anlegen, wenn die Person sich bald einloggt. Weitere Konten legt ein Admin danach auf der Website unter **Admin** an.

### 11. Prüfen

- `https://DEINE-DOMAIN` öffnen: Die Login-Seite erscheint, nach dem Login die Übersicht.
- `curl -sI https://DEINE-DOMAIN/.git/config` zeigt `404`.
- `curl -sI https://DEINE-DOMAIN/website/` zeigt ohne Login `302` mit `Location: /login?...`.
- Unter **Team** das eigene Profil ändern und speichern. Auf GitHub erscheint ein Commit mit dir als Autor.

### Betrieb

| Aufgabe | Befehl |
| --- | --- |
| Log des Dienstes | `journalctl -u campus-dienst -f` |
| Log vom Abgleich mit GitHub | `journalctl -u campus-pull` |
| Passwort zurücksetzen | `sudo -u campus python3 server/konto.py zuruecksetzen felix` (oder auf der Website unter Admin) |
| Konto sperren | `sudo -u campus python3 server/konto.py sperren felix` |
| Konten sichern | `/var/lib/campus/konten.json` wegkopieren |

- **Neuer Code kommt von selbst:** Der Timer holt ihn. Ändert sich etwas unter `server/*.py`, startet sich der Dienst innerhalb von 20 Sekunden selbst neu.
- **Von Hand nachziehen** muss man nur geänderte Vorlagen: nach einer Änderung an `server/nginx-campus.conf` die Datei wieder nach `/etc/nginx/conf.d/` kopieren (Domain und certbot-Zeilen behalten) und `sudo systemctl reload nginx`, nach einer Änderung an den Units wieder kopieren und `sudo systemctl daemon-reload`.
- **Wenn der Abgleich hängt:** `journalctl -u campus-pull` zeigt den Grund. Meist wurde auf GitHub die Geschichte umgeschrieben (Force-Push). Dann auf dem Server `sudo -u campus git -C /srv/campus/repo fetch` und `sudo -u campus git -C /srv/campus/repo reset --hard origin/main`.
