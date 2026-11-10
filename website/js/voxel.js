/* Gemeinsame Bausteine: Daten laden und Blockmodelle mit three.js zeichnen. */
(function () {
  "use strict";

  var ROOT = "../";

  function ladeJSON(pfad) {
    return fetch(ROOT + pfad).then(function (r) {
      if (!r.ok) throw new Error(pfad + " nicht gefunden (" + r.status + ")");
      return r.json();
    });
  }
  function ladeText(pfad) {
    return fetch(ROOT + pfad).then(function (r) {
      if (!r.ok) throw new Error(pfad + " nicht gefunden (" + r.status + ")");
      return r.text();
    });
  }
  function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }

  /* Kleiner Zufall pro Block, damit Flächen nicht flach wirken (immer gleich für denselben Block). */
  function rauschen(x, y, z) {
    var n = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719) * 43758.5453;
    return (n - Math.floor(n)) * 0.08 - 0.04;
  }

  /**
   * Baut ein Blockmodell als Gruppe aus InstancedMeshes.
   * modell: { palette: [...], bloecke: [[x,y,z,i], ...] }
   * opt.maxY: nur Blöcke bis zu dieser Höhe; opt.versatz: [x,y,z]
   * Rückgabe: { gruppe, pickbar: [mesh], gibBlock(mesh, instanceId) }
   */
  function baueModell(modell, opt) {
    opt = opt || {};
    var maxY = opt.maxY == null ? Infinity : opt.maxY;
    var vs = opt.versatz || [0, 0, 0];
    var gruppe = new THREE.Group();
    var proSorte = modell.palette.map(function () { return []; });
    modell.bloecke.forEach(function (b) { if (b[1] <= maxY) proSorte[b[3]].push(b); });

    var wuerfel = new THREE.BoxGeometry(1, 1, 1);
    var klein = new THREE.BoxGeometry(0.4, 0.5, 0.4);
    var pickbar = [];
    var m4 = new THREE.Matrix4(), farbe = new THREE.Color();

    modell.palette.forEach(function (p, i) {
      var liste = proSorte[i];
      if (!liste.length) return;
      var mat = p.transparent
        ? new THREE.MeshLambertMaterial({ color: p.farbe, transparent: true, opacity: p.id === "glass" ? 0.32 : 0.75, depthWrite: false })
        : new THREE.MeshLambertMaterial({ color: 0xffffff });
      var mesh = new THREE.InstancedMesh(p.klein ? klein : wuerfel, mat, liste.length);
      var basis = new THREE.Color(p.farbe);
      liste.forEach(function (b, j) {
        m4.makeTranslation(b[0] + vs[0] + 0.5, b[1] + vs[1] + (p.klein ? 0.25 : 0.5), b[2] + vs[2] + 0.5);
        mesh.setMatrixAt(j, m4);
        if (!p.transparent) {
          var r = rauschen(b[0], b[1], b[2]);
          farbe.copy(basis).offsetHSL(0, 0, r);
          mesh.setColorAt(j, farbe);
        }
      });
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
      mesh.userData = { sorte: p, bloecke: liste };
      if (p.transparent) mesh.renderOrder = 2;
      else pickbar.push(mesh);
      gruppe.add(mesh);
    });
    return {
      gruppe: gruppe,
      pickbar: pickbar,
      gibBlock: function (mesh, id) {
        var b = mesh.userData.bloecke[id];
        return { x: b[0], y: b[1], z: b[2], sorte: mesh.userData.sorte };
      }
    };
  }

  /** Szene mit Licht, Kamera und Steuerung in einem Container. */
  function baueSzene(container) {
    var renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    container.appendChild(renderer.domElement);
    var scene = new THREE.Scene();
    var kamera = new THREE.PerspectiveCamera(40, 1, 0.5, 4000);
    var steuerung = new THREE.OrbitControls(kamera, renderer.domElement);
    steuerung.enableDamping = true;
    steuerung.dampingFactor = 0.12;
    steuerung.maxPolarAngle = Math.PI * 0.49;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8678, 0.75));
    var sonne = new THREE.DirectionalLight(0xffffff, 0.65);
    sonne.position.set(0.6, 1, 0.35);
    scene.add(sonne);
    var sonne2 = new THREE.DirectionalLight(0xffffff, 0.2);
    sonne2.position.set(-0.5, 0.4, -0.8);
    scene.add(sonne2);

    function hintergrund() { scene.background = new THREE.Color(cssVar("--scene") || "#dedcd5"); }
    hintergrund();
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      if (mq.addEventListener) mq.addEventListener("change", function () { hintergrund(); neu(); });
    }

    var brauchtRender = true;
    function neu() { brauchtRender = true; }
    steuerung.addEventListener("change", neu);

    function groesse() {
      var w = container.clientWidth, h = container.clientHeight;
      renderer.setSize(w, h, false);
      renderer.domElement.style.width = w + "px";
      renderer.domElement.style.height = h + "px";
      kamera.aspect = w / Math.max(1, h);
      kamera.updateProjectionMatrix();
      neu();
    }
    window.addEventListener("resize", groesse);
    groesse();

    (function loop() {
      requestAnimationFrame(loop);
      if (steuerung.update()) brauchtRender = true;
      if (brauchtRender) { renderer.render(scene, kamera); brauchtRender = false; }
    })();

    return { renderer: renderer, scene: scene, kamera: kamera, steuerung: steuerung, neu: neu, groesse: groesse };
  }

  /** Kamera so setzen, dass ein Quader [min, max] gut im Bild ist. */
  function blickeAuf(sz, min, max) {
    var c = new THREE.Vector3((min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2);
    var r = Math.max(max[0] - min[0], max[2] - min[2], (max[1] - min[1]) * 1.5);
    sz.steuerung.target.copy(c);
    sz.kamera.position.set(c.x + r * 0.75, c.y + r * 0.8, c.z + r * 0.95);
    sz.steuerung.update();
    sz.neu();
  }

  /** Rahmen um einen Quader, für Hover und Auswahl. */
  function rahmen(min, max, farbe, dicke) {
    var g = new THREE.BoxGeometry(max[0] - min[0] + 0.12, max[1] - min[1] + 0.12, max[2] - min[2] + 0.12);
    var linien = new THREE.LineSegments(new THREE.EdgesGeometry(g), new THREE.LineBasicMaterial({ color: farbe, depthTest: false, transparent: true, opacity: dicke || 1 }));
    linien.position.set((min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2);
    linien.renderOrder = 10;
    var huelle = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: farbe, transparent: true, opacity: 0.08, depthWrite: false }));
    huelle.position.copy(linien.position);
    huelle.renderOrder = 9;
    var gr = new THREE.Group(); gr.add(huelle); gr.add(linien);
    return gr;
  }

  /* Gebäude gedreht gebaut? drehung in Grad im Uhrzeigersinn (90 = Plan-Norden zeigt nach Osten). */
  var KORREKTUR = { 0: [0, 0], 90: [1, 0], 180: [1, 1], 270: [0, 1] };
  function drehGruppe(drehung) {
    var d = ((drehung || 0) % 360 + 360) % 360, g = new THREE.Group();
    g.rotation.y = -d * Math.PI / 180;
    g.userData.korrektur = KORREKTUR[d] || [0, 0];
    g.position.set(g.userData.korrektur[0], 0, g.userData.korrektur[1]);
    return g;
  }
  /* Umrandung eines Modells in Szenen-Koordinaten (InstancedMesh liefert in three r147 keine eigene). */
  function weltBox(halter, modell) {
    var mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    modell.bloecke.forEach(function (b) { for (var a = 0; a < 3; a++) { mn[a] = Math.min(mn[a], b[a]); mx[a] = Math.max(mx[a], b[a] + 1); } });
    halter.updateMatrixWorld(true);
    var box = new THREE.Box3();
    [mn[0], mx[0]].forEach(function (x) { [mn[1], mx[1]].forEach(function (y) { [mn[2], mx[2]].forEach(function (z) {
      box.expandByPoint(halter.localToWorld(new THREE.Vector3(x, y, z)));
    }); }); });
    return box;
  }
  /* Plan-Koordinate eines Blocks in Weltkoordinate umrechnen. */
  function weltVon(p0, drehung, x, y, z) {
    if (!p0) return null;
    var d = ((drehung || 0) % 360 + 360) % 360, dx = x, dz = z;
    if (d === 90) { dx = -z; dz = x; } else if (d === 180) { dx = -x; dz = -z; } else if (d === 270) { dx = z; dz = -x; }
    return [p0[0] + dx, p0[1] + y, p0[2] + dz];
  }

  /* Navigation oben auf jeder Seite. aktiv: "uebersicht", "map" oder eine Gebäude-ID */
  function navi(aktiv) {
    var nav = document.getElementById("nav");
    if (!nav) return;
    function link(href, text, an) { return "<a href='" + href + "'" + (an ? " aria-current='page'" : "") + ">" + esc(text) + "</a>"; }
    nav.innerHTML = link("index.html", "Übersicht", aktiv === "uebersicht") + link("map.html", "Map", aktiv === "map");
    ladeJSON("campus/campus.json").then(function (c) {
      var h = "";
      c.gebaeude.forEach(function (g) { if (g.ordner) h += link("gebaeude.html?id=" + encodeURIComponent(g.id), g.name, aktiv === g.id); });
      if (h) nav.insertAdjacentHTML("beforeend", "<span class='sep' aria-hidden='true'></span>" + h);
    }).catch(function () {});
  }

  /* Alle Daten eines Gebäudes laden. Fehlende Dateien werden zu null. */
  function ladeGebaeude(id) {
    var ordner = "gebaeude/" + id + "/";
    function opt(p) { return p ? ladeJSON(ordner + p).catch(function () { return null; }) : Promise.resolve(null); }
    return ladeJSON(ordner + "gebaeude.json").then(function (geb) {
      var d = geb.dateien || {};
      return Promise.all([
        opt(d.modell === undefined ? "modell.json" : d.modell),
        opt(d.konfigDaten === undefined ? "konfig.json" : d.konfigDaten),
        opt(d.einrichtungDaten === undefined ? "einrichtung.json" : d.einrichtungDaten)
      ]).then(function (r) {
        return { id: id, ordner: ordner, geb: geb, modell: r[0], konfig: r[1] || { netzwerke: [], teile: [] }, einr: r[2] || { teile: [] } };
      });
    });
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]; }); }

  window.Campus = { ladeJSON: ladeJSON, ladeText: ladeText, baueModell: baueModell, baueSzene: baueSzene, blickeAuf: blickeAuf, rahmen: rahmen, cssVar: cssVar, esc: esc, drehGruppe: drehGruppe, weltVon: weltVon, weltBox: weltBox, navi: navi, ladeGebaeude: ladeGebaeude };
})();
