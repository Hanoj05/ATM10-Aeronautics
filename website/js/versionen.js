/* Versionen: git log über den Campus-Dienst, Karten-Stände lassen sich zurückholen (nur Admin). */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("versionen");

  var wer = null, leute = {}, alle = [], ab = 0, github = null, filter = "", SEITE = 40;

  function wann(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }) + " " + d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
  }
  function toast(text, fehler) {
    var t = $("toast"); t.textContent = text; t.className = "kb-toast" + (fehler ? " fehler" : ""); t.hidden = false;
    setTimeout(function () { t.hidden = true; }, fehler ? 8000 : 4000);
  }

  function eintrag(v) {
    var id = /^([a-z][a-z0-9-]*)@campus\.invalid$/.exec(v.mail);
    var p = id && leute[id[1]];
    var kopf = p ? C.avatar(p, 30) : C.avatar({ anzeigename: v.autor, farbe: "#62645f" }, 30);
    var knopf = v.karte && wer && wer.admin && alle[0] !== v
      ? "<button type='button' class='knopf leise' data-zurueck='" + esc(v.commit) + "'>Diesen Kartenstand wiederherstellen</button>" : "";
    return "<li class='box ver-eintrag" + (v.karte ? " karte" : "") + "'>" + kopf +
      "<div class='ver-text'><div class='ver-kopf'><b>" + esc(p ? p.anzeigename : v.autor) + "</b><span>" + esc(wann(v.datum)) + "</span>" +
      (v.ueber === "Campus-Website" ? "<span class='chip'>über die Website</span>" : "") + "</div>" +
      "<p>" + esc(v.betreff) + "</p>" +
      "<div class='ver-unten'>" + v.bereiche.map(function (b) { return "<span class='chip" + (b === "Karte" ? " ok" : "") + "'>" + esc(b) + "</span>"; }).join("") +
      (github ? "<a href='" + esc(github) + "/commit/" + esc(v.commit) + "' target='_blank' rel='noopener'><code>" + esc(v.commit.slice(0, 7)) + "</code></a>" : "<code>" + esc(v.commit.slice(0, 7)) + "</code>") +
      knopf + "</div></div></li>";
  }

  function zeige() {
    var sichtbar = alle.filter(function (v) { return !filter || v.bereiche.indexOf(filter) >= 0; });
    $("liste").innerHTML = sichtbar.map(eintrag).join("") || "<li class='note'>Nichts gefunden.</li>";
  }

  function laden() {
    return C.api("versionen?ab=" + ab).then(function (j) {
      github = j.github;
      alle = alle.concat(j.versionen);
      $("mehr").hidden = j.versionen.length < SEITE;
      zeige();
    }).catch(function (e) { $("liste").innerHTML = "<li class='meldung fehler'>" + esc(e.message) + "</li>"; });
  }

  $("mehr").addEventListener("click", function () { ab += SEITE; laden(); });
  $("filter").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-f]");
    if (!b) return;
    filter = b.getAttribute("data-f");
    [].forEach.call(this.querySelectorAll("button"), function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    zeige();
  });
  $("liste").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-zurueck]");
    if (!b) return;
    if (!b.classList.contains("sicher")) {
      b.classList.add("sicher"); b.textContent = "Wirklich? Klick noch einmal: Karte auf diesen Stand setzen"; return;
    }
    b.disabled = true; b.textContent = "Setze zurück …";
    C.api("versionen/" + b.getAttribute("data-zurueck") + "/wiederherstellen", {}).then(function (j) {
      toast(j.commit ? "Karte zurückgesetzt, neuer Commit " + j.commit.slice(0, 7) + "." : "Die Karte war schon auf diesem Stand.");
      alle = []; ab = 0; laden();
    }).catch(function (e) { toast(e.message, true); b.disabled = false; b.classList.remove("sicher"); b.textContent = "Diesen Kartenstand wiederherstellen"; });
  });

  Promise.all([C.ich(), C.ladeJSON("team/liste.json").catch(function () { return []; })]).then(function (r) {
    wer = r[0];
    if (!wer) { $("liste").innerHTML = "<li class='note'>Die Versionen gibt es nur auf dem Server mit Login.</li>"; return; }
    return Promise.all(r[1].map(function (id) { return C.ladeJSON("team/" + id + ".json").catch(function () { return null; }); })).then(function (ps) {
      ps.filter(Boolean).forEach(function (p) { leute[p.id] = p; });
      return laden();
    });
  });
})();
