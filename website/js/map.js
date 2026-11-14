/* Campus-Seite: alle Gebäude an ihrer Weltposition, Klick öffnet die Gebäudeseite.
 * map.html?zweig=NAME zeigt den Stand aus einem anderen Git-Branch (nur auf dem Server,
 * der Campus-Dienst liest die Dateien dort aus dem Branch). Gibt es campus/gelaende.json,
 * wird das Gelände drumherum mitgezeichnet. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  var viewport = $("viewport"), tooltip = $("tooltip");
  var eintraege = [], gelaende = null;
  var zweig = new URLSearchParams(location.search).get("zweig") || "";
  if (zweig === "main") zweig = "";
  C.navi("map");

  function lade(pfad) { return C.ladeJSON(pfad, zweig); }

  if (zweig) {
    var z = document.createElement("span");
    z.className = "zweig";
    z.textContent = "Branch: " + zweig;
    document.querySelector(".topbar").appendChild(z);
    document.title = "Campus-Map · " + zweig;
  }
  zeigeStandAuswahl();

  lade("campus/campus.json").then(function (campus) {
    if (campus.welt) $("welt").textContent = campus.welt;
    return Promise.all([
      Promise.all(campus.gebaeude.map(function (g) {
        if (!g.ordner) return Promise.resolve({ g: g });
        return Promise.all([
          lade(g.ordner + "/gebaeude.json").catch(function () { return null; }),
          lade(g.ordner + "/modell.json").catch(function () { return null; })
        ]).then(function (r) { return { g: g, geb: r[0], modell: r[1] }; });
      })),
      lade("campus/gelaende.json").catch(function () { return null; })
    ]);
  }).then(function (r) {
    eintraege = r[0];
    gelaende = r[1];
    zeigeListe();
    return C.bereit;
  }).then(function () {
    starte3D();
  }).catch(function (e) {
    $("loading").textContent = zweig ? "Den Branch „" + zweig + "“ konnte ich nicht laden: " + e.message : "Fehler: " + e.message;
  });

  /* Auswahlfeld „Stand“: nur, wenn der Campus-Dienst Branches liefert (lokal gibt es ihn nicht) */
  function zeigeStandAuswahl() {
    C.api("zweige").then(function (d) {
      var liste = (d && d.zweige) || [];
      if (zweig && !liste.some(function (b) { return b.name === zweig; })) liste.push({ name: zweig, fehlt: true });
      if (liste.length < 2 && !zweig) return;
      var sel = $("stand");
      sel.innerHTML = liste.map(function (b) {
        var text = b.name + (b.name === "main" ? " (aktuell)" : "") + (b.fehlt ? " (gibt es nicht)" : "");
        return "<option value='" + esc(b.name) + "'" + ((b.name === (zweig || "main")) ? " selected" : "") + ">" + esc(text) + "</option>";
      }).join("");
      sel.title = liste.filter(function (b) { return b.betreff; }).map(function (b) { return b.name + ": " + b.betreff; }).join("\n");
      sel.addEventListener("change", function () {
        var u = new URL(location.href);
        if (sel.value === "main") u.searchParams.delete("zweig"); else u.searchParams.set("zweig", sel.value);
        location.href = u.toString();
      });
      $("stand-feld").hidden = false;
    }).catch(function () { /* ohne Dienst kein Auswahlfeld */ });
  }

  function link(e) { return "gebaeude.html?id=" + encodeURIComponent(e.g.id) + "#ansicht"; }

  function zeigeListe() {
    var h = "", ohnePos = 0;
    eintraege.forEach(function (e, i) {
      var nichtAufKarte = e.g.karte === false;
      var text = "<strong>" + esc(e.g.name) + "</strong><span>" + esc(e.g.zweck || "") + " · " + esc(e.g.status || "")
        + (nichtAufKarte ? " · nicht auf der Map" : "") + "</span>";
      if (e.g.ordner) h += "<a href='" + link(e) + "' data-i='" + i + "'>" + text + "</a>";
      else h += "<div class='item'>" + text + "</div>";
      if (e.modell && !e.g.position && !nichtAufKarte) ohnePos++;
    });
    $("liste").innerHTML = h;
    var hinweise = [];
    if (ohnePos) hinweise.push("Bei " + ohnePos + " Gebäude fehlt noch die Weltposition in campus/campus.json. Es steht deshalb vorläufig am Nullpunkt.");
    if (zweig) hinweise.push("Du siehst den Stand aus dem Branch „" + zweig + "“. Die Gebäudeseiten zeigen weiter den Stand aus main.");
    $("hinweis").textContent = hinweise.join(" ");
  }

  function starte3D() {
    var sz = C.baueSzene(viewport);
    var campus = C.baueCampus(sz, eintraege, { gitter: !gelaende }), pick = campus.pick, gesamt = campus.gesamt;
    var mitModell = eintraege.filter(function (e) { return e.modell && e.g.karte !== false; });

    if (gelaende) {
      var gel = C.baueGelaende(gelaende, campus.basis);
      sz.scene.add(gel);
      $("gelaende-feld").hidden = false;
      $("gelaende-an").addEventListener("change", function () { gel.visible = this.checked; sz.neu(); });
      /* Kamera weiter weg erlauben, das Gelände ist größer als der Campus */
      sz.kamera.far = 8000; sz.kamera.updateProjectionMatrix();
    }

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
