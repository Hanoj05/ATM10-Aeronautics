/* Campus-Seite: alle Gebäude an ihrer Weltposition, Klick öffnet die Gebäudeseite. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  var viewport = $("viewport"), tooltip = $("tooltip");
  var eintraege = [];
  C.navi("map");

  C.ladeJSON("campus/campus.json").then(function (campus) {
    if (campus.welt) $("welt").textContent = campus.welt;
    return Promise.all(campus.gebaeude.map(function (g) {
      if (!g.ordner) return Promise.resolve({ g: g });
      return Promise.all([
        C.ladeJSON(g.ordner + "/gebaeude.json").catch(function () { return null; }),
        C.ladeJSON(g.ordner + "/modell.json").catch(function () { return null; })
      ]).then(function (r) { return { g: g, geb: r[0], modell: r[1] }; });
    }));
  }).then(function (liste) {
    eintraege = liste;
    zeigeListe();
    return C.bereit;
  }).then(function () {
    starte3D();
  }).catch(function (e) { $("loading").textContent = "Fehler: " + e.message; });

  function link(e) { return "gebaeude.html?id=" + encodeURIComponent(e.g.id) + "#ansicht"; }

  function zeigeListe() {
    var h = "", ohnePos = 0;
    eintraege.forEach(function (e, i) {
      var text = "<strong>" + esc(e.g.name) + "</strong><span>" + esc(e.g.zweck || "") + " · " + esc(e.g.status || "") + "</span>";
      if (e.g.ordner) h += "<a href='" + link(e) + "' data-i='" + i + "'>" + text + "</a>";
      else h += "<div class='item'>" + text + "</div>";
      if (e.modell && !e.g.position) ohnePos++;
    });
    $("liste").innerHTML = h;
    if (ohnePos) $("hinweis").textContent = "Bei " + ohnePos + " Gebäude fehlt noch die Weltposition in campus/campus.json. Es steht deshalb vorläufig am Nullpunkt.";
  }

  function starte3D() {
    var sz = C.baueSzene(viewport), pick = [], gesamt = { min: [Infinity, 0, Infinity], max: [-Infinity, 10, -Infinity] };
    var mitModell = eintraege.filter(function (e) { return e.modell; });
    var basis = null;
    mitModell.forEach(function (e) { if (e.g.position && !basis) basis = e.g.position; });
    /* Gebäude ohne Weltposition kommen rechts neben die eingetragenen */
    var reserve = 0;
    mitModell.forEach(function (e) {
      if (!e.g.position || !basis || !e.geb || !e.geb.masse) return;
      reserve = Math.max(reserve, e.g.position[0] - basis[0] + Math.max(e.geb.masse.breite || 0, e.geb.masse.tiefe || 0) + 20);
    });
    mitModell.forEach(function (e) {
      var vs;
      if (e.g.position && basis) vs = [e.g.position[0] - basis[0], e.g.position[1] - basis[1], e.g.position[2] - basis[2]];
      else { vs = [reserve, 0, 0]; reserve += (e.geb && e.geb.masse && e.geb.masse.breite || 40) + 20; }
      var halter = C.drehGruppe(e.g.drehung);
      halter.position.x += vs[0]; halter.position.y += vs[1]; halter.position.z += vs[2];
      var m = C.baueModell(e.modell);
      halter.add(m.gruppe);
      m.pickbar.forEach(function (p) { p.userData.eintrag = e; pick.push(p); });
      sz.scene.add(halter);
      var b3 = C.weltBox(halter, e.modell);
      e.box = [[b3.min.x, b3.min.y, b3.min.z], [b3.max.x, b3.max.y, b3.max.z]];
      for (var a = 0; a < 3; a++) { gesamt.min[a] = Math.min(gesamt.min[a], e.box[0][a]); gesamt.max[a] = Math.max(gesamt.max[a], e.box[1][a]); }
    });
    /* Boden */
    var spanne = Math.max(200, (gesamt.max[0] - gesamt.min[0]) * 3, (gesamt.max[2] - gesamt.min[2]) * 3);
    var gitter = new THREE.GridHelper(spanne, Math.round(spanne / 8), 0x9a978d, 0xb9b6ad);
    gitter.position.set((gesamt.min[0] + gesamt.max[0]) / 2, -0.01, (gesamt.min[2] + gesamt.max[2]) / 2);
    gitter.material.transparent = true; gitter.material.opacity = 0.45;
    sz.scene.add(gitter);

    function ansicht() {
      C.blickeAuf(sz, gesamt.min, [gesamt.max[0], gesamt.max[1] * 0.4, gesamt.max[2]]);
      /* etwas weiter weg, damit alle Gebäude ganz ins Bild passen */
      var t = sz.steuerung.target; sz.kamera.position.sub(t).multiplyScalar(1.3).add(t);
      sz.steuerung.update(); sz.neu();
    }
    $("ansicht").addEventListener("click", ansicht);
    ansicht();
    $("loading").hidden = !!mitModell.length;
    if (!mitModell.length) $("loading").textContent = "Noch kein Gebäude mit Blockmodell.";

    var ray = new THREE.Raycaster(), maus = new THREE.Vector2(), aktiv = null, rahmen = null, runter = null;
    function markiere(e) {
      if (aktiv === e) return;
      aktiv = e;
      if (rahmen) { sz.scene.remove(rahmen); rahmen = null; }
      if (e) { rahmen = C.rahmen(e.box[0], e.box[1], C.cssVar("--honey") || "#d9840b", 1); sz.scene.add(rahmen); }
      document.querySelectorAll("#liste a").forEach(function (a) { a.classList.toggle("hl", e && eintraege[+a.getAttribute("data-i")] === e); });
      sz.renderer.domElement.classList.toggle("hovering", !!e);
      sz.neu();
    }
    sz.renderer.domElement.addEventListener("pointermove", function (ev) {
      var r = sz.renderer.domElement.getBoundingClientRect();
      maus.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
      maus.y = -((ev.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(maus, sz.kamera);
      var t = ray.intersectObjects(pick, false)[0];
      var e = t ? t.object.userData.eintrag : null;
      markiere(e);
      if (!e) { tooltip.hidden = true; return; }
      tooltip.textContent = e.g.name + " · " + (e.g.zweck || "") + " · " + (e.g.status || "");
      var vr = viewport.getBoundingClientRect();
      tooltip.style.left = (ev.clientX - vr.left) + "px"; tooltip.style.top = (ev.clientY - vr.top) + "px";
      tooltip.hidden = false;
    });
    sz.renderer.domElement.addEventListener("pointerleave", function () { markiere(null); tooltip.hidden = true; });
    sz.renderer.domElement.addEventListener("pointerdown", function (ev) { runter = [ev.clientX, ev.clientY]; });
    sz.renderer.domElement.addEventListener("pointerup", function (ev) {
      if (!runter || Math.hypot(ev.clientX - runter[0], ev.clientY - runter[1]) > 4 || !aktiv) return;
      location.href = link(aktiv);
    });
  }
})();
