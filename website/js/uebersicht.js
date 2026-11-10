/* Übersicht: eine Karte pro Gebäude mit Kennzahlen und Sprungmarken. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  C.navi("uebersicht");

  C.ladeJSON("campus/campus.json").then(function (campus) {
    if (campus.welt) document.getElementById("welt").textContent = campus.welt;
    return Promise.all(campus.gebaeude.map(function (g) {
      if (!g.ordner) return Promise.resolve({ g: g });
      return C.ladeGebaeude(g.id).then(function (d) { d.g = g; return d; }).catch(function () { return { g: g }; });
    }));
  }).then(function (liste) {
    var h = "", netze = "";
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
        var base = "gebaeude.html?id=" + encodeURIComponent(g.id);
        h += "<div class='links'><a href='" + base + "#ansicht'>3D-Ansicht</a><a href='" + base + "#konfig'>Konfiguration</a>" + (geb.dateien && geb.dateien.bauplan ? "<a href='" + base + "#bauplan'>Bauplan</a>" : "") + "</div>";
        d.konfig.netzwerke.forEach(function (n) {
          netze += "<div class='box flow' style='grid-template-columns:220px minmax(0,1fr)'><div class='kopf'><strong>" + esc(n.name) + "</strong><small>" + esc(n.mod) + " · " + esc(g.name) + "</small></div><div class='wer'>";
          n.kanaele.forEach(function (k) { netze += "<span><span class='k' style='background:" + k.farbe + "'>K" + k.nr + "</span> " + esc(k.zweck) + "</span>"; });
          netze += "</div></div>";
        });
      } else {
        h += "<p class='note'>Noch kein Ordner angelegt.</p>";
      }
      h += "</article>";
    });
    document.getElementById("karten").innerHTML = h;
    document.getElementById("netze").innerHTML = netze || "<p class='note'>Noch keine Netzwerke eingetragen.</p>";
  }).catch(function (e) { document.getElementById("karten").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });
})();
