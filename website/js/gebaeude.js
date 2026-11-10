/* Gebäudeseite: Tabs für 3D-Ansicht, Konfiguration, Einrichtung, Dokumente und Bauplan. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var id = new URLSearchParams(location.search).get("id") || "wabenhaus";
  var $ = function (s) { return document.getElementById(s); };
  C.navi(id);

  var D = null;            /* geladene Daten: geb, modell, konfig, einr, ordner */
  var kanaele = {};
  var VIEWS = ["ansicht", "konfig", "einrichtung", "dokumente", "bauplan"];

  C.ladeGebaeude(id).then(function (d) {
    D = d;
    D.konfig.netzwerke.forEach(function (n) { n.kanaele.forEach(function (k) { kanaele[k.nr] = k; }); });
    kopf();
    zeigeKonfig();
    zeigeEinrichtung();
    dokumente();
    bauplan();
    route();
    window.addEventListener("hashchange", route);
  }).catch(function (e) { $("titel").textContent = "Gebäude nicht gefunden"; $("zweck").textContent = e.message; });

  function kopf() {
    var g = D.geb;
    document.title = g.name + " · Tech-Campus";
    $("titel").textContent = g.name;
    $("zweck").textContent = g.zweck || "";
    var st = $("status"); st.textContent = g.status || ""; if (g.status === "gebaut") st.classList.add("ok");
    if (!(g.dateien && g.dateien.bauplan)) $("bauplanTab").hidden = true;
  }

  /* ---------- Routing über den Hash ---------- */
  function route() {
    var v = (location.hash || "#ansicht").slice(1);
    if (VIEWS.indexOf(v) < 0) v = "ansicht";
    VIEWS.forEach(function (n) { $("view-" + n).classList.toggle("on", n === v); });
    document.querySelectorAll(".subtabs a").forEach(function (a) { a.setAttribute("aria-current", a.getAttribute("data-view") === v ? "true" : "false"); });
    if (v === "ansicht") { if (!drei.sz) starte3D(); else drei.sz.groesse(); }
    if (v === "bauplan" && !$("bauplanFrame").src && D.geb.dateien && D.geb.dateien.bauplan) $("bauplanFrame").src = "../" + D.ordner + D.geb.dateien.bauplan;
  }
  function geheZu(view) { if (location.hash !== "#" + view) location.hash = view; else route(); }

  function welt(x, y, z) { return D.geb.welt ? C.weltVon(D.geb.welt.p0, D.geb.welt.drehung, x, y, z) : null; }
  function weltText(von, bis) {
    var w0 = welt(von[0], von[1], von[2]); if (!w0) return null;
    var w1 = welt(bis[0], bis[1], bis[2]);
    var lo = [0, 1, 2].map(function (i) { return Math.min(w0[i], w1[i]); }), hi = [0, 1, 2].map(function (i) { return Math.max(w0[i], w1[i]); });
    return lo.join(", ") + (lo.join() === hi.join() ? "" : " bis " + hi.join(", "));
  }
  function kChip(nr) { var k = kanaele[nr]; return "<span class='k' style='background:" + (k ? k.farbe : "#777") + "'>K" + nr + "</span>"; }

  /* ================= 3D-Ansicht ================= */
  var drei = { sz: null, halter: null, modell: null, ebene: "technik", maxY: 0, marker: [], hover: null, fest: null, kanalRahmen: [], aktiveKanaele: {} };

  function starte3D() {
    if (!D.modell) { $("loading").textContent = "Für dieses Gebäude gibt es noch kein Blockmodell (modell.json)."; uebersichtPanel(); return; }
    var sz = drei.sz = C.baueSzene($("viewport"));
    drei.halter = C.drehGruppe(D.geb.welt && D.geb.welt.drehung);
    sz.scene.add(drei.halter);
    D.modell.bloecke.forEach(function (b) { if (b[1] > drei.maxY) drei.maxY = b[1]; });
    var sl = $("schnitt"); sl.max = drei.maxY;
    sl.addEventListener("input", function () { setzeSchnitt(+sl.value); });
    $("ansichtReset").addEventListener("click", ansichtReset);
    document.querySelectorAll("[data-ebene]").forEach(function (b) { b.addEventListener("click", function () { setzeEbene(b.getAttribute("data-ebene")); }); });
    baueMarker();
    setzeSchnitt(Math.min(+sl.value, drei.maxY));
    ansichtReset();
    $("loading").hidden = true;
    uebersichtPanel();
    if (drei.warten) { var w = drei.warten; drei.warten = null; w(); }

    var ray = new THREE.Raycaster(), maus = new THREE.Vector2(), runter = null, canvas = sz.renderer.domElement;
    canvas.addEventListener("pointermove", function (ev) {
      var r = canvas.getBoundingClientRect();
      maus.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
      maus.y = -((ev.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(maus, sz.kamera);
      var ziele = drei.modellObj.pickbar.slice();
      if (drei.ebene === "einrichtung") ziele = ziele.concat(drei.marker.filter(function (m) { return m.visible; }));
      var t = ray.intersectObjects(ziele, false)[0];
      if (!t) { setzeHover(null); $("tooltip").hidden = true; return; }
      var ding = null, block = null, text;
      if (t.object.userData.einr) { ding = { art: "einr", teil: t.object.userData.einr }; text = ding.teil.name + " · " + ding.teil.zelle; }
      else {
        block = drei.modellObj.gibBlock(t.object, t.instanceId);
        if (drei.ebene === "technik") { var tt = konfigTeilBei(block); if (tt) ding = { art: "konfig", teil: tt, block: block }; }
        else { var et = einrBlockTeil(block); if (et) ding = { art: "einr", teil: et }; }
        var w = welt(block.x, block.y, block.z);
        text = (ding ? ding.teil.name + " · " : "") + block.sorte.name + " · " + zelleBei(block.x, block.z) + " · " + (w ? "Welt " + w.join(", ") : "Plan " + block.x + ", " + block.y + ", " + block.z);
      }
      setzeHover(ding);
      var tip = $("tooltip"), vr = $("viewport").getBoundingClientRect();
      tip.textContent = text; tip.style.left = (ev.clientX - vr.left) + "px"; tip.style.top = (ev.clientY - vr.top) + "px"; tip.hidden = false;
    });
    canvas.addEventListener("pointerleave", function () { setzeHover(null); $("tooltip").hidden = true; });
    canvas.addEventListener("pointerdown", function (ev) { runter = [ev.clientX, ev.clientY]; });
    canvas.addEventListener("pointerup", function (ev) {
      if (!runter || Math.hypot(ev.clientX - runter[0], ev.clientY - runter[1]) > 4) return;
      halteFest(drei.hover);
    });
  }

  function setzeSchnitt(y) {
    $("schnitt").value = y;
    $("schnittWert").textContent = "y " + y;
    if (drei.modellObj) drei.halter.remove(drei.modellObj.gruppe);
    drei.modellObj = C.baueModell(D.modell, { maxY: y });
    drei.halter.add(drei.modellObj.gruppe);
    markerSichtbar();
    drei.sz.neu();
  }
  function ansichtReset() {
    var box = C.weltBox(drei.halter, D.modell);
    C.blickeAuf(drei.sz, [box.min.x, 0, box.min.z], [box.max.x, 8, box.max.z]);
  }
  function setzeEbene(e) {
    drei.ebene = e;
    document.querySelectorAll("[data-ebene]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-ebene") === e ? "true" : "false"); });
    halteFest(null);
    markerSichtbar();
    kanalRahmenNeu();
    uebersichtPanel();
  }

  /* --- Einrichtungs-Marker --- */
  function baueMarker() {
    var honig = C.cssVar("--honey") || "#d9840b", grau = "#8a8c86";
    D.einr.teile.forEach(function (t) {
      (t.orte || []).forEach(function (o) {
        var min = [Math.min(o[0][0], o[1][0]), Math.min(o[0][1], o[1][1]), Math.min(o[0][2], o[1][2])];
        var max = [Math.max(o[0][0], o[1][0]) + 1, Math.max(o[0][1], o[1][1]) + 1, Math.max(o[0][2], o[1][2]) + 1];
        var farbe = t.status === "fertig" ? grau : honig;
        var g = new THREE.BoxGeometry(max[0] - min[0] + 0.1, max[1] - min[1] + 0.1, max[2] - min[2] + 0.1);
        var m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: farbe, transparent: true, opacity: 0.22, depthWrite: false }));
        m.position.set((min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2);
        m.renderOrder = 8;
        var kanten = new THREE.LineSegments(new THREE.EdgesGeometry(g), new THREE.LineBasicMaterial({ color: farbe, transparent: true, opacity: 0.9 }));
        m.add(kanten);
        m.userData = { einr: t, unten: min[1] };
        drei.marker.push(m);
        drei.halter.add(m);
      });
    });
  }
  function markerSichtbar() {
    var cut = +$("schnitt").value;
    drei.marker.forEach(function (m) { m.visible = drei.ebene === "einrichtung" && m.userData.unten <= cut; });
    if (drei.sz) drei.sz.neu();
  }

  /* --- Treffer zuordnen --- */
  function konfigTeilBei(b) {
    for (var i = 0; i < D.konfig.teile.length; i++) {
      var t = D.konfig.teile[i];
      if (b.x >= t.von[0] && b.x <= t.bis[0] && b.y >= t.von[1] && b.y <= t.bis[1] && b.z >= t.von[2] && b.z <= t.bis[2]) return t;
    }
    return null;
  }
  function einrBlockTeil(b) {
    for (var i = 0; i < D.einr.teile.length; i++) if (D.einr.teile[i].block && D.einr.teile[i].block === b.sorte.id) return D.einr.teile[i];
    return null;
  }
  function zelleBei(x, z) {
    var g = D.geb; if (!g.zellen || !g.zellen.length) return g.name;
    var w = g.wabe ? g.wabe.zelle : [0, 0], best = null, bd = Infinity;
    g.zellen.forEach(function (c) { var d = Math.hypot(x + 0.5 - (c.ursprung[0] + w[0] / 2), z + 0.5 - (c.ursprung[1] + w[1] / 2)); if (d < bd) { bd = d; best = c; } });
    return best ? best.name : g.name;
  }

  /* --- Hover und Festhalten --- */
  function rahmenFuer(ding, farbe, staerke) {
    var gr = new THREE.Group();
    boxenVon(ding).forEach(function (b) { gr.add(C.rahmen(b[0], b[1], farbe, staerke)); });
    return gr;
  }
  function boxenVon(ding) {
    var t = ding.teil;
    if (ding.art === "konfig") return [[[t.von[0], t.von[1], t.von[2]], [t.bis[0] + 1, t.bis[1] + 1, t.bis[2] + 1]]];
    return (t.orte || []).map(function (o) {
      return [[Math.min(o[0][0], o[1][0]), Math.min(o[0][1], o[1][1]), Math.min(o[0][2], o[1][2])], [Math.max(o[0][0], o[1][0]) + 1, Math.max(o[0][1], o[1][1]) + 1, Math.max(o[0][2], o[1][2]) + 1]];
    });
  }
  function gleich(a, b) { return a && b && a.art === b.art && a.teil === b.teil && (a.block ? a.block.sorte.id : "") === (b.block ? b.block.sorte.id : ""); }
  function setzeHover(ding) {
    if (gleich(ding, drei.hover) || (!ding && !drei.hover)) return;
    drei.hover = ding;
    if (drei.hoverRahmen) { drei.halter.remove(drei.hoverRahmen); drei.hoverRahmen = null; }
    if (ding && !(drei.fest && drei.fest.teil === ding.teil)) {
      drei.hoverRahmen = rahmenFuer(ding, C.cssVar("--honey") || "#d9840b", 0.8);
      drei.halter.add(drei.hoverRahmen);
    }
    drei.sz.renderer.domElement.classList.toggle("hovering", !!ding);
    if (!drei.fest) { if (ding) zeigeDing(ding); else uebersichtPanel(); }
    drei.sz.neu();
  }
  function halteFest(ding) {
    drei.fest = ding || null;
    if (drei.festRahmen) { drei.halter.remove(drei.festRahmen); drei.festRahmen = null; }
    if (drei.fest) {
      drei.festRahmen = rahmenFuer(drei.fest, C.cssVar("--honey") || "#d9840b", 1);
      drei.halter.add(drei.festRahmen);
      zeigeDing(drei.fest);
    } else uebersichtPanel();
    if (drei.sz) drei.sz.neu();
  }
  function fokussiere(ding) {
    var boxen = boxenVon(ding);
    if (!boxen.length) { halteFest(ding); return; }
    var oben = Math.max.apply(null, boxen.map(function (b) { return b[1][1]; }));
    var unten = Math.min.apply(null, boxen.map(function (b) { return b[0][1]; }));
    var cut = +$("schnitt").value;
    if (cut < oben - 1 || cut < unten) setzeSchnitt(Math.min(drei.maxY, Math.max(oben, 5)));
    halteFest(ding);
    var mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    boxen.forEach(function (b) { for (var a = 0; a < 3; a++) { mn[a] = Math.min(mn[a], b[0][a]); mx[a] = Math.max(mx[a], b[1][a]); } });
    var c = drei.halter.localToWorld(new THREE.Vector3((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2));
    var weite = Math.max(34, Math.max(mx[0] - mn[0], mx[2] - mn[2]) * 1.8);
    var off = drei.sz.kamera.position.clone().sub(drei.sz.steuerung.target).setLength(weite);
    drei.sz.steuerung.target.copy(c); drei.sz.kamera.position.copy(c).add(off); drei.sz.steuerung.update(); drei.sz.neu();
  }
  /* Von anderen Tabs aus: Teil in 3D zeigen */
  function zeigeIn3D(art, teil) {
    var los = function () {
      if (drei.ebene !== (art === "konfig" ? "technik" : "einrichtung")) setzeEbene(art === "konfig" ? "technik" : "einrichtung");
      fokussiere({ art: art, teil: teil });
    };
    geheZu("ansicht");
    if (drei.sz) setTimeout(los, 30); else drei.warten = los;
  }

  function kanalRahmenNeu() {
    if (!drei.sz) return;
    drei.kanalRahmen.forEach(function (r) { drei.halter.remove(r); }); drei.kanalRahmen = [];
    if (drei.ebene !== "technik") { drei.sz.neu(); return; }
    Object.keys(drei.aktiveKanaele).forEach(function (nr) {
      D.konfig.teile.forEach(function (t) {
        if (!(t.nodes || []).some(function (n) { return n.kanaele.some(function (k) { return String(k.k) === nr; }); })) return;
        var r = rahmenFuer({ art: "konfig", teil: t }, kanaele[nr].farbe, 1);
        drei.kanalRahmen.push(r); drei.halter.add(r);
      });
    });
    drei.sz.neu();
  }

  /* --- Panel rechts --- */
  function uebersichtPanel() {
    var g = D.geb, p = $("panel"), h = "<div><h2>" + esc(g.name) + "</h2><p class='meta'>" + esc(g.zweck || "") + "</p></div>";
    h += "<dl class='kv'>";
    if (g.masse && g.masse.breite) h += "<dt>Größe</dt><dd>" + g.masse.breite + " × " + g.masse.tiefe + " Blöcke, " + g.masse.hoehe + " hoch</dd>";
    h += "<dt>P0 in der Welt</dt><dd>" + (g.welt && g.welt.p0 ? g.welt.p0.join(", ") : "noch nicht eingetragen") + "</dd>";
    if (g.welt && g.welt.drehung) h += "<dt>Drehung</dt><dd>" + g.welt.drehung + "° im Uhrzeigersinn, Ansicht wie in der Welt</dd>";
    h += "</dl>";
    if (drei.ebene === "technik") {
      D.konfig.netzwerke.forEach(function (n) {
        h += "<div><h3>" + esc(n.mod) + " „" + esc(n.name) + "“</h3><div class='channels'>";
        n.kanaele.forEach(function (k) { h += "<button type='button' data-k='" + k.nr + "' aria-pressed='" + (drei.aktiveKanaele[k.nr] ? "true" : "false") + "' title='" + esc(k.zweck) + "'>" + kChip(k.nr) + esc(k.typ) + "</button>"; });
        h += "</div><p class='meta' style='margin:8px 0 0;font-size:13px'>Kanal anklicken, um alle Teile darauf zu markieren.</p></div>";
      });
      if (D.konfig.teile.length) {
        h += "<div><h3>Teile</h3><div class='parts'>";
        D.konfig.teile.forEach(function (t, i) { h += "<button type='button' data-kt='" + i + "'>" + esc(t.name) + "<span>" + esc(t.zelle || "") + "</span></button>"; });
        h += "</div></div>";
      }
      h += "<p class='note'>Fahr über eine Maschine oder ein Barrel, um die Konfiguration zu sehen.</p>";
    } else {
      var f = D.einr.teile.filter(function (t) { return t.status === "fertig"; }).length;
      h += "<div><h3>Einrichtung</h3><p class='meta' style='margin:0 0 6px'>" + f + " von " + D.einr.teile.length + " fertig</p><div class='balken'><i style='width:" + (D.einr.teile.length ? Math.round(f / D.einr.teile.length * 100) : 0) + "%'></i></div></div>";
      h += "<div><h3>Teile</h3><div class='parts'>";
      D.einr.teile.forEach(function (t, i) { h += "<button type='button' data-et='" + i + "'>" + esc(t.name) + "<span>" + esc(t.zelle) + "</span></button>"; });
      h += "</div></div><p class='note'>Orange Kästen sind offen, graue fertig. Fahr darüber für Details.</p>";
    }
    p.innerHTML = h;
    p.querySelectorAll("[data-k]").forEach(function (b) {
      b.addEventListener("click", function () {
        var nr = b.getAttribute("data-k");
        if (drei.aktiveKanaele[nr]) delete drei.aktiveKanaele[nr]; else drei.aktiveKanaele[nr] = 1;
        b.setAttribute("aria-pressed", drei.aktiveKanaele[nr] ? "true" : "false");
        kanalRahmenNeu();
      });
    });
    p.querySelectorAll("[data-kt]").forEach(function (b) { b.addEventListener("click", function () { if (drei.sz) fokussiere({ art: "konfig", teil: D.konfig.teile[+b.getAttribute("data-kt")] }); }); });
    p.querySelectorAll("[data-et]").forEach(function (b) { b.addEventListener("click", function () { if (drei.sz) fokussiere({ art: "einr", teil: D.einr.teile[+b.getAttribute("data-et")] }); }); });
  }

  function zeigeDing(ding) {
    var p = $("panel"), t = ding.teil, h;
    if (ding.art === "konfig") h = konfigKarte(t, ding.block);
    else h = einrKarte(t);
    if (drei.fest && drei.fest.teil === t) h += "<button type='button' class='unpin' id='unpin'>Loslassen</button>";
    p.innerHTML = h;
    var u = $("unpin"); if (u) u.addEventListener("click", function () { halteFest(null); });
  }
  function konfigKarte(t, block) {
    var h = "<div><h2>" + esc(t.name) + "</h2><p class='meta'>" + esc(t.art || "") + (t.zelle ? " · " + esc(t.zelle) : "") + "</p></div>";
    var eins = t.bis.join() === t.von.join(), wt = weltText(t.von, t.bis);
    h += "<dl class='kv'><dt>Plan</dt><dd>" + t.von.join(", ") + (eins ? "" : " bis " + t.bis.join(", ")) + "</dd>";
    if (wt) h += "<dt>Welt</dt><dd>" + wt + "</dd>";
    if (t.aufbau) h += "<dt>Aufbau</dt><dd>" + esc(t.aufbau) + "</dd>";
    (t.einstellungen || []).forEach(function (e) { h += "<dt>" + esc(e[0]) + "</dt><dd>" + esc(e[1]) + "</dd>"; });
    h += "</dl>";
    if (t.nodes && t.nodes.length) {
      h += "<div><h3>Nodes</h3><div class='nodes'>";
      t.nodes.forEach(function (n) {
        var aktiv = block && n.block && block.sorte.id === n.block;
        h += "<div class='node" + (aktiv ? " active" : "") + "'><div class='head'>" + esc(n.label) + "<span>" + (n.anzahl || 1) + " ×</span></div><div class='ch'>";
        n.kanaele.forEach(function (k) { h += kChip(k.k) + "<span class='dir'>" + esc(k.richtung) + "</span><span>" + esc(k.filter || "") + "</span>"; });
        h += "</div></div>";
      });
      h += "</div></div>";
    }
    if (t.hinweise && t.hinweise.length) h += "<div><h3>Hinweise</h3><ul class='hinweise'>" + t.hinweise.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>";
    return h;
  }
  function einrKarte(t) {
    var h = "<div><h2>" + esc(t.name) + "</h2><p class='meta'>" + esc(t.zelle) + "</p></div>";
    h += "<div><span class='status " + esc(t.status) + "'>" + esc(t.status) + "</span></div>";
    h += "<p style='margin:0'>" + esc(t.was || "") + "</p><dl class='kv'>";
    if (t.mod) h += "<dt>Mod</dt><dd>" + esc(t.mod) + "</dd>";
    (t.orte || []).forEach(function (o, i) {
      var wt = weltText(o[0], o[1]);
      h += "<dt>" + (t.orte.length > 1 ? "Ort " + (i + 1) : "Ort") + "</dt><dd>" + (wt ? "Welt " + wt : "Plan " + o[0].join(", ")) + "</dd>";
    });
    if (t.block) h += "<dt>Ort</dt><dd>alle markierten Plätze im Modell</dd>";
    if (!t.block && !(t.orte || []).length) h += "<dt>Ort</dt><dd>noch nicht festgelegt</dd>";
    return h + "</dl>";
  }

  /* ================= Konfiguration ================= */
  function zeigeKonfig() {
    var nrs = []; D.konfig.netzwerke.forEach(function (n) { n.kanaele.forEach(function (k) { nrs.push(k.nr); }); });
    var h = "<thead><tr><th>Teil</th>" + nrs.map(function (nr) { return "<th class='c' title='" + esc(kanaele[nr].zweck) + "'>" + kChip(nr) + "</th>"; }).join("") + "<th>Nodes</th></tr></thead><tbody>";
    D.konfig.teile.forEach(function (t, i) {
      var nodes = 0; (t.nodes || []).forEach(function (n) { nodes += n.anzahl || 1; });
      var wt = weltText(t.von, t.bis);
      h += "<tr><td><button type='button' class='teil' data-zeige='" + i + "'>" + esc(t.name) + "</button><span class='ort'>" + esc(t.zelle || "") + (wt ? " · " + wt : "") + "</span></td>";
      nrs.forEach(function (nr) {
        var rein = false, raus = false;
        (t.nodes || []).forEach(function (n) { n.kanaele.forEach(function (k) { if (k.k === nr) { if (k.richtung === "rein") rein = true; else raus = true; } }); });
        var f = kanaele[nr].farbe, c = "";
        if (raus) c += "<span class='pfeil' style='background:" + f + "' title='sendet'>raus →</span> ";
        if (rein) c += "<span class='pfeil rein' style='color:" + f + "' title='empfängt'>→ rein</span>";
        h += "<td class='c'>" + c + "</td>";
      });
      h += "<td class='c'>" + nodes + "</td></tr>";
    });
    $("matrix").innerHTML = h + "</tbody>";
    $("matrix").querySelectorAll("[data-zeige]").forEach(function (b) { b.addEventListener("click", function () { zeigeIn3D("konfig", D.konfig.teile[+b.getAttribute("data-zeige")]); }); });

    var f = "";
    nrs.forEach(function (nr) {
      var sender = [], empf = [];
      D.konfig.teile.forEach(function (t) {
        (t.nodes || []).forEach(function (n) { n.kanaele.forEach(function (k) {
          if (k.k !== nr) return;
          var txt = n.label === t.name ? t.name : t.name + " · " + n.label;
          var eintrag = "<span title='" + esc(k.filter || "") + "'>" + esc(txt) + "</span>";
          if (k.richtung === "rein") { if (empf.indexOf(eintrag) < 0) empf.push(eintrag); } else if (sender.indexOf(eintrag) < 0) sender.push(eintrag);
        }); });
      });
      f += "<div class='box flow'><div class='kopf'><span>" + kChip(nr) + " <strong>" + esc(kanaele[nr].typ) + "</strong></span><small>" + esc(kanaele[nr].zweck) + "</small></div>";
      f += "<div class='wer'>" + (sender.join("") || "<span>–</span>") + "</div><div class='arrow'>→</div><div class='wer'>" + (empf.join("") || "<span>–</span>") + "</div></div>";
    });
    $("fluesse").innerHTML = f || "<p class='note'>Noch keine Kanäle eingetragen.</p>";
  }

  /* ================= Einrichtung ================= */
  function zeigeEinrichtung() {
    var zellen = [];
    D.einr.teile.forEach(function (t) { if (zellen.indexOf(t.zelle) < 0) zellen.push(t.zelle); });
    var fh = "";
    zellen.forEach(function (z) {
      var liste = D.einr.teile.filter(function (t) { return t.zelle === z; }), fertig = liste.filter(function (t) { return t.status === "fertig"; }).length;
      fh += "<div class='box zelle'><strong>" + esc(z) + "</strong><div class='balken'><i style='width:" + Math.round(fertig / liste.length * 100) + "%'></i></div><small>" + fertig + " von " + liste.length + " fertig</small></div>";
    });
    $("fortschritt").innerHTML = fh || "<p class='note'>Noch keine Einrichtung eingetragen.</p>";

    var sh = "";
    if ((D.einr.stil || []).length || (D.einr.mods || []).length) {
      sh += "<div class='box' style='padding:14px 18px;display:grid;gap:10px'>";
      if ((D.einr.stil || []).length) sh += "<div><h3 style='margin:0 0 6px;font:600 11px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)'>Stilregeln</h3><ul class='hinweise'>" + D.einr.stil.map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") + "</ul></div>";
      if ((D.einr.mods || []).length) sh += "<div><h3 style='margin:0 0 6px;font:600 11px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)'>Mods</h3><dl class='kv'>" + D.einr.mods.map(function (m) { return "<dt>" + esc(m[0]) + "</dt><dd>" + esc(m[1]) + "</dd>"; }).join("") + "</dl></div>";
      sh += "</div>";
    }
    $("stil").innerHTML = sh;

    var h = "";
    zellen.forEach(function (z) {
      h += "<h3>" + esc(z) + "</h3><div class='karten'>";
      D.einr.teile.forEach(function (t, i) {
        if (t.zelle !== z) return;
        var hatOrt = t.block || (t.orte || []).length;
        h += "<article class='box karte'><div class='oben'><strong>" + esc(t.name) + "</strong><span class='status " + esc(t.status) + "'>" + esc(t.status) + "</span></div>";
        if (t.mod) h += "<span class='mod'>" + esc(t.mod) + "</span>";
        h += "<p>" + esc(t.was || "") + "</p>";
        if (hatOrt && D.modell) h += "<button type='button' class='zeige' data-einr='" + i + "'>Im 3D zeigen</button>";
        h += "</article>";
      });
      h += "</div>";
    });
    $("einrListe").innerHTML = h;
    $("einrListe").querySelectorAll("[data-einr]").forEach(function (b) { b.addEventListener("click", function () { zeigeIn3D("einr", D.einr.teile[+b.getAttribute("data-einr")]); }); });
  }

  /* ================= Dokumente und Bauplan ================= */
  function dokumente() {
    var tabs = document.querySelectorAll("[data-doc]");
    function zeige(name) {
      tabs.forEach(function (t) { t.setAttribute("aria-pressed", t.getAttribute("data-doc") === name ? "true" : "false"); });
      var datei = D.geb.dateien && D.geb.dateien[name];
      if (!datei) { $("doc").innerHTML = "<p>Noch keine Datei.</p>"; return; }
      C.ladeText(D.ordner + datei).then(function (md) {
        $("doc").innerHTML = marked.parse(md);
        $("doc").querySelectorAll("a[href]").forEach(function (a) {
          var href = a.getAttribute("href");
          if (/^(einrichtung|konfig)\.md$/.test(href)) a.addEventListener("click", function (e) { e.preventDefault(); zeige(href.replace(".md", "")); });
          else if (!/^https?:/.test(href)) a.href = "../" + D.ordner + href;
        });
      }).catch(function (e) { $("doc").textContent = e.message; });
    }
    tabs.forEach(function (t) { t.addEventListener("click", function () { zeige(t.getAttribute("data-doc")); }); });
    zeige("konfig");
  }
  function bauplan() {
    if (D.geb.dateien && D.geb.dateien.bauplan) $("bauplanNeu").href = "../" + D.ordner + D.geb.dateien.bauplan;
  }
})();
