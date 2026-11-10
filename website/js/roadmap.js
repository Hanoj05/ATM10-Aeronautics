/* Roadmap: liest campus/roadmap.json und zeigt Phasen mit Stand. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("roadmap");

  var STATUS = { "erledigt": "erledigt", "in Arbeit": "arbeit", "offen": "offen" };
  var filter = "alle", daten = null;

  function zaehle(punkte) {
    var z = { erledigt: 0, "in Arbeit": 0, offen: 0, alle: punkte.length };
    punkte.forEach(function (p) { z[p.status] = (z[p.status] || 0) + 1; });
    return z;
  }
  function prozent(z) { return z.alle ? Math.round(z.erledigt / z.alle * 100) : 0; }

  Promise.all([
    C.ladeJSON("campus/roadmap.json"),
    C.ladeJSON("campus/campus.json").catch(function () { return { gebaeude: [] }; })
  ]).then(function (r) {
    var roadmap = r[0], namen = {};
    r[1].gebaeude.forEach(function (g) { namen[g.id] = g.name; });
    /* Fortschritt aus den Gebäudedaten holen, wo ein Punkt das will */
    var holen = [];
    roadmap.phasen.forEach(function (ph) { ph.punkte.forEach(function (p) {
      if (p.fortschritt === "einrichtung" && p.gebaeude) {
        holen.push(C.ladeJSON("gebaeude/" + p.gebaeude + "/einrichtung.json").then(function (e) {
          var t = e.teile || [];
          p.messung = { fertig: t.filter(function (x) { return x.status === "fertig"; }).length, von: t.length };
        }).catch(function () {}));
      }
    }); });
    return Promise.all(holen).then(function () { daten = { roadmap: roadmap, namen: namen }; zeige(); });
  }).catch(function (e) { $("stand").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });

  $("filter").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-f]");
    if (!b) return;
    filter = b.getAttribute("data-f");
    $("filter").querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    zeige();
  });

  function zeige() {
    var phasen = daten.roadmap.phasen, alle = [];
    phasen.forEach(function (ph) { alle = alle.concat(ph.punkte); });
    var z = zaehle(alle);
    var aktuell = phasen.filter(function (ph) { return ph.punkte.some(function (p) { return p.status !== "erledigt"; }); })[0];

    var s = "<div class='rm-gross'><b>" + prozent(z) + " %</b><span>" + z.erledigt + " von " + z.alle + " Punkten erledigt</span></div>";
    s += "<div class='rm-balken' role='img' aria-label='" + z.erledigt + " erledigt, " + z["in Arbeit"] + " in Arbeit, " + z.offen + " offen'>";
    s += "<i class='erledigt' style='width:" + (z.erledigt / z.alle * 100) + "%'></i><i class='arbeit' style='width:" + (z["in Arbeit"] / z.alle * 100) + "%'></i></div>";
    s += "<div class='rm-zahlen'><span><i class='punkt erledigt'></i>Erledigt <b>" + z.erledigt + "</b></span><span><i class='punkt arbeit'></i>In Arbeit <b>" + z["in Arbeit"] + "</b></span><span><i class='punkt offen'></i>Offen <b>" + z.offen + "</b></span>";
    if (aktuell) s += "<span class='rm-jetzt'>Jetzt dran: <b>" + esc(aktuell.titel) + "</b></span>";
    s += "</div>";
    $("stand").innerHTML = s;

    var h = "";
    phasen.forEach(function (ph, i) {
      var zp = zaehle(ph.punkte);
      var art = zp.erledigt === zp.alle ? "fertig" : ph === aktuell ? "aktuell" : "spaeter";
      var sichtbar = ph.punkte.filter(function (p) { return filter === "alle" || p.status === filter; });
      h += "<li class='rm-phase " + art + "'><div class='rm-marke' aria-hidden='true'>" + (art === "fertig" ? "✓" : i + 1) + "</div><div class='rm-inhalt'>";
      h += "<div class='rm-kopf'><div><h2>" + esc(ph.titel) + (art === "aktuell" ? " <span class='chip ok'>jetzt</span>" : "") + "</h2><p>" + esc(ph.ziel) + "</p></div>";
      h += "<div class='rm-mini'><small>" + zp.erledigt + " / " + zp.alle + "</small><div class='balken'><i style='width:" + prozent(zp) + "%'></i></div></div></div>";
      if (sichtbar.length) {
        h += "<ul class='rm-punkte'>";
        sichtbar.forEach(function (p) {
          var kl = STATUS[p.status] || "offen";
          h += "<li class='box rm-punkt " + kl + "'><span class='rm-status " + kl + "'>" + esc(p.status) + "</span><div class='rm-text'><strong>" + esc(p.titel) + "</strong>";
          if (p.text) h += "<p>" + esc(p.text) + "</p>";
          if (p.messung && p.messung.von) h += "<div class='rm-messung'><small>" + p.messung.fertig + " von " + p.messung.von + " fertig</small><div class='balken'><i style='width:" + Math.round(p.messung.fertig / p.messung.von * 100) + "%'></i></div></div>";
          h += "</div><div class='rm-meta'><span class='rm-bereich'>" + esc(p.bereich || "") + "</span>";
          if (p.gebaeude && daten.namen[p.gebaeude]) h += "<a href='gebaeude.html?id=" + encodeURIComponent(p.gebaeude) + "#" + esc(p.tab || "ansicht") + "'>" + esc(daten.namen[p.gebaeude]) + " →</a>";
          h += "</div></li>";
        });
        h += "</ul>";
      } else {
        h += "<p class='note rm-leer'>Nichts mit diesem Status.</p>";
      }
      h += "</div></li>";
    });
    $("phasen").innerHTML = h;
  }
})();
