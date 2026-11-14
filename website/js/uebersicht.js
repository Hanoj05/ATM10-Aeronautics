/* Übersicht: oben der Campus in 3D als Bühne (dreht sich langsam), darunter eine Karte pro Gebäude. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("uebersicht");

  C.ladeJSON("campus/campus.json").then(function (campus) {
    if (campus.welt) $("welt-text").textContent = "Unser Campus in " + campus.welt + ". Fahr mit der Maus über ein Gebäude, ein Klick öffnet es.";
    return Promise.all(campus.gebaeude.map(function (g) {
      if (!g.ordner) return Promise.resolve({ g: g });
      return C.ladeGebaeude(g.id).then(function (d) { d.g = g; return d; }).catch(function () { return { g: g }; });
    }));
  }).then(function (liste) {
    karten(liste);
    zahlen(liste);
    if (window.THREE) C.bereit.then(function () { buehne(liste); });
    else $("loading").textContent = "3D-Ansicht nicht verfügbar.";
  }).catch(function (e) { $("karten").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });

  function link(g, tab) { return "gebaeude.html?id=" + encodeURIComponent(g.id) + "#" + (tab || "ansicht"); }

  function zahlen(liste) {
    var gebaut = 0, teile = 0, bloecke = 0;
    liste.forEach(function (d) {
      if (d.g.status === "gebaut") gebaut++;
      if (d.konfig) teile += d.konfig.teile.length;
      if (d.modell) bloecke += d.modell.bloecke.length;
    });
    function z(wert, text) { return "<div class='hero-zahl'><b data-zahl='" + wert + "'>0</b><span>" + esc(text) + "</span></div>"; }
    $("zahlen").innerHTML = z(liste.length, "Gebäude") + z(gebaut, "fertig") + z(teile, "Teile") + z(bloecke, "Blöcke");
    /* hochzählen */
    [].forEach.call($("zahlen").querySelectorAll("b"), function (b, i) {
      var ziel = +b.getAttribute("data-zahl"), t0 = null;
      function schritt(t) {
        if (t0 === null) t0 = t + 350 + i * 90;
        var p = Math.max(0, Math.min(1, (t - t0) / 1100)), e = 1 - Math.pow(1 - p, 4);
        b.textContent = Math.round(ziel * e).toLocaleString("de-DE");
        if (p < 1) requestAnimationFrame(schritt);
      }
      requestAnimationFrame(schritt);
    });
  }

  function karten(liste) {
    var h = "";
    liste.forEach(function (d) {
      var g = d.g, geb = d.geb;
      h += "<article class='box gebkarte'><div><h3>" + esc(g.name) + "</h3><p class='note' style='margin:2px 0 0'>" + esc((geb && geb.zweck) || g.zweck || "") + "</p></div>";
      h += "<div><span class='chip" + (g.status === "gebaut" ? " ok" : "") + "'>" + esc(g.status || "") + "</span></div>";
      if (geb) {
        var teile = d.konfig.teile.length, nodes = 0;
        d.konfig.teile.forEach(function (t) { (t.nodes || []).forEach(function (n) { nodes += n.anzahl || 1; }); });
        h += "<div class='kz'>";
        if (geb.masse && geb.masse.breite) h += "<span>Größe <b>" + geb.masse.breite + " × " + geb.masse.tiefe + "</b></span>";
        h += "<span>Teile <b>" + teile + "</b></span><span>Nodes <b>" + nodes + "</b></span>";
        h += "<span>P0 <b>" + (g.position ? g.position.join(", ") : "fehlt") + "</b></span></div>";
        h += "<div class='links'><a href='" + link(g, "ansicht") + "'>3D-Ansicht</a><a href='" + link(g, "konfig") + "'>Konfiguration</a>" + (geb.dateien && geb.dateien.bauplan ? "<a href='" + link(g, "bauplan") + "'>Bauplan</a>" : "") + "</div>";
      } else {
        h += "<p class='note'>Noch kein Ordner angelegt.</p>";
      }
      h += "</article>";
    });
    $("karten").innerHTML = h;
  }

  /* Die Bühne: durchsichtiger Renderer über dem Farbverlauf, Kamera dreht langsam um den Campus */
  function buehne(liste) {
    var hero = $("hero"), tooltip = $("tooltip");
    var sz = C.baueSzene(hero, { durchsichtig: true });
    hero.insertBefore(sz.renderer.domElement, hero.firstChild);
    var campus = C.baueCampus(sz, liste, { gitterDeckkraft: 0.14 });
    if (!campus.anzahl) { $("loading").textContent = "Noch kein Gebäude mit Blockmodell."; return; }
    $("loading").hidden = true;
    var g = campus.gesamt, st = sz.steuerung;
    C.blickeAuf(sz, g.min, [g.max[0], g.max[1] * 0.4, g.max[2]]);
    /* von etwas weiter oben und weiter weg, Mitte leicht nach rechts, damit die Glaskarte links unten nichts verdeckt */
    var t = st.target; sz.kamera.position.sub(t).multiplyScalar(0.62).add(t);
    /* Bild nach rechts schieben, damit die Glaskarte links den Campus nicht verdeckt */
    function versatz() {
      var w = hero.clientWidth, h = hero.clientHeight;
      if (w > 900) sz.kamera.setViewOffset(w, h, -w * 0.17, h * 0.04, w, h); else sz.kamera.clearViewOffset();
      sz.neu();
    }
    window.addEventListener("resize", versatz); versatz();
    st.enableZoom = false;          /* Mausrad scrollt die Seite, nicht die Kamera */
    st.enablePan = false;
    st.autoRotate = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    st.autoRotateSpeed = 0.55;
    st.update();

    /* sanft hereinfahren */
    var ziel = sz.kamera.position.clone(), start = ziel.clone().sub(t).multiplyScalar(1.45).add(t), t0 = performance.now();
    sz.kamera.position.copy(start);
    (function fahrt(jetzt) {
      var p = Math.min(1, (jetzt - t0) / 1800), e = 1 - Math.pow(1 - p, 4);
      if (p < 1 && !st.anfasst) { sz.kamera.position.lerpVectors(start, ziel, e); st.update(); sz.neu(); requestAnimationFrame(fahrt); }
    })(t0);

    /* Nach dem Loslassen nach ein paar Sekunden wieder weiterdrehen */
    var pause = null;
    st.addEventListener("start", function () { st.anfasst = true; st.autoRotate = false; clearTimeout(pause); });
    st.addEventListener("end", function () { pause = setTimeout(function () { st.autoRotate = true; }, 4000); });
    /* nur drehen, solange die Bühne zu sehen ist */
    if ("IntersectionObserver" in window) new IntersectionObserver(function (e) {
      if (!st.anfasst) st.autoRotate = e[0].isIntersecting;
    }).observe(hero);

    var ray = new THREE.Raycaster(), maus = new THREE.Vector2(), aktiv = null, rahmen = null, runter = null;
    var dom = sz.renderer.domElement;
    function markiere(e) {
      if (aktiv === e) return;
      aktiv = e;
      if (rahmen) { sz.scene.remove(rahmen); rahmen = null; }
      if (e) { rahmen = C.rahmen(e.box[0], e.box[1], C.cssVar("--honey") || "#e08a0c", 1); sz.scene.add(rahmen); }
      dom.classList.toggle("hovering", !!e);
      sz.neu();
    }
    dom.addEventListener("pointermove", function (ev) {
      var r = dom.getBoundingClientRect();
      maus.x = ((ev.clientX - r.left) / r.width) * 2 - 1;
      maus.y = -((ev.clientY - r.top) / r.height) * 2 + 1;
      ray.setFromCamera(maus, sz.kamera);
      var tr = ray.intersectObjects(campus.pick, false)[0];
      var e = tr ? tr.object.userData.eintrag : null;
      markiere(e);
      if (!e) { tooltip.hidden = true; return; }
      tooltip.textContent = e.g.name + " · " + (e.g.status || "");
      tooltip.style.left = (ev.clientX - r.left) + "px"; tooltip.style.top = (ev.clientY - r.top) + "px";
      tooltip.hidden = false;
    });
    dom.addEventListener("pointerleave", function () { markiere(null); tooltip.hidden = true; });
    dom.addEventListener("pointerdown", function (ev) { runter = [ev.clientX, ev.clientY]; });
    dom.addEventListener("pointerup", function (ev) {
      if (!runter || Math.hypot(ev.clientX - runter[0], ev.clientY - runter[1]) > 4 || !aktiv) return;
      location.href = link(aktiv.g);
    });
  }
})();
