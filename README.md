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
team/                  Öffentliche Profile (Anzeigename, Minecraft-Name, Farbe, Info), keine Konto-Daten
texturen/              Blocktexturen für die 3D-Ansicht (Atlas plus Zuordnung), erzeugt mit tools/hole-texturen.py
tools/                 Hilfsskripte: modell.json aus Bauplan oder Schematic, Texturen holen, Zip bauen
website/               Die Campus-Website
server/                Campus-Dienst (Konten, Speichern), nginx-Konfiguration, systemd-Units
download/              campus-ansicht.zip: nur Map und 3D-Ansicht, offline per Doppelklick
```

## Website ansehen

```
python3 -m http.server 8000
```

im Repo-Ordner starten und `http://localhost:8000` öffnen. Details in [website/README.md](website/README.md). Lokal gibt es keine Anmeldung, die Team-Seite ist dann nur zum Lesen und die Admin-Seite geht nicht.

Online läuft die Seite auf unserem Server hinter der Authentik-Anmeldung (Single Sign-on), siehe [Server einrichten](#server-einrichten).

Ohne Server und ohne Technik: [download/campus-ansicht.zip](download/campus-ansicht.zip) entpacken und `index.html` öffnen.

## Neues Gebäude anlegen

1. Ordner `gebaeude/vorlage` kopieren und umbenennen, zum Beispiel `gebaeude/me-zentrale`.
2. `gebaeude.json` ausfüllen, vor allem `id`, `name` und `zweck`.
3. Das Gebäude in `campus/campus.json` eintragen.
4. `konfig.json` und `konfig.md` nach und nach füllen, dann erscheinen die Teile auf der Website.

## Karte aktualisieren

Für alle, die die 3D-Karte auf den Stand der Welt bringen wollen. Du brauchst nur Minecraft und den Browser.

### In Minecraft: die Schematic speichern

1. Ein **Schematic and Quill** (aus Create) craften und in die Hand nehmen.
2. Auf der Website unter **Import** steht die Ecke vom letzten Mal, zum Beispiel `221, 65, -391`. Geh in der Welt genau zu diesem Block (mit F3 siehst du die Koordinaten) und klick ihn als erste Ecke an.
3. Die zweite Ecke diagonal gegenüber anklicken: so weit, dass alle Gebäude drin sind, und höher als das höchste Gebäude. Mit Strg und Mausrad lässt sich die Auswahl noch vergrößern.
4. Speichern und einen Namen vergeben, zum Beispiel `campus`.
5. Die Datei liegt jetzt im Ordner `schematics` deiner Minecraft-Instanz, neben `mods` und `saves`. In Prism: Instanz anklicken, **Ordner** öffnen.

Wichtig: Unten auf Bodenhöhe anfangen, sonst fehlt der Boden. Wählst du eine andere erste Ecke, musst du auf der Website die neue Koordinate eintragen: das kleinste x, das kleinste y und das kleinste z deiner Auswahl.

### Auf der Website: hochladen und prüfen

1. Einloggen, oben rechts auf **Import**.
2. Die Datei auswählen. Die Ecke ist schon eingetragen, nur ändern, wenn du in Minecraft eine andere erste Ecke genommen hast.
3. **Hochladen und Vorschau** und kurz warten. Bis du übernimmst, ändert sich an der Website noch nichts.
4. Die Vorschau prüfen:
   - **Tabelle:** pro Gebäude, wie viele Blöcke es vorher und nachher hat. Ist eine Zeile rot („verliert … % der Blöcke“), war meistens die Auswahl zu klein oder die Ecke falsch. Dann **Verwerfen** und noch einmal.
   - **3D-Ansicht:** bei „Unterschied“ ist grün dazugekommen und rot weggefallen. Oben lässt sich ein einzelnes Gebäude auswählen.
   - **Neue Blöcke ohne Textur:** harmlos, sie sind erst einmal einfarbig. Die Texturen holt Jonah später am PC.
   - **Gebautes außerhalb aller Gebäude:** vielleicht ein neues Gebäude. Das wird nicht von allein angelegt, sag Bescheid oder leg eine Karte im Kanban an.
   - **Modell aus:** nur nach Absprache ändern. „Schematic“ heißt: so wie in der Welt. „Entwurfs-Skript“ heißt: der Plan, für Gebäude, die noch nicht fertig sind. Nach einer Änderung **Mit diesen Einstellungen neu berechnen**.
5. Passt alles: **Übernehmen**. Gab es Warnungen, musst du vorher bestätigen, dass du sie gesehen hast. Danach zeigt die Map den neuen Stand.

Es kann immer nur einer gleichzeitig importieren. Steht oben, dass gerade jemand anderes dran ist, warte einfach. Spätestens nach 30 Minuten ist wieder frei.

### Wenn etwas schiefgegangen ist

Ein Admin geht auf **Versionen**, wählt oben **Karte** und klickt beim letzten guten Stand auf **Diesen Kartenstand wiederherstellen** (zweimal, zur Sicherheit). Das holt Schematic und Modelle zurück, als neuer Eintrag im Verlauf. Kanban und Profile bleiben dabei unverändert.

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

So läuft die Website online:

```
Browser ──https──> Nginx Proxy Manager (Docker) ──http──> Campus-Server (CentOS)
                     │  Anmeldung über Authentik           nginx: Dateien aus dem Repo
                     └─ schickt Benutzername, Gruppen      Campus-Dienst: Konten, Speichern, Git
                        und das Proxy-Geheimnis mit
```

- **Authentik** macht den Login (Single Sign-on). Passwörter gibt es auf der Website keine.
- **Nginx Proxy Manager (NPM)** steht davor, macht HTTPS und fragt bei Authentik nach, ob jemand angemeldet ist. Danach schickt er den Authentik-Benutzernamen, die Gruppen und ein geheimes Proxy-Passwort an den Campus-Server.
- **Campus-Server:** nginx liefert die Dateien direkt aus dem Repo aus, fragt aber bei jedem Aufruf den Campus-Dienst (`server/dienst.py`), ob die Person rein darf. Der Dienst glaubt dem Benutzernamen nur, wenn das Proxy-Geheimnis stimmt, und schaut nach, welches Campus-Konto dazugehört.
- **Admin** ist, wer in Authentik in der Gruppe `campus-admins` ist.
- Änderungen über die Website (Profil, Kanban, Import) schreibt der Dienst als Commit mit der Person als Autor ins Repo und pusht sie nach GitHub. Ein Timer holt alle 2 Minuten den Stand von GitHub, damit auch Pushes vom eigenen PC online ankommen.

| Was | Wo |
| --- | --- |
| Repo-Checkout | Campus-Server: `/srv/campus/repo`, gehört dem Nutzer `campus` |
| Konten (welcher Authentik-Name welches Konto ist) | Campus-Server: `/var/lib/campus/konten.json` (nie im Repo) |
| Deploy-Key und `known_hosts` für GitHub | Campus-Server: `/etc/campus/` |
| Proxy-Geheimnis | Campus-Server: `/etc/campus/dienst.env`, dazu dieselbe Zeichenkette im NPM |
| nginx-Konfiguration | Campus-Server: `/etc/nginx/conf.d/campus.conf`, Vorlage `server/nginx-campus.conf` |
| Dienst und Timer | Campus-Server: `/etc/systemd/system/`, Vorlagen `server/campus-dienst.service`, `server/campus-pull.service`, `server/campus-pull.timer` |
| HTTPS-Zertifikat | NPM |
| Benutzer, Gruppen, Passwörter | Authentik |

Die Anleitung ist für CentOS Stream 9 oder 10 auf dem Campus-Server. Alle Befehle dort als normaler Nutzer mit `sudo`. Platzhalter:

- `DEINE-DOMAIN`: die Adresse der Website, zum Beispiel `campus.example.org`
- `NPM-IP`: die IP-Adresse, mit der NPM beim Campus-Server ankommt (bei Docker die des Docker-Hosts)
- `CAMPUS-IP`: die IP-Adresse des Campus-Servers
- `AUTHENTIK-OUTPOST`: Adresse des Authentik-Outposts aus Sicht von NPM, beim eingebauten Outpost zum Beispiel `http://192.168.1.20:9000`

### 1. Voraussetzungen prüfen

- Die Domain zeigt per DNS auf den NPM (nicht auf den Campus-Server).
- NPM erreicht den Campus-Server auf Port 80. Vom NPM-Host aus: `curl -sI http://CAMPUS-IP` (am Anfang darf das noch fehlschlagen, nginx kommt in Schritt 9).
- NPM erreicht den Authentik-Outpost.
- `cat /etc/os-release` auf dem Campus-Server zeigt CentOS Stream 9 oder 10.

### 2. Pakete

```
sudo dnf install -y python3 git nginx policycoreutils-python-utils
python3 --version
```

`python3 --version` muss 3.9 oder neuer zeigen. Der Dienst braucht keine Zusatzpakete aus pip. certbot braucht es nicht, HTTPS macht NPM.

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

Die Zeile beginnt mit `ssh-ed25519` und endet mit `campus-server`. Auf GitHub im Repo unter **Settings → Deploy keys → Add deploy key** einfügen, Titel `campus-server`, Haken bei **Allow write access** setzen, speichern. Das geht nur mit Admin-Rechten im Repo, also die Zeile an Jonah schicken. Die Datei ohne `.pub` ist der private Schlüssel und verlässt den Server nie.

### 5. Repo klonen

```
SSH_BEFEHL="ssh -i /etc/campus/deploy-key -o UserKnownHostsFile=/etc/campus/known_hosts -o IdentitiesOnly=yes"
sudo -u campus env GIT_SSH_COMMAND="$SSH_BEFEHL" git clone git@github.com:Hanoj05/ATM10-Aeronautics.git /srv/campus/repo
sudo -u campus git -C /srv/campus/repo config core.sshCommand "$SSH_BEFEHL"
sudo -u campus git -C /srv/campus/repo config pull.ff only
```

Ab jetzt nimmt Git in diesem Repo immer den Deploy-Key, auch für den Timer und den Dienst.

### 6. Proxy-Geheimnis

Eine lange Zufallszeichenkette, die nur NPM und der Campus-Dienst kennen. Ohne sie glaubt der Dienst keinem Benutzernamen, so kann niemand mit selbst gebauten Headern an NPM vorbei.

```
GEHEIMNIS=$(openssl rand -hex 32)
echo "CAMPUS_PROXY_GEHEIMNIS=$GEHEIMNIS" | sudo tee /etc/campus/dienst.env > /dev/null
sudo chown root:root /etc/campus/dienst.env
sudo chmod 600 /etc/campus/dienst.env
echo "$GEHEIMNIS"
```

Die angezeigte Zeichenkette brauchst du in Schritt 11 im NPM. Nicht ins Repo, nicht in den Chat.

### 7. SELinux

CentOS lässt nginx sonst weder ins Repo schauen noch mit dem Dienst reden.

```
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/campus/repo(/.*)?"
sudo restorecon -R /srv/campus/repo
sudo setsebool -P httpd_can_network_connect 1
```

### 8. Dienst und Timer starten

```
sudo cp /srv/campus/repo/server/campus-dienst.service /srv/campus/repo/server/campus-pull.service /srv/campus/repo/server/campus-pull.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campus-dienst.service
sudo systemctl enable --now campus-pull.timer
systemctl status campus-dienst.service
```

Der Status muss `active (running)` zeigen, und im Log (`journalctl -u campus-dienst`) darf **keine** Warnung zu `CAMPUS_PROXY_GEHEIMNIS` stehen. Der Dienst lauscht nur auf `127.0.0.1:8090`.

### 9. nginx auf dem Campus-Server

```
sudo cp /srv/campus/repo/server/nginx-campus.conf /etc/nginx/conf.d/campus.conf
sudo sed -i 's/NPM-IP-ADRESSE/NPM-IP/g' /etc/nginx/conf.d/campus.conf
sudo nginx -t
sudo systemctl enable --now nginx
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="NPM-IP" port port="80" protocol="tcp" accept'
sudo firewall-cmd --reload
```

`nginx -t` muss `syntax is ok` und `test is successful` melden. Port 80 ist damit nur für NPM offen, nginx selbst lässt auch nur NPM rein (doppelt hält besser).

### 10. Authentik

In der Authentik-Admin-Oberfläche:

1. **Gruppen** unter Directory → Groups: Zugang hat die bestehende Gruppe `tofg-users`. Neu anlegen: `campus-admins` (Admins der Website). Beide Benutzer müssen in `tofg-users` sein, Jonah zusätzlich in `campus-admins`.
2. **Provider** unter Applications → Providers → Create: Typ **Proxy Provider**, Modus **Forward auth (single application)**, External host `https://DEINE-DOMAIN`.
3. **Application** unter Applications → Applications → Create: Name `Campus`, Slug `campus`, Provider aus Schritt 2.
4. In der Application unter **Policy / Group / User Bindings** die Gruppe `tofg-users` binden. Wer nicht in der Gruppe ist, kommt dann gar nicht erst durch.
5. Unter Applications → Outposts den Outpost (meist **authentik Embedded Outpost**) bearbeiten und die Application `Campus` hinzufügen.

### 11. Nginx Proxy Manager

Neuen **Proxy Host** anlegen:

- **Details:** Domain `DEINE-DOMAIN`, Scheme `http`, Forward Hostname/IP `CAMPUS-IP`, Port `80`. **Block Common Exploits** an.
- **SSL:** Zertifikat per Let's Encrypt anfordern, **Force SSL** und **HTTP/2** an.
- **Advanced:** folgendes einfügen, `AUTHENTIK-OUTPOST` und `PROXY-GEHEIMNIS` ersetzen:

```nginx
proxy_buffers 8 16k;
proxy_buffer_size 32k;
port_in_redirect off;

# Schematic-Import: bis 21 MB, Vorschau darf rechnen
client_max_body_size 25m;
proxy_read_timeout 300s;
proxy_send_timeout 300s;

location / {
    proxy_pass          $forward_scheme://$server:$port;
    proxy_set_header    Host $host;
    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header    X-Forwarded-Proto $scheme;
    proxy_http_version  1.1;

    # Geheimnis für den Campus-Dienst (aus /etc/campus/dienst.env)
    proxy_set_header    X-Campus-Proxy "PROXY-GEHEIMNIS";

    # Authentik
    auth_request        /outpost.goauthentik.io/auth/nginx;
    error_page          401 = @goauthentik_proxy_signin;
    auth_request_set    $auth_cookie $upstream_http_set_cookie;
    add_header          Set-Cookie $auth_cookie;

    auth_request_set    $authentik_username $upstream_http_x_authentik_username;
    auth_request_set    $authentik_groups $upstream_http_x_authentik_groups;
    auth_request_set    $authentik_email $upstream_http_x_authentik_email;
    auth_request_set    $authentik_name $upstream_http_x_authentik_name;
    auth_request_set    $authentik_uid $upstream_http_x_authentik_uid;

    proxy_set_header    X-authentik-username $authentik_username;
    proxy_set_header    X-authentik-groups $authentik_groups;
    proxy_set_header    X-authentik-email $authentik_email;
    proxy_set_header    X-authentik-name $authentik_name;
    proxy_set_header    X-authentik-uid $authentik_uid;
}

# Der Outpost selbst muss ohne Anmeldung erreichbar sein
location /outpost.goauthentik.io {
    proxy_pass              AUTHENTIK-OUTPOST/outpost.goauthentik.io;
    proxy_set_header        Host $host;
    proxy_set_header        X-Original-URL $scheme://$http_host$request_uri;
    add_header              Set-Cookie $auth_cookie;
    auth_request_set        $auth_cookie $upstream_http_set_cookie;
    proxy_pass_request_body off;
    proxy_set_header        Content-Length "";
}

# Nicht angemeldet: weiter zum Authentik-Login
location @goauthentik_proxy_signin {
    internal;
    add_header Set-Cookie $auth_cookie;
    return 302 /outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
}
```

Wichtig: Im Tab **Custom Locations** nichts anlegen. Jede Location ohne diesen Block würde am Login vorbei zum Campus-Server durchreichen (das Proxy-Geheimnis fehlt dann zwar, und der Dienst lässt niemanden rein, aber sauber ist das nicht).

### 12. Erste Konten

Ein Konto verbindet einen Authentik-Benutzer mit einem Profil unter `team/`. Groß- und Kleinschreibung beim Authentik-Namen ist egal.

```
cd /srv/campus/repo
sudo -u campus python3 server/konto.py anlegen jonah --authentik JOberascher --anzeigename Jonah --minecraft Informiert
sudo -u campus python3 server/konto.py anlegen felix --authentik FFoerster --anzeigename Felix --minecraft MultiBilliardaer
sudo -u campus python3 server/konto.py liste
```

Weitere Konten legt ein Admin danach auf der Website unter **Admin** an. Die Person braucht vorher einen Benutzer in Authentik in der Gruppe `tofg-users`.

### 13. Prüfen

- `https://DEINE-DOMAIN` öffnen: Es kommt der Authentik-Login, danach die Übersicht. Oben rechts stehen Name, **Import**, **Versionen** und bei Admins **Admin**.
- Von einem anderen Rechner als NPM: `curl -sI http://CAMPUS-IP/website/` darf keine Antwort liefern oder muss `403` zeigen.
- `curl -sI https://DEINE-DOMAIN/website/` zeigt ohne Anmeldung `302` mit `Location: /outpost.goauthentik.io/start?...`.
- `curl -sI https://DEINE-DOMAIN/.git/config` zeigt ohne Anmeldung `302`, angemeldet im Browser `404`.
- Unter **Team** das eigene Profil ändern und speichern. Auf GitHub erscheint ein Commit mit dir als Autor.
- **Abmelden** oben rechts führt zur Abmeldung bei Authentik.

### Betrieb

| Aufgabe | Befehl |
| --- | --- |
| Log des Dienstes | `journalctl -u campus-dienst -f` |
| Log vom Abgleich mit GitHub | `journalctl -u campus-pull` |
| Passwort zurücksetzen | in Authentik |
| Admin-Recht geben oder nehmen | in Authentik, Gruppe `campus-admins` |
| Authentik-Namen eines Kontos ändern | `sudo -u campus python3 server/konto.py authentik felix NEUER-NAME` (oder auf der Website unter Admin) |
| Konto sperren | `sudo -u campus python3 server/konto.py sperren felix`, aber nicht aus `tofg-users` nehmen, die Gruppe gilt auch für andere Dienste |
| Konten sichern | `/var/lib/campus/konten.json` wegkopieren |
| Liegen gebliebenen Import entfernen | auf der Website unter Import **Verwerfen** (geht auch für Admins), oder er verfällt nach 30 Minuten von selbst |

- **Neuer Code kommt von selbst:** Der Timer holt ihn. Ändert sich etwas unter `server/*.py`, startet sich der Dienst innerhalb von 20 Sekunden selbst neu.
- **Von Hand nachziehen** muss man nur geänderte Vorlagen: nach einer Änderung an `server/nginx-campus.conf` die Datei wieder nach `/etc/nginx/conf.d/` kopieren (NPM-IP wieder eintragen) und `sudo systemctl reload nginx`, nach einer Änderung an den Units wieder kopieren und `sudo systemctl daemon-reload`.
- **Wenn der Abgleich hängt:** `journalctl -u campus-pull` zeigt den Grund. Meist wurde auf GitHub die Geschichte umgeschrieben (Force-Push). Dann auf dem Server `sudo -u campus git -C /srv/campus/repo fetch` und `sudo -u campus git -C /srv/campus/repo reset --hard origin/main`.
