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
        if (typeof THREE === "undefined") { fertig(); return; }
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
    if (typeof THREE === "undefined") { fertig(); return; }   /* Seite ohne 3D: Atlas gar nicht erst laden */
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
  /* Seiten ohne 3D (Übersicht, Technik, Team …) laden three.js nicht, dort bleiben die beiden leer */
  var MIT_3D = typeof THREE !== "undefined";
  var WUERFEL = MIT_3D ? new THREE.BoxGeometry(1, 1, 1) : null;
  var KLEIN = MIT_3D ? new THREE.BoxGeometry(0.4, 0.5, 0.4) : null;

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
  function baueSzene(container, opt) {
    opt = opt || {};
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: !!opt.durchsichtig });
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

    function hintergrund() { scene.background = opt.durchsichtig ? null : new THREE.Color(cssVar("--scene") || "#e9e7e0"); }
    hintergrund();
    /* Systemfarbe oder Schalter im Profilmenü geändert: Hintergrund nachziehen */
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      if (mq.addEventListener) mq.addEventListener("change", function () { hintergrund(); neu(); });
    }
    document.addEventListener("campus-thema", function () { hintergrund(); neu(); });

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

  /** Alle Gebäude an ihrer Weltposition in die Szene setzen (Map und Startseite).
   *  eintraege: [{ g, geb, modell }]. Gibt pickbare Meshes und die Gesamtgröße zurück, e.box wird gesetzt. */
  function baueCampus(sz, eintraege, opt) {
    opt = opt || {};
    var pick = [], gesamt = { min: [Infinity, 0, Infinity], max: [-Infinity, 10, -Infinity] };
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
      var halter = drehGruppe(e.g.drehung);
      halter.position.x += vs[0]; halter.position.y += vs[1]; halter.position.z += vs[2];
      var m = baueModell(e.modell);
      halter.add(m.gruppe);
      m.pickbar.forEach(function (p) { p.userData.eintrag = e; pick.push(p); });
      sz.scene.add(halter);
      var b3 = weltBox(halter, e.modell);
      e.box = [[b3.min.x, b3.min.y, b3.min.z], [b3.max.x, b3.max.y, b3.max.z]];
      for (var a = 0; a < 3; a++) { gesamt.min[a] = Math.min(gesamt.min[a], e.box[0][a]); gesamt.max[a] = Math.max(gesamt.max[a], e.box[1][a]); }
    });
    if (opt.gitter !== false && mitModell.length) {
      var spanne = Math.max(200, (gesamt.max[0] - gesamt.min[0]) * 3, (gesamt.max[2] - gesamt.min[2]) * 3);
      var gitter = new THREE.GridHelper(spanne, Math.round(spanne / 8), 0x9a978d, 0xb9b6ad);
      gitter.position.set((gesamt.min[0] + gesamt.max[0]) / 2, -0.01, (gesamt.min[2] + gesamt.max[2]) / 2);
      gitter.material.transparent = true; gitter.material.opacity = opt.gitterDeckkraft || 0.45;
      sz.scene.add(gitter);
    }
    return { pick: pick, gesamt: gesamt, anzahl: mitModell.length };
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

  /* --- Campus-Dienst (Anmeldung über Authentik, Speichern) ---
   * Gibt es nur auf dem Server. Lokal mit python3 -m http.server fehlt er, dann bleibt die
   * Seite einfach ohne Login-Teil. */
  function api(pfad, daten) {
    var opt = { credentials: "same-origin", cache: "no-store" };
    if (daten !== undefined) { opt.method = "POST"; opt.headers = { "Content-Type": "application/json" }; opt.body = JSON.stringify(daten); }
    return fetch(ROOT + "api/" + pfad, opt).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) { var e = new Error(j.fehler || "Der Dienst antwortet nicht (" + r.status + ")."); e.status = r.status; throw e; }
        return j;
      });
    });
  }
  var ichAnfrage = null;
  /* Wer ist eingeloggt? null ohne Dienst oder ohne Login. */
  function ich() {
    if (!ichAnfrage) ichAnfrage = api("ich").catch(function () { return null; });
    return ichAnfrage;
  }
  /* Rundes Bild mit Initialen in der Profilfarbe */
  function avatar(p, groesse) {
    var name = (p && (p.anzeigename || p.id)) || "?", teile = name.trim().split(/\s+/);
    var ini = (teile[0].charAt(0) + (teile.length > 1 ? teile[teile.length - 1].charAt(0) : "")).toUpperCase();
    return "<span class='avatar' style='--av:" + esc((p && p.farbe) || "#62645f") + (groesse ? ";--av-g:" + groesse + "px" : "") + "' aria-hidden='true'>" + esc(ini) + "</span>";
  }

  /* --- Hell / Dunkel ---
   * Gespeichert pro Browser in localStorage ("campus-thema": "hell" oder "dunkel", fehlt = wie das System).
   * Jede Seite setzt das schon im <head>, damit beim Laden nichts aufblitzt. */
  var THEMA_KEY = "campus-thema";
  function icon(pfad) { return "<svg viewBox='0 0 24 24' width='16' height='16' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>" + pfad + "</svg>"; }
  var ICON = {
    system: icon("<rect x='3' y='4' width='18' height='12' rx='2'/><path d='M8 20h8M12 16v4'/>"),
    hell: icon("<circle cx='12' cy='12' r='4'/><path d='M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4'/>"),
    dunkel: icon("<path d='M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z'/>")
  };
  var THEMEN = [["system", "System"], ["hell", "Hell"], ["dunkel", "Dunkel"]];
  function thema() {
    try { var t = localStorage.getItem(THEMA_KEY); return t === "hell" || t === "dunkel" ? t : "system"; } catch (e) { return "system"; }
  }
  function setzeThema(t) {
    try { if (t === "system") localStorage.removeItem(THEMA_KEY); else localStorage.setItem(THEMA_KEY, t); } catch (e) {}
    var html = document.documentElement;
    html.classList.add("thema-wechsel");
    if (t === "system") html.removeAttribute("data-theme"); else html.setAttribute("data-theme", t);
    clearTimeout(setzeThema.zeit);
    setzeThema.zeit = setTimeout(function () { html.classList.remove("thema-wechsel"); }, 400);
    document.querySelectorAll("[data-thema]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-thema") === t)); });
    document.querySelectorAll(".thema-knopf").forEach(function (k) { k.innerHTML = ICON[t]; });
    document.dispatchEvent(new CustomEvent("campus-thema", { detail: t }));
  }
  /* Drei Knöpfe System / Hell / Dunkel, überall einsetzbar (Profilmenü, Team-Seite) */
  function themaWahl() {
    var jetzt = thema();
    return "<div class='thema-wahl' role='group' aria-label='Darstellung'>" + THEMEN.map(function (t) {
      return "<button type='button' data-thema='" + t[0] + "' aria-pressed='" + (t[0] === jetzt) + "'>" + ICON[t[0]] + t[1] + "</button>";
    }).join("") + "</div>";
  }
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest("[data-thema]");
    if (b) setzeThema(b.getAttribute("data-thema"));
  }, true);   /* Capture: greift auch im Menü, das Klicks sonst abfängt */

  /* Aufklappmenü am Avatar (oder am Thema-Knopf ohne Login) */
  var alleMenues = [];
  function menueAn(knopf, menue, beimOeffnen) {
    function zu() { if (menue.hidden) return; menue.classList.add("geht"); knopf.setAttribute("aria-expanded", "false");
      setTimeout(function () { menue.hidden = true; menue.classList.remove("geht"); }, 160); }
    alleMenues.push(zu);
    knopf.addEventListener("click", function (ev) {
      ev.stopPropagation();
      if (!menue.hidden) return zu();
      alleMenues.forEach(function (f) { if (f !== zu) f(); });
      menue.hidden = false; menue.classList.remove("geht"); knopf.setAttribute("aria-expanded", "true");
      if (beimOeffnen) beimOeffnen();
    });
    menue.addEventListener("click", function (ev) { if (!ev.target.closest("a")) ev.stopPropagation(); });
    document.addEventListener("click", zu);
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !menue.hidden) { zu(); knopf.focus(); } });
  }

  /* --- Glocke: Benachrichtigungen vom Dienst (Kanban-Zuweisungen, Statuswechsel, Karten-Import) --- */
  var GLOCKE_SVG = "<svg viewBox='0 0 24 24' width='18' height='18' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9'/><path d='M10.3 21a1.94 1.94 0 0 0 3.4 0'/></svg>";
  function vorWann(iso) {
    var s = (Date.now() - Date.parse(iso)) / 1000;
    if (s < 60) return "gerade eben";
    if (s < 3600) return "vor " + Math.floor(s / 60) + " Min.";
    if (s < 86400) return "vor " + Math.floor(s / 3600) + " Std.";
    if (s < 7 * 86400) { var t = Math.floor(s / 86400); return t === 1 ? "gestern" : "vor " + t + " Tagen"; }
    return new Date(iso).toLocaleDateString("de-DE", { day: "numeric", month: "short" });
  }
  function glocke(box) {
    var knopf = box.querySelector(".glocke-knopf"), menue = box.querySelector(".glocke-menue"), zahl = knopf.querySelector(".zahl");
    var letzte = null;
    function zeigeZahl(n) {
      var alt = zahl.textContent;
      zahl.textContent = n > 9 ? "9+" : String(n);
      zahl.hidden = !n;
      knopf.setAttribute("aria-label", n ? n + " neue Benachrichtigungen" : "Benachrichtigungen");
      if (n && alt !== zahl.textContent) { knopf.classList.remove("klingelt"); void knopf.offsetWidth; knopf.classList.add("klingelt"); }
    }
    function liste(d) {
      var l = menue.querySelector(".glocke-liste");
      if (!d.liste.length) { l.innerHTML = "<p class='glocke-leer'>Noch nichts Neues. Wenn dich jemand bei einer Kanban-Karte einträgt, erscheint es hier.</p>"; return; }
      l.innerHTML = d.liste.slice(0, 30).map(function (e) {
        return "<a class='glocke-eintrag" + (e.gelesen ? "" : " neu") + "' href='" + esc(e.link || "#") + "'>" +
          avatar({ id: e.von, anzeigename: e.vonName, farbe: e.vonFarbe }, 30) +
          "<span><span class='t'>" + esc(e.text) + "</span><small>" + esc(vorWann(e.zeit)) + "</small></span></a>";
      }).join("");
    }
    function hole() {
      if (document.hidden) return;
      api("glocke").then(function (d) { letzte = d; zeigeZahl(d.ungelesen); if (!menue.hidden) liste(d); }).catch(function () {});
    }
    menueAn(knopf, menue, function () {
      if (letzte) liste(letzte);
      api("glocke").then(function (d) {
        letzte = d; liste(d);
        if (d.ungelesen) api("glocke/gelesen", {}).then(function () { zeigeZahl(0); d.liste.forEach(function (e) { e.gelesen = true; }); }).catch(function () {});
      }).catch(function () { menue.querySelector(".glocke-liste").innerHTML = "<p class='glocke-leer'>Der Dienst antwortet gerade nicht.</p>"; });
    });
    hole();
    setInterval(hole, 45000);
    document.addEventListener("visibilitychange", hole);
  }

  /* Navigation oben auf jeder Seite. aktiv: "uebersicht", "map", "technik", "kanban", "team", "import", "versionen", "admin" oder eine Gebäude-ID */
  function navi(aktiv) {
    var nav = document.getElementById("nav");
    if (!nav) return;
    function link(href, text, an) { return "<a href='" + href + "'" + (an ? " aria-current='page'" : "") + ">" + esc(text) + "</a>"; }
    nav.innerHTML = link("index.html", "Übersicht", aktiv === "uebersicht") + link("map.html", "Map", aktiv === "map") + link("technik.html", "Technik", aktiv === "technik") + link("kanban.html", "Kanban", aktiv === "kanban") + link("team.html", "Team", aktiv === "team");
    var gebaeude = ladeJSON("campus/campus.json").then(function (c) {
      var h = "";
      c.gebaeude.forEach(function (g) { if (g.ordner) h += link("gebaeude.html?id=" + encodeURIComponent(g.id), g.name, aktiv === g.id); });
      if (h) nav.insertAdjacentHTML("beforeend", "<span class='sep' aria-hidden='true'></span>" + h);
    }).catch(function () {}).then(function () { linse(nav, "a[aria-current='page']"); });
    var site = nav.parentNode;
    Promise.all([ich(), gebaeude]).then(function (r) {
      var i = r[0];
      if (!site) return;
      var box = document.createElement("div");
      box.className = "wer";
      if (!i) {
        /* Ohne Login (lokal): nur der Schalter für die Darstellung */
        box.innerHTML = "<button type='button' class='thema-knopf' aria-haspopup='true' aria-expanded='false' title='Darstellung'>" + ICON[thema()] + "</button>" +
          "<div class='menue' hidden><div class='menue-teil' style='border-top:0;margin-top:0'><span>Darstellung</span>" + themaWahl() + "</div></div>";
      } else {
        /* Import, Versionen und Admin wohnen im Profilmenü, damit die Leiste einzeilig bleibt */
        var extra = [["import", "import.html", "Karte aktualisieren"], ["versionen", "versionen.html", "Versionen"]];
        if (i.admin) extra.push(["admin", "admin.html", "Admin"]);
        var extraAktiv = extra.filter(function (e) { return e[0] === aktiv; })[0];
        box.innerHTML = (extraAktiv ? link(extraAktiv[1], extraAktiv[2], true) : "") +
          "<button type='button' class='glocke-knopf' aria-haspopup='true' aria-expanded='false' aria-label='Benachrichtigungen' title='Benachrichtigungen'>" + GLOCKE_SVG + "<span class='zahl' hidden></span></button>" +
          "<div class='menue glocke-menue' hidden><div class='glocke-kopf'><b>Benachrichtigungen</b></div><div class='glocke-liste'><p class='glocke-leer'>Lade …</p></div></div>" +
          "<button type='button' class='ich-knopf' aria-haspopup='true' aria-expanded='false' title='Mein Profil'>" + avatar(i) + "<span>" + esc(i.anzeigename) + "</span><span class='pfeil-runter' aria-hidden='true'></span></button>" +
          "<div class='menue' hidden>" +
            "<div class='menue-kopf'>" + avatar(i, 38) + "<div><b>" + esc(i.anzeigename) + "</b>" + (i.minecraft ? "<small>" + esc(i.minecraft) + "</small>" : "") + "</div></div>" +
            "<a href='team.html#" + encodeURIComponent(i.id) + "'>Mein Profil</a>" +
            "<a href='kanban.html?person=" + encodeURIComponent(i.id) + "'>Meine Aufgaben</a>" +
            "<div class='menue-trenner'></div>" +
            extra.map(function (e) { return link(e[1], e[2], e[0] === aktiv); }).join("") +
            "<div class='menue-teil'><span>Darstellung</span>" + themaWahl() + "</div>" +
            "<a class='abmelden' href='/outpost.goauthentik.io/sign_out'>Abmelden</a>" +
          "</div>";
      }
      site.appendChild(box);
      menueAn(box.querySelector(".ich-knopf, .thema-knopf"), box.querySelector(".menue:not(.glocke-menue)"));
      if (i) glocke(box);
    });
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

  /* --- Effekte: Einfliegen beim Scrollen, Lichtschein unter der Maus, hochzählende Zahlen, Nav-Marker ---
   * Die Seiten bauen ihren Inhalt erst nach dem Laden, darum schaut ein MutationObserver nach neuen Elementen. */
  (function effekte() {
    var ruhig = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var ZIELE = ".box, .gebkarte, .team-karte, .kb-spalte, .tk-kachel, .campus-list a, .flow";
    var io = !ruhig && "IntersectionObserver" in window ? new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        e.target.classList.remove("vorher");
        setTimeout(function () { e.target.classList.remove("einflug"); e.target.style.removeProperty("--verz"); }, 900);
      });
    }, { rootMargin: "0px 0px -6% 0px" }) : null;

    function zaehle(el) {
      var m = /^(\d+)(\D*)$/.exec(el.textContent.trim());
      if (!m || ruhig) return;
      var ziel = +m[1], rest = m[2], t0 = null;
      if (ziel < 2) return;
      function schritt(t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(ziel * e) + rest;
        if (p < 1) requestAnimationFrame(schritt);
      }
      requestAnimationFrame(schritt);
    }

    function neu(wurzel) {
      if (!wurzel.querySelectorAll) return;
      var liste = [].slice.call(wurzel.querySelectorAll(ZIELE));
      if (wurzel.matches && wurzel.matches(ZIELE)) liste.unshift(wurzel);
      var nr = 0;
      liste.forEach(function (el) {
        if (el.dataset.fx) return;
        el.dataset.fx = "1";
        /* nur beim ersten Aufbau, nicht wenn Kanban & Co. später neu zeichnen */
        if (io && !el.closest(".menue") && performance.now() < 4000) {
          el.classList.add("einflug", "vorher");
          el.style.setProperty("--verz", Math.min(nr++, 10) * 55 + "ms");
          io.observe(el);
        }
        if (el.classList.contains("tk-kachel")) { var b = el.querySelector("b"); if (b) zaehle(b); }
      });
      [].slice.call(wurzel.querySelectorAll(".note")).forEach(function (n) { n.classList.toggle("laedt", /^Lade\b/.test(n.textContent.trim())); });
    }

    function start() {
      neu(document.body);
      new MutationObserver(function (ms) {
        ms.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) neu(n); else if (n.parentNode) neu(n.parentNode); }); });
      }).observe(document.body, { childList: true, subtree: true });
    }
    if (document.body) start(); else document.addEventListener("DOMContentLoaded", start);

    /* Lichtschein: Mausposition in der Karte als CSS-Variablen */
    document.addEventListener("pointermove", function (ev) {
      var box = ev.target.closest && ev.target.closest(".box");
      if (!box) return;
      var r = box.getBoundingClientRect();
      box.style.setProperty("--mx", (ev.clientX - r.left) + "px");
      box.style.setProperty("--my", (ev.clientY - r.top) + "px");
    }, { passive: true });
  })();

  /* Glas-Linse, die zum Link unter der Maus gleitet und zum aktiven Link zurückfedert.
   * Für die Hauptnavigation und die Unter-Tabs der Gebäudeseiten. */
  function linse(box, aktivSel) {
    if (!box || box.querySelector(":scope > .marker")) return;
    var m = document.createElement("span");
    m.className = "marker"; m.setAttribute("aria-hidden", "true");
    box.appendChild(m); box.classList.add("mit-marker");
    function auf(a, istAktiv) {
      if (!a) { m.style.opacity = "0"; return; }
      m.style.opacity = "1"; m.style.left = a.offsetLeft + "px"; m.style.width = a.offsetWidth + "px";
      m.style.top = a.offsetTop + "px"; m.style.height = a.offsetHeight + "px";
      m.style.setProperty("--punkt", istAktiv ? "1" : "0");
    }
    function aktiv() { auf(box.querySelector(aktivSel), true); }
    box.addEventListener("pointerover", function (ev) { var a = ev.target.closest("a"); if (a && box.contains(a)) auf(a, a.matches(aktivSel)); });
    box.addEventListener("pointerleave", aktiv);
    window.addEventListener("resize", aktiv);
    new MutationObserver(aktiv).observe(box, { attributes: true, subtree: true, attributeFilter: ["aria-current"] });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(aktiv);
    m.style.transition = "none"; aktiv(); void m.offsetWidth; m.style.transition = "";
  }
  document.addEventListener("DOMContentLoaded", function () { linse(document.querySelector(".subtabs"), "a[aria-current='true']"); });

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]; }); }

  window.Campus = { bereit: bereit, ladeJSON: ladeJSON, ladeText: ladeText, baueModell: baueModell, baueSzene: baueSzene, baueCampus: baueCampus, blickeAuf: blickeAuf, rahmen: rahmen, cssVar: cssVar, esc: esc, drehGruppe: drehGruppe, weltVon: weltVon, weltBox: weltBox, navi: navi, linse: linse, thema: thema, setzeThema: setzeThema, themaWahl: themaWahl, ladeGebaeude: ladeGebaeude, api: api, ich: ich, avatar: avatar };
})();
