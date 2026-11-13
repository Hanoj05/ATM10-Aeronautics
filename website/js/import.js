/* Karte aktualisieren: Schematic hochladen, Vorschau mit 3D-Vergleich, übernehmen.
 * Die ganze Arbeit macht der Campus-Dienst (server/karte.py), diese Seite zeigt nur an. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("import");

  var stand = null, wer = null, campus = [];
  var drei = null, modelle = {}, modus = "unterschied", fokus = "";

  function zahl(n) { return Number(n).toLocaleString("de-DE"); }
  function meldung(el, text, fehler) { el.className = "meldung" + (fehler ? " fehler" : ""); el.textContent = text || ""; }
  function hinweis(text) { $("hinweis").hidden = !text; $("hinweis").textContent = text || ""; }

  /* ---------- Zustand anzeigen ---------- */
  function zeige() {
    var imp = stand.import;
    var fremd = imp && !imp.meins;
    $("hochBox").hidden = !!(imp && imp.ergebnis && imp.meins) || fremd;
    $("vorschau").hidden = !(imp && imp.meins && imp.ergebnis);
    if (fremd) hinweis(imp.name + " importiert gerade eine Schematic. Es geht immer nur ein Import gleichzeitig. Bitte warten, bis " + imp.name + " übernommen oder verworfen hat (spätestens nach 30 Minuten ist wieder frei).");
    else hinweis("");
    var ecke = (imp && imp.ecke) || stand.ecke || [0, 64, 0];
    var f = $("hoch");
    f.elements.x.value = ecke[0]; f.elements.y.value = ecke[1]; f.elements.z.value = ecke[2];
    if (imp && imp.meins && imp.ergebnis) vorschau(imp);
  }

  function vorschau(imp) {
    var e = imp.ergebnis;
    $("kopf").innerHTML = "<div class='im-kopf-zeile'><b>" + esc(imp.dateiname) + "</b><span>" + zahl(imp.anzahl) + " Blöcke, " +
      imp.groesse.join(" × ") + " groß, Ecke " + imp.ecke.join(", ") + "</span></div>" +
      "<p class='note'>Hochgeladen von " + esc(imp.name) + ". Bis zum Übernehmen ändert sich nichts an der Website.</p>";
    var warnungen = 0;
    $("tabelle").innerHTML = e.gebaeude.map(function (g) {
      if (g.warnung) warnungen++;
      var quelle = "<select data-feld='quelle' data-id='" + esc(g.id) + "'>" +
        "<option value='schematic'" + (g.quelle === "schematic" ? " selected" : "") + ">Schematic</option>" +
        "<option value='entwurf'" + (g.quelle === "entwurf" ? " selected" : "") + (g.kannEntwurf ? "" : " disabled") + ">Entwurfs-Skript</option></select>";
      var bereich = g.quelle === "schematic" && g.von && g.bis
        ? "<span class='im-bereich' data-id='" + esc(g.id) + "'>" + [0, 1, 2].map(function (i) { return "<input type='number' data-feld='von' data-i='" + i + "' value='" + g.von[i] + "' aria-label='von " + "xyz"[i] + "'>"; }).join("") +
          "<span>bis</span>" + [0, 1, 2].map(function (i) { return "<input type='number' data-feld='bis' data-i='" + i + "' value='" + g.bis[i] + "' aria-label='bis " + "xyz"[i] + "'>"; }).join("") + "</span>"
        : "<span class='note'>" + (g.quelle === "entwurf" ? "kommt aus dem Skript" : "–") + "</span>";
      return "<tr class='" + (g.warnung ? "warn" : "") + "' data-id='" + esc(g.id) + "'><td><b>" + esc(g.name) + "</b></td><td>" + quelle + "</td><td>" + bereich + "</td>" +
        "<td class='zahl'>" + zahl(g.vorher) + " → " + zahl(g.nachher) + "</td>" +
        "<td class='zahl'><span class='d'>+" + zahl(g.dazu) + "</span> <span class='w'>−" + zahl(g.weg) + "</span></td>" +
        "<td>" + (g.warnung ? "<span class='chip warn'>" + esc(g.warnung) + "</span>" : "") + "</td></tr>";
    }).join("");
    var h = "";
    if (e.ohneTextur.length) {
      h += "<section class='box im-liste'><h3>Neue Blöcke ohne Textur</h3><p class='note'>Die Website zeigt sie in einer Ersatzfarbe. Texturen holt <code>tools/hole-texturen.py</code> am eigenen PC.</p><ul>" +
        e.ohneTextur.map(function (b) {
          return "<li><code>" + esc(b.id) + "</code> <span class='note'>" + Object.keys(b.wo).map(function (n) { return esc(n) + " (" + b.wo[n] + ")"; }).join(", ") + "</span></li>";
        }).join("") + "</ul></section>";
    }
    if (e.aussen.length) {
      h += "<section class='box im-liste'><h3>Gebautes außerhalb aller Gebäude</h3><p class='note'>Steht in der Schematic, gehört aber zu keinem Gebäude. Vielleicht ein neues Gebäude? Das wird nicht von allein angelegt, sondern von Hand in <code>campus/campus.json</code> und <code>gebaeude/</code>.</p><ul>" +
        e.aussen.map(function (a) {
          return "<li><b>" + zahl(a.bloecke) + " Blöcke</b> bei x " + a.von[0] + " … " + a.bis[0] + ", y " + a.von[1] + " … " + a.bis[1] + ", z " + a.von[2] + " … " + a.bis[2] +
            " <span class='note'>(" + a.haeufig.map(esc).join(", ") + ")</span></li>";
        }).join("") + "</ul></section>";
    }
    $("hinweise").innerHTML = h;
    $("warnOk").hidden = !warnungen;
    $("warnHaken").checked = false;
    $("fokus").innerHTML = "<option value=''>ganzer Campus</option>" + e.gebaeude.map(function (g) { return "<option value='" + esc(g.id) + "'>" + esc(g.name) + "</option>"; }).join("");
    $("fokus").value = fokus;
    ladeModelle(e.gebaeude);
  }

  function einstellungen() {
    var aus = {};
    [].forEach.call(document.querySelectorAll("#tabelle tr"), function (tr) {
      var id = tr.getAttribute("data-id"), e = { quelle: tr.querySelector("[data-feld=quelle]").value };
      var von = tr.querySelectorAll("[data-feld=von]"), bis = tr.querySelectorAll("[data-feld=bis]");
      if (von.length === 3) {
        e.von = [].map.call(von, function (i) { return parseInt(i.value, 10); });
        e.bis = [].map.call(bis, function (i) { return parseInt(i.value, 10); });
      }
      aus[id] = e;
    });
    return aus;
  }

  /* ---------- 3D ---------- */
  function ladeModelle(liste) {
    $("loading").hidden = false; $("loading").textContent = "Lade Modelle …";
    modelle = {};
    return Promise.all(liste.map(function (g) {
      var c = campus.filter(function (x) { return x.id === g.id; })[0];
      if (!c || !c.position) return null;
      return Promise.all([
        C.ladeJSON(c.ordner + "/modell.json").catch(function () { return null; }),
        C.api("import/modell/" + encodeURIComponent(g.id)).catch(function () { return null; })
      ]).then(function (r) { modelle[g.id] = { c: c, vorher: r[0], nachher: r[1] }; });
    })).then(function () { zeichne(); $("loading").hidden = true; });
  }

  function schluessel(m) {
    var pal = m.palette || [], s = {};
    m.bloecke.forEach(function (b) { s[b[0] + "," + b[1] + "," + b[2] + "," + ((pal[b[3]] || {}).id || b[3])] = b; });
    return s;
  }
  var DIFF_PALETTE = [
    { id: "diff:gleich", name: "unverändert", farbe: "#bcb9b0", transparent: false, klein: false },
    { id: "diff:dazu", name: "dazu", farbe: "#2e9d4f", transparent: false, klein: false },
    { id: "diff:weg", name: "weg", farbe: "#d0362c", transparent: false, klein: false }
  ];
  function unterschied(alt, neu) {
    var a = alt ? schluessel(alt) : {}, n = neu ? schluessel(neu) : {}, bl = [];
    Object.keys(n).forEach(function (k) { var b = n[k]; bl.push([b[0], b[1], b[2], a[k] ? 0 : 1]); });
    Object.keys(a).forEach(function (k) { if (!n[k]) { var b = a[k]; bl.push([b[0], b[1], b[2], 2]); } });
    return { palette: DIFF_PALETTE, bloecke: bl };
  }

  function zeichne() {
    if (!drei) drei = { sz: C.baueSzene($("viewport")), teile: [] };
    var sz = drei.sz;
    drei.teile.forEach(function (t) { sz.scene.remove(t); });
    drei.teile = [];
    var basis = null, gesamt = { min: [Infinity, 0, Infinity], max: [-Infinity, 10, -Infinity] }, ziel = null;
    Object.keys(modelle).forEach(function (id) { if (!basis) basis = modelle[id].c.position; });
    Object.keys(modelle).forEach(function (id) {
      var e = modelle[id];
      var m = modus === "vorher" ? e.vorher : modus === "nachher" ? e.nachher : unterschied(e.vorher, e.nachher);
      if (!m || !m.bloecke.length) return;
      var halter = C.drehGruppe(e.c.drehung);
      halter.position.x += e.c.position[0] - basis[0];
      halter.position.y += e.c.position[1] - basis[1];
      halter.position.z += e.c.position[2] - basis[2];
      halter.add(C.baueModell(m).gruppe);
      sz.scene.add(halter); drei.teile.push(halter);
      var b = C.weltBox(halter, m), box = [[b.min.x, b.min.y, b.min.z], [b.max.x, b.max.y, b.max.z]];
      if (id === fokus) ziel = box;
      for (var a = 0; a < 3; a++) { gesamt.min[a] = Math.min(gesamt.min[a], box[0][a]); gesamt.max[a] = Math.max(gesamt.max[a], box[1][a]); }
    });
    if (!drei.gitter && isFinite(gesamt.min[0])) {
      var spanne = Math.max(200, (gesamt.max[0] - gesamt.min[0]) * 3, (gesamt.max[2] - gesamt.min[2]) * 3);
      drei.gitter = new THREE.GridHelper(spanne, Math.round(spanne / 8), 0x9a978d, 0xb9b6ad);
      drei.gitter.position.set((gesamt.min[0] + gesamt.max[0]) / 2, -0.01, (gesamt.min[2] + gesamt.max[2]) / 2);
      drei.gitter.material.transparent = true; drei.gitter.material.opacity = 0.45;
      sz.scene.add(drei.gitter);
    }
    if (!drei.blick || drei.blick !== fokus) {
      drei.blick = fokus;
      if (ziel) C.blickeAuf(sz, ziel[0], ziel[1]);
      else if (isFinite(gesamt.min[0])) {
        C.blickeAuf(sz, gesamt.min, [gesamt.max[0], gesamt.max[1] * 0.4, gesamt.max[2]]);
        var t = sz.steuerung.target; sz.kamera.position.sub(t).multiplyScalar(1.3).add(t); sz.steuerung.update();
      }
    }
    $("legende").hidden = modus !== "unterschied";
    sz.neu();
  }

  $("modus").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-m]");
    if (!b) return;
    modus = b.getAttribute("data-m");
    [].forEach.call(this.querySelectorAll("button"), function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    zeichne();
  });
  $("fokus").addEventListener("change", function () { fokus = this.value; drei.blick = null; zeichne(); });

  /* ---------- Aktionen ---------- */
  $("hoch").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var f = ev.target, datei = f.elements.datei.files[0], m = f.querySelector(".meldung"), knopf = f.querySelector("button");
    if (!datei) return;
    if (datei.size > stand.maxUploadMB * 1024 * 1024) { meldung(m, "Die Datei ist größer als " + stand.maxUploadMB + " MB.", true); return; }
    var ecke = [f.elements.x.value, f.elements.y.value, f.elements.z.value].map(function (v) { return parseInt(v, 10); }).join(",");
    knopf.disabled = true; meldung(m, "Lade hoch und rechne die Vorschau, das dauert etwas …");
    fetch("../api/import/hochladen?ecke=" + encodeURIComponent(ecke) + "&name=" + encodeURIComponent(datei.name), {
      method: "POST", body: datei, credentials: "same-origin", headers: { "Content-Type": "application/octet-stream" }
    }).then(function (r) {
      return r.json().catch(function () { return { fehler: "Der Dienst antwortet nicht (" + r.status + ")." }; }).then(function (j) { if (!r.ok) throw new Error(j.fehler); return j; });
    }).then(function (j) {
      knopf.disabled = false; meldung(m, ""); stand.import = j.import; zeige();
      $("vorschau").scrollIntoView({ behavior: "smooth" });
    }).catch(function (e) { knopf.disabled = false; meldung(m, e.message, true); });
  });

  $("tabelle").addEventListener("change", function () { meldung($("rechnenMeldung"), "Einstellungen geändert: bitte neu berechnen, bevor du übernimmst."); $("uebernehmen").disabled = true; });
  $("neuRechnen").addEventListener("click", function () {
    var b = this; b.disabled = true; meldung($("rechnenMeldung"), "Rechne …");
    C.api("import/vorschau", { ecke: stand.import.ecke, einstellungen: einstellungen() }).then(function (j) {
      b.disabled = false; meldung($("rechnenMeldung"), "Neu berechnet."); $("uebernehmen").disabled = false;
      stand.import = j.import; zeige();
    }).catch(function (e) { b.disabled = false; meldung($("rechnenMeldung"), e.message, true); });
  });

  $("uebernehmen").addEventListener("click", function () {
    var m = $("endeMeldung");
    if (!$("warnOk").hidden && !$("warnHaken").checked) { meldung(m, "Bitte erst bestätigen, dass du die Warnungen gesehen hast.", true); return; }
    var b = this; b.disabled = true; meldung(m, "Schreibe und schicke nach GitHub …");
    C.api("import/uebernehmen", {}).then(function (j) {
      $("vorschau").hidden = true; $("hochBox").hidden = true;
      $("fertig").hidden = false;
      $("fertig").innerHTML = "<h2>Übernommen</h2><p>" + (j.commit ? "Die Karte ist aktualisiert (Commit <code>" + esc(j.commit.slice(0, 7)) + "</code>). Die <a href='map.html'>Map</a> zeigt jetzt den neuen Stand."
        : "Es gab nichts zu ändern, die Karte war schon auf diesem Stand.") + " Alle Änderungen stehen unter <a href='versionen.html'>Versionen</a>.</p>";
    }).catch(function (e) { b.disabled = false; meldung(m, e.message, true); });
  });
  $("verwerfen").addEventListener("click", function () {
    C.api("import/verwerfen", {}).then(function () { location.reload(); }).catch(function (e) { meldung($("endeMeldung"), e.message, true); });
  });

  /* ---------- Start ---------- */
  Promise.all([C.ich(), C.ladeJSON("campus/campus.json").catch(function () { return { gebaeude: [] }; })]).then(function (r) {
    wer = r[0]; campus = r[1].gebaeude;
    if (!wer) { hinweis("Die Karte aktualisieren geht nur auf dem Server mit Login."); return; }
    return C.api("import/status").then(function (s) { stand = s; zeige(); });
  }).catch(function (e) { hinweis("Fehler: " + e.message); });
})();
