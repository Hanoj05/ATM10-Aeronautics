/* Gebäudeseite: 3D-Modell, Hover über Teile zeigt deren Konfiguration. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var id = new URLSearchParams(location.search).get("id") || "wabenhaus";
  var ordner = "gebaeude/" + id + "/";

  var $ = function (s) { return document.getElementById(s); };
  var panel = $("panel"), tooltip = $("tooltip"), viewport = $("viewport");
  var geb, konfig = { netzwerke: [], teile: [] }, modell = null;
  var kanaele = {};
  var sz, aktuell = null, maxY = 0, halter = null;
  var hoverRahmen = null, festRahmen = null, kanalRahmen = [];
  var fest = null, aktiveKanaele = {};

  function optional(p) { return C.ladeJSON(p).catch(function () { return null; }); }

  Promise.all([C.ladeJSON(ordner + "gebaeude.json"), optional(ordner + "konfig.json"), optional(ordner + "modell.json")])
    .then(function (r) {
      geb = r[0]; if (r[1]) konfig = r[1]; modell = r[2];
      konfig.netzwerke.forEach(function (n) { n.kanaele.forEach(function (k) { kanaele[k.nr] = k; }); });
      kopf(); dokumente(); uebersicht();
      if (modell) starte3D();
      else $("loading").textContent = "Für dieses Gebäude gibt es noch kein Blockmodell (modell.json).";
    })
    .catch(function (e) { $("loading").textContent = "Fehler: " + e.message; });

  function kopf() {
    document.title = geb.name + " · Tech-Campus";
    $("titel").textContent = geb.name;
    $("zweck").textContent = geb.zweck || "";
    var st = $("status"); st.textContent = geb.status || ""; if (geb.status === "gebaut") st.classList.add("ok");
    var bp = $("bauplanLink");
    if (geb.dateien && geb.dateien.bauplan) bp.href = "../" + ordner + geb.dateien.bauplan; else bp.hidden = true;
  }

  /* ---------- 3D ---------- */
  function starte3D() {
    sz = C.baueSzene(viewport);
    halter = C.drehGruppe(geb.welt && geb.welt.drehung);
    sz.scene.add(halter);
    modell.bloecke.forEach(function (b) { if (b[1] > maxY) maxY = b[1]; });
    var sl = $("schnitt"); sl.max = maxY;
    sl.addEventListener("input", function () { setzeSchnitt(+sl.value); });
    setzeSchnitt(Math.min(+sl.value, maxY));
    $("ansicht").addEventListener("click", ansicht);
    ansicht();
    $("loading").hidden = true;

    var ray = new THREE.Raycaster(), maus = new THREE.Vector2(), runter = null;
    sz.renderer.domElement.addEventListener("pointermove", function (ev) {
      var r = sz.renderer.domElement.getBoundingClientRect();
      maus.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
      maus.y = -((ev.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(maus, sz.kamera);
      var treffer = ray.intersectObjects(aktuell.pickbar, false)[0];
      if (!treffer) { hover(null); tooltip.hidden = true; return; }
      var b = aktuell.gibBlock(treffer.object, treffer.instanceId);
      var teil = teilBei(b.x, b.y, b.z);
      hover(teil, b);
      var w = welt(b.x, b.y, b.z);
      tooltip.textContent = (teil ? teil.name + " · " : "") + b.sorte.name + " · " + zelleBei(b.x, b.z) + " · " + (w ? "Welt " + w.join(", ") : "Plan " + b.x + ", " + b.y + ", " + b.z);
      var vr = viewport.getBoundingClientRect();
      tooltip.style.left = (ev.clientX - vr.left) + "px";
      tooltip.style.top = (ev.clientY - vr.top) + "px";
      tooltip.hidden = false;
    });
    sz.renderer.domElement.addEventListener("pointerleave", function () { hover(null); tooltip.hidden = true; });
    sz.renderer.domElement.addEventListener("pointerdown", function (ev) { runter = [ev.clientX, ev.clientY]; });
    sz.renderer.domElement.addEventListener("pointerup", function (ev) {
      if (!runter || Math.hypot(ev.clientX - runter[0], ev.clientY - runter[1]) > 4) return;
      halteFest(letzterHover ? letzterHover.teil : null, letzterHover ? letzterHover.block : null);
    });
  }

  function setzeSchnitt(y) {
    $("schnittWert").textContent = "y " + y;
    if (aktuell) halter.remove(aktuell.gruppe);
    aktuell = C.baueModell(modell, { maxY: y });
    halter.add(aktuell.gruppe);
    sz.neu();
  }

  function ansicht() {
    var box = C.weltBox(halter, modell);
    C.blickeAuf(sz, [box.min.x, 0, box.min.z], [box.max.x, 8, box.max.z]);
  }

  function teilBei(x, y, z) {
    for (var i = 0; i < konfig.teile.length; i++) {
      var t = konfig.teile[i];
      if (x >= t.von[0] && x <= t.bis[0] && y >= t.von[1] && y <= t.bis[1] && z >= t.von[2] && z <= t.bis[2]) return t;
    }
    return null;
  }
  function zelleBei(x, z) {
    if (!geb.zellen || !geb.zellen.length) return geb.name;
    var w = geb.wabe ? geb.wabe.zelle : [0, 0], best = null, bd = Infinity;
    geb.zellen.forEach(function (c) {
      var d = Math.hypot(x + 0.5 - (c.ursprung[0] + w[0] / 2), z + 0.5 - (c.ursprung[1] + w[1] / 2));
      if (d < bd) { bd = d; best = c; }
    });
    return best ? best.name : geb.name;
  }
  function welt(x, y, z) { return geb.welt ? C.weltVon(geb.welt.p0, geb.welt.drehung, x, y, z) : null; }
  function boxVon(t) { return [[t.von[0], t.von[1], t.von[2]], [t.bis[0] + 1, t.bis[1] + 1, t.bis[2] + 1]]; }

  var letzterHover = null;
  function hover(teil, block) {
    letzterHover = teil || block ? { teil: teil, block: block } : null;
    var key = teil ? teil.id + "|" + (block ? block.sorte.id : "") : "";
    if (hover.key === key) return;
    hover.key = key;
    if (hoverRahmen) { halter.remove(hoverRahmen); hoverRahmen = null; }
    if (teil && teil !== fest) {
      var b = boxVon(teil);
      hoverRahmen = C.rahmen(b[0], b[1], C.cssVar("--honey") || "#d9840b", 0.8);
      halter.add(hoverRahmen);
    }
    sz.renderer.domElement.classList.toggle("hovering", !!teil);
    if (!fest) { if (teil) zeigeTeil(teil, block); else uebersicht(); }
    sz.neu();
  }
  function halteFest(teil, block) {
    fest = teil || null;
    if (festRahmen) { halter.remove(festRahmen); festRahmen = null; }
    if (fest) {
      var b = boxVon(fest);
      festRahmen = C.rahmen(b[0], b[1], C.cssVar("--honey") || "#d9840b", 1);
      halter.add(festRahmen);
      zeigeTeil(fest, block);
    } else uebersicht();
    sz.neu();
  }

  function kanalRahmenNeu() {
    kanalRahmen.forEach(function (r) { halter.remove(r); }); kanalRahmen = [];
    Object.keys(aktiveKanaele).forEach(function (nr) {
      konfig.teile.forEach(function (t) {
        var nutzt = (t.nodes || []).some(function (n) { return n.kanaele.some(function (k) { return String(k.k) === nr; }); });
        if (!nutzt) return;
        var b = boxVon(t), r = C.rahmen(b[0], b[1], kanaele[nr].farbe, 1);
        kanalRahmen.push(r); halter.add(r);
      });
    });
    if (sz) sz.neu();
  }

  /* ---------- Panel ---------- */
  function kChip(nr) {
    var k = kanaele[nr];
    return "<span class='k' style='background:" + (k ? k.farbe : "#777") + "'>K" + nr + "</span>";
  }
  function uebersicht() {
    var h = "<div><h2>" + esc(geb.name) + "</h2><p class='meta'>" + esc(geb.zweck || "") + "</p></div>";
    h += "<dl class='kv'>";
    if (geb.masse && geb.masse.breite) h += "<dt>Größe</dt><dd>" + geb.masse.breite + " × " + geb.masse.tiefe + " Blöcke, " + geb.masse.hoehe + " hoch</dd>";
    if (geb.zellen) h += "<dt>Zellen</dt><dd>" + geb.zellen.map(function (c) { return esc(c.name); }).join(", ") + "</dd>";
    h += "<dt>P0 in der Welt</dt><dd>" + (geb.welt && geb.welt.p0 ? geb.welt.p0.join(", ") : "noch nicht eingetragen") + "</dd>";
    if (geb.welt && geb.welt.drehung) h += "<dt>Drehung</dt><dd>" + geb.welt.drehung + "° im Uhrzeigersinn, die Ansicht ist wie in der Welt ausgerichtet</dd>";
    h += "</dl>";
    konfig.netzwerke.forEach(function (n) {
      h += "<div><h3>" + esc(n.mod) + " „" + esc(n.name) + "“</h3><div class='channels'>";
      n.kanaele.forEach(function (k) {
        h += "<button type='button' data-k='" + k.nr + "' aria-pressed='" + (aktiveKanaele[k.nr] ? "true" : "false") + "' title='" + esc(k.zweck) + "'>" + kChip(k.nr) + esc(k.typ) + "</button>";
      });
      h += "</div><p class='meta' style='margin:8px 0 0;font-size:13px'>Kanal anklicken, um alle Teile darauf im Modell zu markieren.</p></div>";
    });
    if (konfig.teile.length) {
      h += "<div><h3>Teile</h3><div class='parts'>";
      konfig.teile.forEach(function (t) { h += "<button type='button' data-teil='" + esc(t.id) + "'>" + esc(t.name) + "<span>" + esc(t.zelle || "") + "</span></button>"; });
      h += "</div></div>";
    }
    h += "<p class='note'>Fahr im Modell über eine Maschine oder ein Barrel, um die Konfiguration zu sehen. Mit dem Schnitt-Regler schaust du in die Räume.</p>";
    panel.innerHTML = h;
    panel.querySelectorAll("[data-k]").forEach(function (b) {
      b.addEventListener("click", function () {
        var nr = b.getAttribute("data-k");
        if (aktiveKanaele[nr]) delete aktiveKanaele[nr]; else aktiveKanaele[nr] = 1;
        b.setAttribute("aria-pressed", aktiveKanaele[nr] ? "true" : "false");
        kanalRahmenNeu();
      });
    });
    panel.querySelectorAll("[data-teil]").forEach(function (b) {
      b.addEventListener("click", function () {
        var t = konfig.teile.filter(function (x) { return x.id === b.getAttribute("data-teil"); })[0];
        if (!t || !sz) return;
        var bx = boxVon(t);
        if (+$("schnitt").value < t.bis[1]) { $("schnitt").value = t.bis[1] + 1; setzeSchnitt(t.bis[1] + 1); }
        halteFest(t, null);
        var c = halter.localToWorld(new THREE.Vector3((bx[0][0] + bx[1][0]) / 2, (bx[0][1] + bx[1][1]) / 2, (bx[0][2] + bx[1][2]) / 2));
        var off = sz.kamera.position.clone().sub(sz.steuerung.target).setLength(26);
        sz.steuerung.target.copy(c); sz.kamera.position.copy(c).add(off); sz.steuerung.update(); sz.neu();
      });
    });
  }

  function zeigeTeil(t, block) {
    var h = "<div><h2>" + esc(t.name) + "</h2><p class='meta'>" + esc(t.art || "") + (t.zelle ? " · " + esc(t.zelle) : "") + "</p></div>";
    var w0 = welt(t.von[0], t.von[1], t.von[2]), w1 = welt(t.bis[0], t.bis[1], t.bis[2]), eins = t.bis.join() === t.von.join();
    h += "<dl class='kv'><dt>Plan</dt><dd>" + t.von.join(", ") + (eins ? "" : " bis " + t.bis.join(", ")) + "</dd>";
    if (w0) {
      var lo = [0, 1, 2].map(function (i) { return Math.min(w0[i], w1[i]); }), hi = [0, 1, 2].map(function (i) { return Math.max(w0[i], w1[i]); });
      h += "<dt>Welt</dt><dd>" + lo.join(", ") + (eins ? "" : " bis " + hi.join(", ")) + "</dd>";
    }
    if (t.aufbau) h += "<dt>Aufbau</dt><dd>" + esc(t.aufbau) + "</dd>";
    (t.einstellungen || []).forEach(function (e) { h += "<dt>" + esc(e[0]) + "</dt><dd>" + esc(e[1]) + "</dd>"; });
    h += "</dl>";
    if (t.nodes && t.nodes.length) {
      h += "<div><h3>Nodes</h3><div class='nodes'>";
      t.nodes.forEach(function (n) {
        var aktiv = block && n.block && block.sorte.id === n.block;
        h += "<div class='node" + (aktiv ? " active" : "") + "'><div class='head'>" + esc(n.label) + "<span>" + n.anzahl + " ×</span></div><div class='ch'>";
        n.kanaele.forEach(function (k) { h += kChip(k.k) + "<span class='dir'>" + esc(k.richtung) + "</span><span>" + esc(k.filter || "") + "</span>"; });
        h += "</div></div>";
      });
      h += "</div></div>";
    }
    if (t.hinweise && t.hinweise.length) h += "<div><h3>Hinweise</h3><ul class='hinweise'>" + t.hinweise.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul></div>";
    if (fest === t) h += "<button type='button' class='unpin' id='unpin'>Loslassen</button>";
    panel.innerHTML = h;
    var u = $("unpin"); if (u) u.addEventListener("click", function () { halteFest(null); });
  }

  /* ---------- Dokumente ---------- */
  function dokumente() {
    var tabs = document.querySelectorAll("[data-doc]");
    function zeige(name) {
      tabs.forEach(function (t) { t.setAttribute("aria-pressed", t.getAttribute("data-doc") === name ? "true" : "false"); });
      var datei = geb.dateien && geb.dateien[name];
      if (!datei) { $("doc").innerHTML = "<p>Noch keine Datei für „" + name + "“.</p>"; return; }
      C.ladeText(ordner + datei).then(function (md) {
        $("doc").innerHTML = marked.parse(md);
        $("doc").querySelectorAll("a[href]").forEach(function (a) {
          var href = a.getAttribute("href");
          if (/^(einrichtung|konfig)\.md$/.test(href)) a.addEventListener("click", function (e) { e.preventDefault(); zeige(href.replace(".md", "")); });
          else if (!/^https?:/.test(href)) a.href = "../" + ordner + href;
        });
      }).catch(function (e) { $("doc").textContent = e.message; });
    }
    tabs.forEach(function (t) { t.addEventListener("click", function () { zeige(t.getAttribute("data-doc")); }); });
    zeige("konfig");
  }
})();
