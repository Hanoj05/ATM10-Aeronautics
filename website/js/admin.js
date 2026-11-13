/* Admin: Campus-Konten verwalten. Ein Konto verbindet einen Authentik-Benutzer mit einem Profil.
 * Passwörter und Admin-Recht kommen aus Authentik. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("admin");

  var ichId = null;

  function zeit(t) {
    if (!t) return "nie";
    var d = new Date(t);
    return d.toLocaleDateString("de-DE") + " " + d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  }

  function zeile(k) {
    var status = k.gesperrt ? "<span class='chip warn'>gesperrt</span>" : "<span class='chip ok'>aktiv</span>";
    var selbst = k.id === ichId, a = [];
    if (!selbst) {
      a.push("<button type='button' class='knopf leise' data-a='authentik'>Authentik-Name ändern</button>");
      a.push(k.gesperrt ? "<button type='button' class='knopf leise' data-a='entsperren'>Entsperren</button>" : "<button type='button' class='knopf leise' data-a='sperren'>Sperren</button>");
    }
    return "<tr data-id='" + esc(k.id) + "'><td><b>" + esc(k.anzeigename) + "</b><br><code>" + esc(k.id) + "</code></td>" +
      "<td><code>" + esc(k.authentik || "–") + "</code></td><td>" + status + "</td><td>" + esc(zeit(k.letzter_login)) + "</td>" +
      "<td><div class='knoepfe'>" + a.join("") + "</div><div class='zeilenform'></div></td></tr>";
  }

  function laden() {
    return C.api("konten").then(function (j) {
      if (j.adminGruppe) $("adminGruppe").textContent = j.adminGruppe;
      $("konten").innerHTML = j.konten.map(zeile).join("") || "<tr><td colspan='5' class='note'>Keine Konten.</td></tr>";
    }).catch(function (e) {
      $("konten").innerHTML = "<tr><td colspan='5' class='meldung fehler'>" + esc(e.message) + "</td></tr>";
    });
  }

  function aktion(id, daten, meldung) {
    meldung.className = "meldung"; meldung.textContent = "…";
    return C.api("konten/" + encodeURIComponent(id), daten).then(laden).catch(function (e) {
      meldung.className = "meldung fehler"; meldung.textContent = e.message;
    });
  }

  $("konten").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-a]");
    if (!b) return;
    var tr = b.closest("tr"), id = tr.getAttribute("data-id"), was = b.getAttribute("data-a"), platz = tr.querySelector(".zeilenform");
    if (was === "authentik") {
      platz.innerHTML = "<form class='inline'><input name='authentik' type='text' maxlength='150' required placeholder='Benutzername in Authentik' autocapitalize='none' spellcheck='false'>" +
        "<button type='submit' class='knopf'>Setzen</button><span class='meldung' role='status'></span></form>";
      var f = platz.querySelector("form");
      f.elements.authentik.focus();
      f.addEventListener("submit", function (e2) {
        e2.preventDefault();
        aktion(id, { aktion: "authentik", authentik: f.elements.authentik.value.trim() }, f.querySelector(".meldung"));
      });
      return;
    }
    platz.innerHTML = "<span class='meldung' role='status'></span>";
    aktion(id, { aktion: was }, platz.firstChild);
  });

  $("neu").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var f = ev.target, m = f.querySelector(".meldung");
    m.className = "meldung"; m.textContent = "Lege an …";
    C.api("konten", {
      id: f.elements.id.value.trim().toLowerCase(), anzeigename: f.elements.anzeigename.value, minecraft: f.elements.minecraft.value,
      authentik: f.elements.authentik.value.trim()
    }).then(function (j) {
      m.className = j.warnung ? "meldung fehler" : "meldung";
      m.textContent = j.warnung || "Angelegt. Profil liegt jetzt unter team/.";
      f.reset(); laden();
    }).catch(function (e) { m.className = "meldung fehler"; m.textContent = e.message; });
  });

  C.ich().then(function (i) {
    if (!i) { $("hinweis").hidden = false; $("hinweis").textContent = "Die Admin-Seite geht nur auf dem Server mit Anmeldung."; return; }
    if (!i.admin) { $("hinweis").hidden = false; $("hinweis").textContent = "Nur für Admins."; return; }
    ichId = i.id; laden();
  });
})();
