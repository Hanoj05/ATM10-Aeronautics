/* Gemeinsame Bausteine: Daten laden und Blockmodelle mit three.js zeichnen. */
(function () {
  "use strict";

  var ROOT = "../";

  /* "no-cache": der Browser fragt jedes Mal nach, ob sich die Datei geändert hat.
   * python3 -m http.server schickt keine Cache-Regeln, sonst bleiben alte Daten hängen. */
  var FRISCH = { cache: "no-cache" };
  function ladeJSON(pfad) {
    return fetch(ROOT + pfad, FRISCH).then(function (r) {
      if (!r.ok) throw new Error(pfad + " nicht gefunden (" + r.status + ")");
      return r.json();
    });
  }
  function ladeText(pfad) {
    return fetch(ROOT + pfad, FRISCH).then(function (r) {
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

  /* --- Blocktexturen ---
   * texturen/texturen.json ordnet jeder Block-ID je Seite eine Kachel im Atlas zu
   * (erzeugt mit tools/hole-texturen.py). Die Offline-Ansicht bringt dieselben Daten
   * samt Atlas als data-URL in window.CAMPUS_TEXTUREN mit. Fehlt etwas, bleibt die Farbe. */
  var TEX = { daten: null, atlas: null };
  var bereit = new Promise(function (fertig) {
    function mitBild(d, url) {
      var img = new Image();
      img.onload = function () {
        var t = new THREE.Texture(img);
        t.magFilter = THREE.NearestFilter;            /* Pixel-Look */
        t.minFilter = THREE.NearestMipmapLinearFilter; /* weit weg ohne Flimmern */
        t.anisotropy = 8;
        t.needsUpdate = true;
        TEX.daten = d; TEX.atlas = t;
        fertig();
      };
      img.onerror = function () { fertig(); };
      img.src = url;
    }
    if (window.CAMPUS_TEXTUREN) { mitBild(window.CAMPUS_TEXTUREN, window.CAMPUS_TEXTUREN.atlasDaten); return; }
    fetch(ROOT + "texturen/texturen.json", FRISCH)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) { fertig(); return; }
        /* Atlas ebenfalls am Cache vorbei holen */
        return fetch(ROOT + "texturen/" + d.atlas, FRISCH)
          .then(function (r) { if (!r.ok) throw new Error("atlas"); return r.blob(); })
          .then(function (b) { mitBild(d, URL.createObjectURL(b)); });
      })
      .catch(function () { fertig(); });
  });

  /* Reihenfolge der Flächen in BoxGeometry: +x, -x, +y, -y, +z, -z */
  var BOX_SEITEN = ["east", "west", "up", "down", "south", "north"];
  function kachelUV(name) {
    var d = TEX.daten, t = d.texturen[name];
    if (!t) return null;
    var zelle = d.kachel + 2 * d.rand, w = d.groesse[0], h = d.groesse[1];
    var x = (t.nr % d.spalten) * zelle + d.rand, y = Math.floor(t.nr / d.spalten) * zelle + d.rand;
    return { u0: x / w, u1: (x + d.kachel) / w, v0: 1 - (y + d.kachel) / h, v1: 1 - y / h, alpha: t.alpha };
  }
  /* Kacheln je Seite für eine Palettensorte, oder null ohne Textur */
  function texturVon(p) {
    if (!TEX.daten || !p.id || p.id.indexOf("platzhalter:") === 0) return null;
    var b = TEX.daten.bloecke[p.id];
    if (!b) return null;
    var k = {}, alpha = "voll";
    for (var i = 0; i < BOX_SEITEN.length; i++) {
      var uv = kachelUV(b[BOX_SEITEN[i]]);
      if (!uv) return null;
      k[BOX_SEITEN[i]] = uv;
      if (uv.alpha === "halb" || (uv.alpha === "loch" && alpha === "voll")) alpha = uv.alpha;
    }
    k.alpha = alpha;
    return k;
  }
  /* Würfel, dessen sechs Flächen auf die Kacheln im Atlas zeigen */
  function texturWuerfel(basis, k) {
    var g = basis.clone(), uv = g.attributes.uv;
    for (var f = 0; f < 6; f++) {
      var t = k[BOX_SEITEN[f]];
      for (var v = f * 4; v < f * 4 + 4; v++) {
        uv.setXY(v, t.u0 + uv.getX(v) * (t.u1 - t.u0), t.v0 + uv.getY(v) * (t.v1 - t.v0));
      }
    }
    return g;
  }
  /* Zwei gekreuzte Flächen wie bei Blumen und Ketten im Spiel, Mitte auf Höhe 0 */
  function kreuz(t) {
    var pos = [], uv = [], nor = [], idx = [], s = 0.45, h = 0.5;
    [[1, 1], [1, -1]].forEach(function (r, i) {
      var dx = s * r[0], dz = s * r[1], n = [r[1] * 0.7071, 0, -r[0] * 0.7071];
      pos.push(-dx, -h, -dz, dx, -h, dz, dx, h, dz, -dx, h, -dz);
      uv.push(t.u0, t.v0, t.u1, t.v0, t.u1, t.v1, t.u0, t.v1);
      for (var j = 0; j < 4; j++) nor.push(n[0], n[1], n[2]);
      idx.push(i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3);
    });
    var g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx);
    return g;
  }

  /* Geometrie und Material je Sorte nur einmal bauen, der Schnitt-Regler baut sonst ständig neu. */
  var cache = {};
  function teileFuer(p, wuerfel, klein) {
    var k = texturVon(p), schluessel = p.id + "|" + (p.klein ? 1 : 0) + "|" + (p.transparent ? 1 : 0) + "|" + p.farbe + "|" + (k ? 1 : 0);
    if (cache[schluessel]) return cache[schluessel];
    var r;
    if (!k || p.form === "kabel") {
      /* ohne Textur wie bisher: Farbe; Kabel bleiben auch einfarbig, ihre Texturen sind UV-Bögen */
      r = {
        geo: p.klein ? klein : wuerfel, mitte: p.klein ? 0.25 : 0.5, textur: false, pickbar: !p.transparent,
        mat: p.transparent
          ? new THREE.MeshLambertMaterial({ color: p.farbe, transparent: true, opacity: p.id === "glass" ? 0.32 : 0.75, depthWrite: false })
          : new THREE.MeshLambertMaterial({ color: 0xffffff })
      };
    } else if (p.klein && k.alpha !== "voll") {
      /* Blumen, Kette: gekreuzte Flächen mit ausgestanzter Textur */
      r = { geo: kreuz(k.north), mitte: 0.5, textur: true, pickbar: true,
            mat: new THREE.MeshLambertMaterial({ map: TEX.atlas, alphaTest: 0.5, side: THREE.DoubleSide }) };
    } else {
      var opt = { map: TEX.atlas };
      if (k.alpha === "halb") { opt.transparent = true; opt.depthWrite = false; }   /* Stained Glass, Water */
      else if (k.alpha === "loch") opt.alphaTest = 0.5;                              /* Glass, Leaves */
      r = { geo: texturWuerfel(p.klein ? klein : wuerfel, k), mitte: p.klein ? 0.25 : 0.5, textur: true,
            pickbar: !p.transparent, blend: k.alpha === "halb", mat: new THREE.MeshLambertMaterial(opt) };
    }
    cache[schluessel] = r;
    return r;
  }

  /**
   * Baut ein Blockmodell als Gruppe aus InstancedMeshes, eins pro Palettensorte.
   * modell: { palette: [...], bloecke: [[x,y,z,i], ...] }
   * opt.maxY: nur Blöcke bis zu dieser Höhe; opt.versatz: [x,y,z]
   * Rückgabe: { gruppe, pickbar: [mesh], gibBlock(mesh, instanceId) }
   * Texturen werden genutzt, sobald Campus.bereit erfüllt ist; vorher kommt die Farbe.
   */
  function baueModell(modell, opt) {
    opt = opt || {};
    var maxY = opt.maxY == null ? Infinity : opt.maxY;
    var vs = opt.versatz || [0, 0, 0];
    var gruppe = new THREE.Group();
    var proSorte = modell.palette.map(function () { return []; });
    modell.bloecke.forEach(function (b) { if (b[1] <= maxY) proSorte[b[3]].push(b); });

    var wuerfel = WUERFEL, klein = KLEIN;
    var pickbar = [];
    var m4 = new THREE.Matrix4(), farbe = new THREE.Color();

    modell.palette.forEach(function (p, i) {
      var liste = proSorte[i];
      if (!liste.length) return;
      var t = teileFuer(p, wuerfel, klein);
      if (p.form === "kabel") { gruppe.add(baueKabel(p, liste, t.mat, wuerfel, vs, pickbar)); return; }
      var mesh = new THREE.InstancedMesh(t.geo, t.mat, liste.length);
      var basis = new THREE.Color(p.farbe), mitFarbe = t.textur ? !t.blend : !p.transparent;
      liste.forEach(function (b, j) {
        m4.makeTranslation(b[0] + vs[0] + 0.5, b[1] + vs[1] + t.mitte, b[2] + vs[2] + 0.5);
        mesh.setMatrixAt(j, m4);
        if (mitFarbe) {
          var r = rauschen(b[0], b[1], b[2]);
          /* mit Textur nur ein Hauch Helligkeit, damit große Flächen nicht wie Tapete wirken */
          if (t.textur) farbe.setScalar(0.97 + r * 0.6);
          else farbe.copy(basis).offsetHSL(0, 0, r);
          mesh.setColorAt(j, farbe);
        }
      });
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
      mesh.userData = { sorte: p, bloecke: liste };
      if (t.blend || (!t.textur && p.transparent)) mesh.renderOrder = 2;
      if (t.pickbar) pickbar.push(mesh);
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
  var WUERFEL = new THREE.BoxGeometry(1, 1, 1);
  var KLEIN = new THREE.BoxGeometry(0.4, 0.5, 0.4);

  /* AE2-Kabel als Strang: Mittelstück plus ein Arm pro Verbindung.
   * Block = [x, y, z, sorte, maske], Bits der maske: unten, oben, Nord, Süd, West, Ost. */
  var KABEL_RICHTUNG = [[0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1], [-1, 0, 0], [1, 0, 0]];
  function baueKabel(p, liste, mat, wuerfel, vs, pickbar) {
    var d = p.dicke || 0.3, arm = (1 - d) / 2, weg = d / 2 + arm / 2, stuecke = [];
    liste.forEach(function (b) {
      var c = [b[0] + vs[0] + 0.5, b[1] + vs[1] + 0.5, b[2] + vs[2] + 0.5], m = b[4] || 0;
      stuecke.push({ b: b, pos: c, gr: [d, d, d] });
      KABEL_RICHTUNG.forEach(function (r, k) {
        if (!(m & (1 << k))) return;
        stuecke.push({ b: b, pos: [c[0] + r[0] * weg, c[1] + r[1] * weg, c[2] + r[2] * weg], gr: [r[0] ? arm : d, r[1] ? arm : d, r[2] ? arm : d] });
      });
    });
    var mesh = new THREE.InstancedMesh(wuerfel, mat, stuecke.length);
    var m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), v = new THREE.Vector3(), s = new THREE.Vector3(), farbe = new THREE.Color(p.farbe);
    stuecke.forEach(function (t, j) {
      m4.compose(v.set(t.pos[0], t.pos[1], t.pos[2]), q, s.set(t.gr[0], t.gr[1], t.gr[2]));
      mesh.setMatrixAt(j, m4);
      mesh.setColorAt(j, farbe);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.userData = { sorte: p, bloecke: stuecke.map(function (t) { return t.b; }) };
    pickbar.push(mesh);
    return mesh;
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

  /* Navigation oben auf jeder Seite. aktiv: "uebersicht", "map", "technik", "roadmap" oder eine Gebäude-ID */
  function navi(aktiv) {
    var nav = document.getElementById("nav");
    if (!nav) return;
    function link(href, text, an) { return "<a href='" + href + "'" + (an ? " aria-current='page'" : "") + ">" + esc(text) + "</a>"; }
    nav.innerHTML = link("index.html", "Übersicht", aktiv === "uebersicht") + link("map.html", "Map", aktiv === "map") + link("technik.html", "Technik", aktiv === "technik") + link("roadmap.html", "Roadmap", aktiv === "roadmap");
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
        opt(d.konfigDaten === undefined ? "konfig.json" : d.konfigDaten)
      ]).then(function (r) {
        return { id: id, ordner: ordner, geb: geb, modell: r[0], konfig: r[1] || { netzwerke: [], teile: [] } };
      });
    });
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]; }); }

  window.Campus = { bereit: bereit, ladeJSON: ladeJSON, ladeText: ladeText, baueModell: baueModell, baueSzene: baueSzene, blickeAuf: blickeAuf, rahmen: rahmen, cssVar: cssVar, esc: esc, drehGruppe: drehGruppe, weltVon: weltVon, weltBox: weltBox, navi: navi, ladeGebaeude: ladeGebaeude };
})();
