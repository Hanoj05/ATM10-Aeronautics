/* Abgespeckte Campus-Ansicht. Daten kommen aus daten.js (window.CAMPUS_DATEN), deshalb
 * läuft alles auch per Doppelklick ohne Webserver. Zeichnen übernimmt voxel.js der Website. */
(function () {
  "use strict";
  var C = window.Campus, D = window.CAMPUS_DATEN, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };

  function link(g) { return "gebaeude.html?id=" + encodeURIComponent(g.id); }

  /* Maus über Meshes verfolgen: liefert Treffer oder null an die Funktion. */
  function hover(sz, ziele, wenn, klick) {
    var ray = new THREE.Raycaster(), maus = new THREE.Vector2(), canvas = sz.renderer.domElement, runter = null;
    function treffer(ev) {
      var r = canvas.getBoundingClientRect();
      maus.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(maus, sz.kamera);
      var t = ray.intersectObjects(ziele(), false)[0];
      return t ? { t: t, x: ev.clientX - r.left, y: ev.clientY - r.top } : null;
    }
    canvas.addEventListener("pointermove", function (ev) { wenn(treffer(ev)); });
    canvas.addEventListener("pointerleave", function () { wenn(null); });
    if (klick) {
      canvas.addEventListener("pointerdown", function (ev) { runter = [ev.clientX, ev.clientY]; });
      canvas.addEventListener("pointerup", function (ev) {
        if (runter && Math.hypot(ev.clientX - runter[0], ev.clientY - runter[1]) < 5) { var h = treffer(ev); if (h) klick(h); }
        runter = null;
      });
    }
  }

  function zeigeTip(h, text) {
    var tip = $("tip");
    if (!h) { tip.hidden = true; return; }
    tip.textContent = text; tip.style.left = h.x + "px"; tip.style.top = h.y + "px"; tip.hidden = false;
  }

  function map() {
    $("welt").textContent = D.welt || "";
    var liste = D.gebaeude.filter(function (g) { return g.modell; });
    $("liste").innerHTML = liste.map(function (g, i) {
      return "<a href='" + link(g) + "' data-i='" + i + "'><strong>" + esc(g.name) + "</strong><span>" + esc(g.zweck || "") + " · " + esc(g.status || "") + "</span></a>";
    }).join("");

    var sz = C.baueSzene($("viewport")), pick = [], gesamt = { min: [Infinity, 0, Infinity], max: [-Infinity, 10, -Infinity] };
    var basis = null, reserve = 0;
    liste.forEach(function (g) { if (g.position && !basis) basis = g.position; });
    /* Gebäude ohne Weltposition kommen rechts neben die eingetragenen */
    liste.forEach(function (g) {
      if (g.position && basis && g.masse) reserve = Math.max(reserve, g.position[0] - basis[0] + Math.max(g.masse.breite || 0, g.masse.tiefe || 0) + 20);
    });
    liste.forEach(function (g) {
      var vs;
      if (g.position && basis) vs = [g.position[0] - basis[0], g.position[1] - basis[1], g.position[2] - basis[2]];
      else { vs = [reserve, 0, 0]; reserve += (g.masse && g.masse.breite || 40) + 20; }
      var halter = C.drehGruppe(g.drehung);
      halter.position.x += vs[0]; halter.position.y += vs[1]; halter.position.z += vs[2];
      var m = C.baueModell(g.modell);
      halter.add(m.gruppe);
      m.pickbar.forEach(function (p) { p.userData.geb = g; pick.push(p); });
      sz.scene.add(halter);
      var b = C.weltBox(halter, g.modell);
      gesamt.min = [Math.min(gesamt.min[0], b.min.x), 0, Math.min(gesamt.min[2], b.min.z)];
      gesamt.max = [Math.max(gesamt.max[0], b.max.x), Math.max(gesamt.max[1], b.max.y), Math.max(gesamt.max[2], b.max.z)];
    });
    var spanne = Math.max(200, (gesamt.max[0] - gesamt.min[0]) * 3, (gesamt.max[2] - gesamt.min[2]) * 3);
    var gitter = new THREE.GridHelper(spanne, Math.round(spanne / 8), 0x9a978d, 0xb9b6ad);
    gitter.position.set((gesamt.min[0] + gesamt.max[0]) / 2, -0.01, (gesamt.min[2] + gesamt.max[2]) / 2);
    gitter.material.transparent = true; gitter.material.opacity = 0.45;
    sz.scene.add(gitter);
    function reset() {
      C.blickeAuf(sz, gesamt.min, [gesamt.max[0], gesamt.max[1] * 0.4, gesamt.max[2]]);
      /* etwas weiter weg, damit alle Gebäude ganz ins Bild passen */
      var t = sz.steuerung.target; sz.kamera.position.sub(t).multiplyScalar(1.3).add(t);
      sz.steuerung.update(); sz.neu();
    }
    $("reset").addEventListener("click", reset);
    reset();
    $("laden").hidden = !!liste.length;
    if (!liste.length) $("laden").textContent = "Noch kein Gebäude mit Blockmodell.";

    var links = $("liste").querySelectorAll("a");
    hover(sz, function () { return pick; }, function (h) {
      var g = h && h.t.object.userData.geb;
      sz.renderer.domElement.classList.toggle("zeiger", !!g);
      links.forEach(function (a) { a.classList.toggle("an", !!g && liste[+a.getAttribute("data-i")] === g); });
      zeigeTip(h, g ? g.name + " · " + (g.zweck || "") : "");
    }, function (h) { location.href = link(h.t.object.userData.geb); });
  }

  function gebaeude() {
    var id = new URLSearchParams(location.search).get("id");
    var g = D.gebaeude.filter(function (x) { return x.id === id; })[0];
    if (!g || !g.modell) { $("laden").textContent = "Gebäude „" + (id || "") + "“ hat kein Blockmodell."; return; }
    document.title = g.name;
    $("name").textContent = g.name;
    $("zweck").textContent = g.zweck || "";
    var st = $("status"); st.textContent = g.status || ""; if (g.status === "gebaut") st.classList.add("ok");

    var sz = C.baueSzene($("viewport")), halter = C.drehGruppe(g.drehung), obj = null, maxY = 0;
    sz.scene.add(halter);
    g.modell.bloecke.forEach(function (b) { if (b[1] > maxY) maxY = b[1]; });
    var sl = $("schnitt"); sl.max = maxY; sl.value = maxY;
    function schnitt(y) {
      if (obj) halter.remove(obj.gruppe);
      obj = C.baueModell(g.modell, { maxY: y });
      halter.add(obj.gruppe);
      $("schnittWert").textContent = y >= maxY ? "alles" : "y " + y;
      sz.neu();
    }
    sl.addEventListener("input", function () { schnitt(+sl.value); });
    function reset() { var b = C.weltBox(halter, g.modell); C.blickeAuf(sz, [b.min.x, 0, b.min.z], [b.max.x, b.max.y * 0.6, b.max.z]); }
    $("reset").addEventListener("click", reset);
    schnitt(maxY); reset();
    $("laden").hidden = true;

    hover(sz, function () { return obj ? obj.pickbar : []; }, function (h) {
      if (!h) { zeigeTip(null); return; }
      var b = obj.gibBlock(h.t.object, h.t.instanceId);
      zeigeTip(h, b.sorte.name + " · " + b.x + ", " + b.y + ", " + b.z);
    });
  }

  /* erst zeichnen, wenn der Texturatlas geladen ist (ohne Atlas: Farben) */
  window.Ansicht = {
    map: function () { C.bereit.then(map); },
    gebaeude: function () { C.bereit.then(gebaeude); }
  };
})();
