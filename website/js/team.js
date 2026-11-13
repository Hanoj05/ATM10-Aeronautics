/* Team: Profile aus team/<id>.json. Eigenes Profil (Admins: jedes) lässt sich bearbeiten. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("team");

  var profile = [], wer = null, karten = [];

  /* Offene Karten aus dem Kanban, die einer Person zugewiesen sind */
  function aufgaben(id) {
    var meine = karten.filter(function (k) { return k.status !== "erledigt" && (k.zustaendig || []).indexOf(id) >= 0; })
      .sort(function (a, b) { return (a.status === "in Arbeit" ? 0 : 1) - (b.status === "in Arbeit" ? 0 : 1) || a.rang - b.rang; });
    var link = "kanban.html?person=" + encodeURIComponent(id);
    if (!meine.length) return "<p class='note'>Keine offenen Aufgaben. <a href='" + link + "'>Kanban</a></p>";
    return "<ul class='team-aufgaben'>" + meine.slice(0, 6).map(function (k) {
      return "<li><span class='s'>" + esc(k.status) + "</span><span>" + esc(k.titel) + "</span></li>";
    }).join("") + "</ul><a class='note' href='" + link + "'>" + (meine.length > 6 ? "alle " + meine.length + " Aufgaben" : "im Kanban ansehen") + " →</a>";
  }

  function karte(p) {
    var darf = wer && (wer.id === p.id || wer.admin);
    return "<article class='box team-karte' id='" + esc(p.id) + "'>" +
      "<div class='team-kopf'>" + C.avatar(p, 56) + "<div><h2>" + esc(p.anzeigename || p.id) + "</h2>" +
      (p.minecraft ? "<span class='mc' title='Minecraft-Name'>" + esc(p.minecraft) + "</span>" : "<span class='note'>kein Minecraft-Name</span>") + "</div></div>" +
      (p.info ? "<p class='team-info'>" + esc(p.info) + "</p>" : "") +
      "<div class='team-aufgaben-box'><h3 class='team-h3'>Aufgaben</h3>" + aufgaben(p.id) + "</div>" +
      (darf ? "<button type='button' class='knopf leise' data-bearbeiten='" + esc(p.id) + "'>Bearbeiten</button>" : "") +
      "<div class='bearbeiten'></div>" +
      "</article>";
  }

  function zeige() {
    $("karten").innerHTML = profile.length ? profile.map(karte).join("") : "<p class='note'>Noch keine Profile.</p>";
    if (location.hash) {
      var ziel = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (ziel) { ziel.classList.add("hervor"); ziel.scrollIntoView({ block: "center" }); }
    }
  }

  function formular(id, ziel) {
    C.api("profil/" + encodeURIComponent(id)).then(function (r) {
      var p = r.profil;
      ziel.innerHTML = "<form class='formular'>" +
        "<label>Anzeigename <input name='anzeigename' maxlength='40' required value='" + esc(p.anzeigename || "") + "'></label>" +
        "<label>Minecraft-Name <input name='minecraft' maxlength='16' pattern='[A-Za-z0-9_]{3,16}' value='" + esc(p.minecraft || "") + "'></label>" +
        "<label>Farbe <input name='farbe' type='color' value='" + esc(p.farbe || "#d9840b") + "'></label>" +
        "<label>Kurze Info <textarea name='info' maxlength='500' rows='3'>" + esc(p.info || "") + "</textarea></label>" +
        "<div class='knoepfe'><button type='submit' class='knopf'>Speichern</button><button type='button' class='knopf leise' data-abbrechen>Abbrechen</button><span class='meldung' role='status'></span></div>" +
        "</form>";
      var f = ziel.querySelector("form");
      f.querySelector("[data-abbrechen]").addEventListener("click", function () { ziel.innerHTML = ""; });
      f.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var m = f.querySelector(".meldung"), knopf = f.querySelector("button[type=submit]");
        knopf.disabled = true; m.className = "meldung"; m.textContent = "Speichere …";
        C.api("profil/" + encodeURIComponent(id), {
          version: r.version, anzeigename: f.elements.anzeigename.value, minecraft: f.elements.minecraft.value,
          farbe: f.elements.farbe.value, info: f.elements.info.value
        }).then(function (j) {
          profile = profile.map(function (x) { return x.id === id ? j.profil : x; });
          zeige();
        }).catch(function (e) {
          m.className = "meldung fehler"; m.textContent = e.message; knopf.disabled = false;
        });
      });
      f.elements.anzeigename.focus();
    }).catch(function (e) { ziel.innerHTML = "<p class='meldung fehler'>" + esc(e.message) + "</p>"; });
  }

  $("karten").addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-bearbeiten]");
    if (b) formular(b.getAttribute("data-bearbeiten"), b.parentNode.querySelector(".bearbeiten"));
  });

  /* Karten: mit Login über den Dienst, sonst direkt aus kanban/ */
  function ladeKarten() {
    return C.ich().then(function (i) {
      if (i) return C.api("kanban").then(function (j) { return j.karten; });
      return C.ladeJSON("kanban/liste.json").then(function (ids) {
        return Promise.all(ids.map(function (id) { return C.ladeJSON("kanban/karten/" + id + ".json").catch(function () { return null; }); }));
      });
    }).then(function (l) { return l.filter(Boolean); }).catch(function () { return []; });
  }

  Promise.all([
    C.ladeJSON("team/liste.json").catch(function () { return []; }),
    C.ich(),
    ladeKarten()
  ]).then(function (r) {
    wer = r[1];
    karten = r[2];
    return Promise.all(r[0].map(function (id) { return C.ladeJSON("team/" + encodeURIComponent(id) + ".json").catch(function () { return null; }); }));
  }).then(function (liste) {
    profile = liste.filter(Boolean);
    zeige();
  }).catch(function (e) { $("karten").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });
})();
