/* Technik: Übersicht über das ME-System und alle Logistics Networks.
 * ME-Zahlen werden aus den Blockmodellen gezählt, die Netze kommen aus konfig.json. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("technik");

  /* AE2-Blöcke, die in der Übersicht gezählt werden, in dieser Reihenfolge */
  var ME_TEILE = [
    ["ae2:controller", "ME Controller", "Blöcke"],
    ["extendedae:ex_drive", "ME Extended Drive", "Stück, je 20 Zellen-Plätze"],
    ["ae2:drive", "ME Drive", "Stück, je 10 Zellen-Plätze"],
    ["extendedae:wireless_connect", "ME Wireless Connector", "Stück"],
    ["extendedae:wireless_hub", "ME Wireless Hub", "Stück"],
    ["ae2:wireless_access_point", "ME Wireless Access Point", "Stück"],
    ["ae2:crafting_unit", "Crafting Unit", "Stück"],
    ["ae2:pattern_provider", "Pattern Provider", "Stück"],
    ["ae2:molecular_assembler", "Molecular Assembler", "Stück"]
  ];
  var SLOTS = { "extendedae:ex_drive": 20, "ae2:drive": 10 };

  C.ladeJSON("campus/campus.json").then(function (campus) {
    return Promise.all(campus.gebaeude.filter(function (g) { return g.ordner; }).map(function (g) {
      return C.ladeGebaeude(g.id).then(function (d) { d.g = g; return d; }).catch(function () { return null; });
    }));
  }).then(function (liste) {
    liste = liste.filter(Boolean);
    zeigeME(liste);
    zeigeNetze(liste);
  }).catch(function (e) { $("me").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });

  /* Blöcke eines Modells nach Sorte zählen; Kabel nach Kabelsorte */
  function zaehle(modell) {
    var z = {};
    if (!modell) return z;
    modell.bloecke.forEach(function (b) {
      var s = modell.palette[b[3]], id = s.id.split("|")[0];
      z[id] = (z[id] || 0) + 1;
    });
    return z;
  }

  function zeigeME(liste) {
    var mitME = liste.map(function (d) { return { d: d, z: zaehle(d.modell) }; })
      .filter(function (x) { return Object.keys(x.z).some(function (id) { return /^(ae2|extendedae):/.test(id); }); });
    if (!mitME.length) { $("me").innerHTML = "<p class='note'>Noch kein Gebäude mit AE2-Blöcken im Modell.</p>"; return; }
    /* Hauptgebäude = das mit dem Controller */
    mitME.sort(function (a, b) { return (b.z["ae2:controller"] || 0) - (a.z["ae2:controller"] || 0); });
    var haupt = mitME[0], d = haupt.d, z = haupt.z, h = "";

    var slots = 0; Object.keys(SLOTS).forEach(function (id) { slots += (z[id] || 0) * SLOTS[id]; });
    var kabel = 0, kabelSorten = [];
    d.modell.palette.forEach(function (s, i) {
      if (s.form !== "kabel") return;
      var n = d.modell.bloecke.filter(function (b) { return b[3] === i; }).length;
      kabel += n; kabelSorten.push({ name: s.name, farbe: s.farbe, n: n });
    });
    var zus = d.modell.zusatz || {}, p2p = (zus.parts || {})["ae2:me_p2p_tunnel"] || 0;

    h += "<div class='box tk-me'>";
    h += "<div class='tk-me-kopf'><div><h3>" + esc(d.geb.name) + "</h3><p class='note'>" + esc(d.geb.zweck || "") + "</p></div>";
    h += "<div><span class='chip" + (d.geb.status === "gebaut" ? " ok" : "") + "'>" + esc(d.geb.status || "") + "</span> <a class='tk-link' href='gebaeude.html?id=" + encodeURIComponent(d.id) + "#ansicht'>3D-Ansicht →</a></div></div>";
    h += "<div class='tk-zahlen'>";
    h += kachel(z["ae2:controller"] || 0, "Controller-Blöcke");
    h += kachel((z["extendedae:ex_drive"] || 0) + (z["ae2:drive"] || 0), "Drives", slots + " Zellen-Plätze");
    h += kachel(kabel, "Kabelblöcke", kabelSorten.length + " Sorten");
    h += kachel(p2p, "P2P Tunnels");
    h += kachel((z["extendedae:wireless_connect"] || 0) + (z["extendedae:wireless_hub"] || 0) + (z["ae2:wireless_access_point"] || 0), "Wireless-Teile");
    h += "</div>";

    h += "<div class='tk-spalten'>";
    h += "<div><h4>Aufbau</h4><dl class='kv'>";
    ME_TEILE.forEach(function (t) { if (z[t[0]]) h += "<dt>" + esc(t[1]) + "</dt><dd>" + z[t[0]] + " " + esc(t[2]) + "</dd>"; });
    h += "</dl></div>";
    h += "<div><h4>Kabel</h4><ul class='tk-kabel'>";
    kabelSorten.sort(function (a, b) { return b.n - a.n; }).forEach(function (k) {
      h += "<li><i style='background:" + k.farbe + "'></i>" + esc(k.name) + "<b>" + k.n + "</b></li>";
    });
    h += "</ul></div>";
    h += "<div><h4>Energie und Anbindung</h4><dl class='kv'>";
    var gates = [];
    liste.forEach(function (x) {
      var k = (x.modell && x.modell.zusatz && x.modell.zusatz.enderGateKanaele) || {};
      Object.keys(k).forEach(function (kn) { gates.push(x.geb.name + ": " + k[kn] + " × Kanal " + kn); });
    });
    if (gates.length) h += "<dt>Powah Ender Gates</dt><dd>" + gates.map(esc).join("<br>") + "</dd>";
    h += "<dt>Wireless</dt><dd>" + ((z["extendedae:wireless_connect"] || 0) + " Connectors, " + (z["extendedae:wireless_hub"] || 0) + " Hub") + "</dd>";
    var andere = mitME.slice(1).map(function (x) { return x.d.geb.name; });
    if (andere.length) h += "<dt>AE2 auch in</dt><dd>" + andere.map(esc).join(", ") + "</dd>";
    h += "</dl></div>";
    h += "</div>";

    /* Von Hand gepflegte Angaben aus konfig.json */
    var me = d.konfig.me || {};
    h += "<div class='tk-spalten'>";
    h += "<div><h4>Zellen</h4>" + ((me.zellen || []).length
      ? "<dl class='kv'>" + me.zellen.map(function (c) { return "<dt>" + esc(c[0]) + "</dt><dd>" + esc(c[1]) + "</dd>"; }).join("") + "</dl>"
      : "<p class='note'>Noch nicht eingetragen. Die Schematic speichert keine Inventare, Zellen also von Hand in <code>konfig.json</code> unter <code>me.zellen</code> eintragen.</p>") + "</div>";
    h += "<div><h4>Angebunden</h4>" + ((me.anbindungen || []).length
      ? "<ul class='tk-liste'>" + me.anbindungen.map(function (a) { return "<li><b>" + esc(a.gebaeude) + "</b> · " + esc(a.wie) + (a.was ? "<br><small>" + esc(a.was) + "</small>" : "") + "</li>"; }).join("") + "</ul>"
      : "<p class='note'>Noch nichts eingetragen.</p>") + "</div>";
    h += "<div><h4>Hinweise</h4>" + ((me.hinweise || []).length
      ? "<ul class='tk-liste'>" + me.hinweise.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>"
      : "<p class='note'>Keine.</p>") + "</div>";
    h += "</div>";

    if (d.konfig.teile.length) {
      h += "<div><h4>Teile mit Position</h4><div class='tk-teile'>";
      d.konfig.teile.forEach(function (t) {
        var w = C.weltVon(d.geb.welt && d.geb.welt.p0, d.geb.welt && d.geb.welt.drehung, t.von[0], t.von[1], t.von[2]);
        h += "<span><b>" + esc(t.name) + "</b>" + (w ? " · Welt " + w.join(", ") : "") + "</span>";
      });
      h += "</div></div>";
    }
    h += "</div>";
    $("me").innerHTML = h;
  }
  function kachel(zahl, text, unter) {
    return "<div class='tk-kachel'><b>" + zahl + "</b><span>" + esc(text) + "</span>" + (unter ? "<small>" + esc(unter) + "</small>" : "") + "</div>";
  }

  function zeigeNetze(liste) {
    var h = "", anzahl = 0;
    liste.forEach(function (d) {
      d.konfig.netzwerke.forEach(function (n, ni) {
        if (!n.kanaele) return;
        anzahl++;
        var eigene = function (node) { return (node.netz || d.konfig.netzwerke[0].id) === n.id; };
        var nodes = 0, zeilen = [];
        d.konfig.teile.forEach(function (t) {
          (t.nodes || []).forEach(function (node) {
            if (!eigene(node)) return;
            nodes += node.anzahl || 1;
            zeilen.push({ t: t, n: node });
          });
        });
        var chips = n.kanaele.map(function (k) { return chip(k); }).join("");
        h += "<details class='box tk-netz'" + (ni === 0 && anzahl === 1 ? " open" : "") + "><summary>";
        h += "<span class='tk-netz-name'><b>„" + esc(n.name) + "“</b><small>" + esc(n.mod) + " · " + esc(d.geb.name) + "</small></span>";
        h += "<span class='tk-netz-chips'>" + chips + "</span>";
        h += "<span class='tk-netz-zahl'><b>" + nodes + "</b> Nodes</span></summary>";
        h += "<div class='tk-netz-inhalt'>";
        if (n.upgrade) h += "<p class='note' style='margin:0'>" + esc(n.upgrade) + "</p>";

        h += "<div class='scrollx'><table class='tk-tabelle'><thead><tr><th>Kanal</th><th>Typ</th><th>Takt</th><th>Sender</th><th></th><th>Empfänger</th></tr></thead><tbody>";
        n.kanaele.forEach(function (k) {
          var sender = [], empf = [];
          zeilen.forEach(function (z) {
            z.n.kanaele.forEach(function (kk) {
              if (kk.k !== k.nr) return;
              var txt = (z.n.label === z.t.name ? z.t.name : z.t.name + " · " + z.n.label) + ((z.n.anzahl || 1) > 1 ? " ×" + z.n.anzahl : "");
              var e = "<span title='" + esc(kk.filter || "") + "'>" + esc(txt) + "</span>";
              if (kk.richtung === "rein") { if (empf.indexOf(e) < 0) empf.push(e); } else if (sender.indexOf(e) < 0) sender.push(e);
            });
          });
          h += "<tr><td>" + chip(k) + "</td><td>" + esc(k.typ) + "<br><small>" + esc(k.zweck || "") + "</small></td><td>" + esc(k.takt || "–") + "</td>";
          h += "<td><div class='tk-wer'>" + (sender.join("") || "–") + "</div></td><td class='tk-pfeil'>→</td><td><div class='tk-wer'>" + (empf.join("") || "–") + "</div></td></tr>";
        });
        h += "</tbody></table></div>";

        h += "<details class='tk-nodes'><summary>Alle Nodes einzeln (" + nodes + ")</summary><div class='scrollx'><table class='tk-tabelle'><thead><tr><th>Node</th><th>Teil</th><th>Anzahl</th><th>Kanäle und Filter</th></tr></thead><tbody>";
        zeilen.forEach(function (z) {
          h += "<tr><td><b>" + esc(z.n.label) + "</b></td><td>" + esc(z.t.name) + "<br><small>" + esc(z.t.zelle || "") + "</small></td><td>" + (z.n.anzahl || 1) + "</td><td><ul class='tk-kanalliste'>";
          z.n.kanaele.forEach(function (kk) {
            var k = n.kanaele.filter(function (x) { return x.nr === kk.k; })[0] || { nr: kk.k, farbe: "#777" };
            h += "<li>" + chip(k) + "<span class='tk-richtung'>" + esc(kk.richtung) + "</span>" + esc(kk.filter || "") + "</li>";
          });
          h += "</ul></td></tr>";
        });
        h += "</tbody></table></div></details>";
        h += "<a class='tk-link' href='gebaeude.html?id=" + encodeURIComponent(d.id) + "#konfig'>Konfiguration von " + esc(d.geb.name) + " →</a>";
        h += "</div></details>";
      });
    });
    $("netze").innerHTML = h || "<p class='note'>Noch keine Logistics Networks eingetragen.</p>";
    $("alleAuf").addEventListener("click", function () { $("netze").querySelectorAll("details").forEach(function (x) { x.open = true; }); });
    $("alleZu").addEventListener("click", function () { $("netze").querySelectorAll("details").forEach(function (x) { x.open = false; }); });
  }
  function chip(k) { return "<span class='k' style='background:" + (k.farbe || "#777") + "'>K" + k.nr + "</span>"; }
})();
