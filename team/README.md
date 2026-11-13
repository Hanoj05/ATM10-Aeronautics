# Team

Öffentliche Profile für die Seite `website/team.html`. Login-Daten (Passwörter, Sitzungen) liegen nie hier, sondern nur auf dem Server unter `/var/lib/campus/`.

| Datei | Inhalt |
| --- | --- |
| `liste.json` | Alle Profil-IDs, in dieser Reihenfolge zeigt die Seite sie an |
| `<id>.json` | Ein Profil: `id` (gleich dem Kontonamen), `anzeigename`, `minecraft`, `farbe` (`#rrggbb`), `info` |

Jeder ändert sein Profil auf der Website unter **Team → Bearbeiten**, das wird ein eigener Commit mit der Person als Autor. Neue Profile entstehen, wenn der Admin ein Konto anlegt.
