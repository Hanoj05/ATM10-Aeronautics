/* Kanban: Karten aus kanban/karten/*.json in drei Spalten, verschieben per Drag & Drop.
 * Mit Login auf dem Server kommen die Daten über den Campus-Dienst (/api/kanban), jede
 * Änderung wird dort ein Commit. Ohne Dienst (lokal) zeigt die Seite das Board nur an. */
(function () {
  "use strict";
  var C = window.Campus, esc = C.esc;
  var $ = function (s) { return document.getElementById(s); };
  C.navi("kanban");

  var SPALTEN = [
    { status: "offen", titel: "Offen" },
    { status: "in Arbeit", titel: "In Arbeit" },
    { status: "erledigt", titel: "Erledigt" }
  ];
  var BEREICHE = ["Gebäude", "3D", "Doku", "Website", "Betrieb"];
  var NEU_LADEN_ALLE = 20000;          /* so oft fragt die Seite, ob es etwas Neues gibt */

  var d = { phasen: [], karten: [], commit: null };
  var gebaeude = {}, gebaeudeListe = [], leute = {}, leuteListe = [];
  var wer = null, schreiben = false;
  var ziehen = null, offen = null, wartet = false;

  /* ---------- Filter (stehen auch in der Adresse, damit man sie teilen kann) ---------- */
  var F = { person: "", gebaeude: "", bereich: "", wo: "", phase: "", gruppiert: false };
  (function () {
    var q = new URLSearchParams(location.search);
    Object.keys(F).forEach(function (k) { if (q.has(k)) F[k] = k === "gruppiert" ? q.get(k) === "1" : q.get(k); });
  })();
  function filterMerken() {
    var q = new URLSearchParams();
    Object.keys(F).forEach(function (k) { if (F[k]) q.set(k, F[k] === true ? "1" : F[k]); });
    var s = q.toString();
    history.replaceState(null, "", location.pathname + (s ? "?" + s : ""));
  }
  function passt(k) {
    return (!F.person || k.zustaendig.indexOf(F.person) >= 0) && (!F.gebaeude || k.gebaeude === F.gebaeude) &&
      (!F.bereich || k.bereich === F.bereich) && (!F.wo || k.wo === F.wo) && (!F.phase || k.phase === F.phase);
  }

  /* ---------- Hilfen ---------- */
  function sortiert(liste) { return liste.slice().sort(function (a, b) { return a.rang - b.rang || (a.titel < b.titel ? -1 : 1); }); }
  function heute() { var t = new Date(); return t.getFullYear() + "-" + ("0" + (t.getMonth() + 1)).slice(-2) + "-" + ("0" + t.getDate()).slice(-2); }
  function datum(s) { var t = s.split("-"); return t[2] + "." + t[1] + "." + t[0]; }
  function phaseVon(id) { for (var i = 0; i < d.phasen.length; i++) if (d.phasen[i].id === id) return d.phasen[i]; return null; }
  function karteVon(id) { for (var i = 0; i < d.karten.length; i++) if (d.karten[i].id === id) return d.karten[i]; return null; }
  var toastZeit = null;
  function toast(text, fehler) {
    var t = $("toast");
    t.textContent = text; t.className = "kb-toast" + (fehler ? " fehler" : ""); t.hidden = false;
    clearTimeout(toastZeit); toastZeit = setTimeout(function () { t.hidden = true; }, fehler ? 8000 : 3000);
  }

  /* ---------- Zeichnen ---------- */
  function karteHtml(k) {
    var g = k.gebaeude && gebaeude[k.gebaeude];
    var ueberfaellig = k.faellig && k.status !== "erledigt" && k.faellig < heute();
    var ph = phaseVon(k.phase);
    var meta = [];
    if (g) meta.push("<a class='kb-geb' href='gebaeude.html?id=" + encodeURIComponent(k.gebaeude) + (k.tab ? "#" + encodeURIComponent(k.tab) : "") + "'>" + esc(g.name) + " →</a>");
    if (k.faellig) meta.push("<span class='kb-faellig" + (ueberfaellig ? " drueber" : "") + "' title='fällig'>" + (ueberfaellig ? "überfällig " : "bis ") + esc(datum(k.faellig)) + "</span>");
    if (!F.gruppiert && ph) meta.push("<span class='kb-phase'>" + esc(ph.titel) + "</span>");
    var koepfe = k.zustaendig.map(function (id) { return leute[id] ? "<span title='" + esc(leute[id].anzeigename) + "'>" + C.avatar(leute[id], 22) + "</span>" : ""; }).join("");
    return "<article class='kb-karte kb-" + (k.status === "in Arbeit" ? "arbeit" : k.status) + "' data-id='" + esc(k.id) + "'" +
      (schreiben ? " draggable='true' tabindex='0' role='button' aria-label='" + esc(k.titel) + " bearbeiten'" : "") + ">" +
      "<div class='kb-chips'><span class='kb-wo kb-" + (k.wo === "Minecraft" ? "mc" : "web") + "'>" + esc(k.wo) + "</span>" + (k.bereich !== k.wo ? "<span class='kb-bereich'>" + esc(k.bereich) + "</span>" : "") + "</div>" +
      "<h3>" + esc(k.titel) + "</h3>" +
      (k.beschreibung ? "<p class='kb-text'>" + esc(k.beschreibung) + "</p>" : "") +
      ((meta.length || koepfe) ? "<div class='kb-meta'>" + meta.join("") + (koepfe ? "<span class='kb-koepfe'>" + koepfe + "</span>" : "") + "</div>" : "") +
      "</article>";
  }

  function spalteHtml(sp, karten, phase) {
    return "<section class='kb-spalte' data-status='" + esc(sp.status) + "'>" +
      "<h2>" + esc(sp.titel) + " <span>" + karten.length + "</span></h2>" +
      "<div class='kb-liste' data-status='" + esc(sp.status) + "'" + (phase ? " data-phase='" + esc(phase) + "'" : "") + ">" +
      karten.map(karteHtml).join("") + "</div></section>";
  }

  function zeige() {
    var sichtbar = sortiert(d.karten.filter(passt));
    var erledigt = sichtbar.filter(function (k) { return k.status === "erledigt"; }).length;
    var arbeit = sichtbar.filter(function (k) { return k.status === "in Arbeit"; }).length;
    var pz = sichtbar.length ? Math.round(erledigt / sichtbar.length * 100) : 0;
    $("stand").innerHTML = "<div class='kb-zahlen'><b>" + pz + " %</b><span>" + erledigt + " von " + sichtbar.length + " Karten erledigt, " + arbeit + " in Arbeit" +
      (sichtbar.length !== d.karten.length ? " (gefiltert, insgesamt " + d.karten.length + ")" : "") + "</span></div>" +
      "<div class='kb-balken'><i style='width:" + (sichtbar.length ? erledigt / sichtbar.length * 100 : 0) + "%'></i><i class='a' style='width:" + (sichtbar.length ? arbeit / sichtbar.length * 100 : 0) + "%'></i></div>";

    var h = "";
    if (F.gruppiert) {
      d.phasen.forEach(function (ph) {
        if (F.phase && F.phase !== ph.id) return;
        var inPhase = sichtbar.filter(function (k) { return k.phase === ph.id; });
        var fertig = inPhase.filter(function (k) { return k.status === "erledigt"; }).length;
        h += "<section class='kb-bahn'><header><h2>" + esc(ph.titel) + "</h2><span class='note'>" + esc(ph.ziel || "") + "</span><span class='kb-bahn-zahl'>" + fertig + " / " + inPhase.length + "</span></header>" +
          "<div class='kb-spalten'>" + SPALTEN.map(function (sp) {
            return spalteHtml(sp, inPhase.filter(function (k) { return k.status === sp.status; }), ph.id);
          }).join("") + "</div></section>";
      });
    } else {
      h = "<div class='kb-spalten'>" + SPALTEN.map(function (sp) {
        return spalteHtml(sp, sichtbar.filter(function (k) { return k.status === sp.status; }));
      }).join("") + "</div>";
    }
    $("board").innerHTML = h;
  }

  /* ---------- Laden ---------- */
  function ladeStatisch() {
    return Promise.all([C.ladeJSON("kanban/phasen.json"), C.ladeJSON("kanban/liste.json")]).then(function (r) {
      return Promise.all(r[1].map(function (id) { return C.ladeJSON("kanban/karten/" + id + ".json").catch(function () { return null; }); }))
        .then(function (karten) { return { phasen: r[0], karten: karten.filter(Boolean), commit: null }; });
    });
  }
  function laden() {
    return (schreiben ? C.api("kanban") : ladeStatisch()).then(function (neu) {
      neu.karten.forEach(function (k) { k.zustaendig = k.zustaendig || []; k.rang = Number(k.rang) || 0; });
      d = neu; wartet = false;
      zeige();
    });
  }

  /* Neues von anderen? Alle 20 Sekunden und beim Zurückkehren zum Tab nachsehen. */
  function nachsehen() {
    if (!schreiben || document.hidden) return;
    C.api("stand").then(function (s) {
      if (s.commit === d.commit) return;
      if (ziehen || offen) { wartet = true; return; }          /* nicht mitten im Ziehen oder Bearbeiten */
      laden().then(function () { live("aktualisiert " + new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })); });
    }).catch(function (e) { if (e.status === 401) live("abgemeldet, bitte neu laden", true); });
  }
  function live(text, schlecht) { var l = $("live"); l.hidden = false; l.textContent = text; l.classList.toggle("schlecht", !!schlecht); }

  /* ---------- Speichern ---------- */
  function speichere(k, felder) {
    felder.version = k.version;
    return C.api("karten/" + encodeURIComponent(k.id), felder).then(function (j) {
      for (var i = 0; i < d.karten.length; i++) if (d.karten[i].id === k.id) d.karten[i] = j.karte;
      if (j.commit) d.commit = j.commit;
      return j.karte;
    });
  }
  function fehlerNachLaden(e) {
    toast(e.message, true);
    return laden();
  }

  /* ---------- Drag & Drop ---------- */
  var platzhalter = document.createElement("div");
  platzhalter.className = "kb-platz";

  function zielIndex(liste, y) {
    var kinder = [].filter.call(liste.querySelectorAll(".kb-karte"), function (el) { return el.getAttribute("data-id") !== ziehen; });
    for (var i = 0; i < kinder.length; i++) {
      var r = kinder[i].getBoundingClientRect();
      if (y < r.top + r.height / 2) return { vor: kinder[i], index: i, kinder: kinder };
    }
    return { vor: null, index: kinder.length, kinder: kinder };
  }

  $("board").addEventListener("dragstart", function (ev) {
    var el = ev.target.closest && ev.target.closest(".kb-karte");
    if (!el || !schreiben) return;
    ziehen = el.getAttribute("data-id");
    ev.dataTransfer.effectAllowed = "move";
    ev.dataTransfer.setData("text/plain", ziehen);
    platzhalter.style.height = el.offsetHeight + "px";
    setTimeout(function () { el.classList.add("zieht"); }, 0);
  });
  $("board").addEventListener("dragover", function (ev) {
    var liste = ev.target.closest && ev.target.closest(".kb-liste");
    if (!liste || !ziehen) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "move";
    var z = zielIndex(liste, ev.clientY);
    if (z.vor) liste.insertBefore(platzhalter, z.vor); else liste.appendChild(platzhalter);
  });
  $("board").addEventListener("drop", function (ev) {
    var liste = ev.target.closest && ev.target.closest(".kb-liste");
    if (!liste || !ziehen) return;
    ev.preventDefault();
    var k = karteVon(ziehen);
    var z = zielIndex(liste, ev.clientY);
    var nachbar = function (el) { return el ? karteVon(el.getAttribute("data-id")) : null; };
    var davor = nachbar(z.kinder[z.index - 1]), danach = nachbar(z.kinder[z.index]);
    var rang = davor && danach ? (davor.rang + danach.rang) / 2 : davor ? davor.rang + 1000 : danach ? danach.rang - 1000 : 0;
    var felder = { rang: Math.round(rang * 1000) / 1000 };
    var status = liste.getAttribute("data-status"), phase = liste.getAttribute("data-phase");
    if (status !== k.status) felder.status = status;
    if (phase && phase !== k.phase) felder.phase = phase;
    aufraeumen();
    if (felder.rang === k.rang && !felder.status && !felder.phase) return;
    /* Gleich anzeigen, dann speichern. Geht es schief, kommt der echte Stand zurück. */
    var vorher = { rang: k.rang, status: k.status, phase: k.phase };
    k.rang = felder.rang; if (felder.status) k.status = felder.status; if (felder.phase) k.phase = felder.phase;
    zeige();
    speichere(Object.assign({}, k, vorher), felder).then(function (neu) {
      zeige();
      if (felder.status) toast("„" + neu.titel + "“ ist jetzt " + neu.status + ".");
    }).catch(fehlerNachLaden);
  });
  function aufraeumen() {
    if (platzhalter.parentNode) platzhalter.parentNode.removeChild(platzhalter);
    var el = document.querySelector(".kb-karte.zieht");
    if (el) el.classList.remove("zieht");
    ziehen = null;
    if (wartet) laden();
  }
  $("board").addEventListener("dragend", aufraeumen);

  /* ---------- Bearbeiten ---------- */
  var ed = $("edForm");
  function oeffne(k) {
    if (!schreiben) return;
    offen = k || { id: null, titel: "", beschreibung: "", status: "offen", phase: F.phase || (d.phasen.length ? d.phasen[d.phasen.length - 1].id : ""),
      wo: F.wo || "Minecraft", bereich: F.bereich || "Gebäude", gebaeude: F.gebaeude || null, zustaendig: F.person ? [F.person] : (wer ? [wer.id] : []), faellig: null };
    $("edTitel").textContent = offen.id ? "Karte bearbeiten" : "Neue Karte";
    ["titel", "beschreibung", "status", "phase", "wo", "bereich"].forEach(function (f) { ed.elements[f].value = offen[f] || ""; });
    ed.elements.gebaeude.value = offen.gebaeude || "";
    ed.elements.faellig.value = offen.faellig || "";
    [].forEach.call(ed.querySelectorAll("#edLeute input"), function (cb) { cb.checked = offen.zustaendig.indexOf(cb.value) >= 0; });
    $("edLoeschen").hidden = !offen.id;
    $("edLoeschen").textContent = "Löschen";
    $("edMeldung").textContent = ""; $("edMeldung").className = "meldung";
    $("editor").showModal();
    ed.elements.titel.focus();
  }
  function schliessen() {
    $("editor").close();
  }
  $("editor").addEventListener("close", function () { offen = null; if (wartet) laden(); });
  $("edAbbrechen").addEventListener("click", schliessen);
  ed.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var felder = {
      titel: ed.elements.titel.value, beschreibung: ed.elements.beschreibung.value, status: ed.elements.status.value,
      phase: ed.elements.phase.value, wo: ed.elements.wo.value, bereich: ed.elements.bereich.value,
      gebaeude: ed.elements.gebaeude.value || null, faellig: ed.elements.faellig.value || null,
      zustaendig: [].filter.call(ed.querySelectorAll("#edLeute input"), function (cb) { return cb.checked; }).map(function (cb) { return cb.value; })
    };
    if (offen.gebaeude !== felder.gebaeude) felder.tab = null;
    var m = $("edMeldung"); m.className = "meldung"; m.textContent = "Speichere …";
    var knopf = ed.querySelector("button[type=submit]"); knopf.disabled = true;
    var arbeit;
    if (offen.id) {
      if (felder.status !== offen.status) {
        /* Neuer Status: oben in die Zielspalte */
        var dort = d.karten.filter(function (x) { return x.status === felder.status; });
        felder.rang = dort.length ? Math.min.apply(null, dort.map(function (x) { return x.rang; })) - 1000 : 0;
      }
      arbeit = speichere(offen, felder);
    } else {
      var oben = d.karten.filter(function (x) { return x.status === felder.status; });
      felder.rang = oben.length ? Math.min.apply(null, oben.map(function (x) { return x.rang; })) - 1000 : 0;
      arbeit = C.api("karten", felder).then(function (j) { d.karten.push(j.karte); if (j.commit) d.commit = j.commit; return j.karte; });
    }
    arbeit.then(function (k) {
      knopf.disabled = false; schliessen(); zeige(); toast("Gespeichert: „" + k.titel + "“");
    }).catch(function (e) {
      knopf.disabled = false;
      if (e.status === 409) {
        /* Jemand anderes war schneller: nichts überschreiben, frischen Stand zeigen */
        schliessen(); laden();
        toast("Jemand anderes hat diese Karte gerade geändert. Deine Änderung ist nicht gespeichert, das Board zeigt jetzt den neuen Stand.", true);
        return;
      }
      m.className = "meldung fehler"; m.textContent = e.message;
    });
  });
  $("edLoeschen").addEventListener("click", function () {
    var b = $("edLoeschen");
    if (b.textContent === "Löschen") { b.textContent = "Wirklich löschen?"; return; }
    var k = offen;
    C.api("karten/" + encodeURIComponent(k.id) + "/loeschen", { version: k.version }).then(function () {
      d.karten = d.karten.filter(function (x) { return x.id !== k.id; });
      schliessen(); zeige(); toast("Gelöscht: „" + k.titel + "“");
    }).catch(function (e) { $("edMeldung").className = "meldung fehler"; $("edMeldung").textContent = e.message; });
  });

  $("board").addEventListener("click", function (ev) {
    if (ev.target.closest("a")) return;
    var el = ev.target.closest(".kb-karte");
    if (el) oeffne(karteVon(el.getAttribute("data-id")));
  });
  $("board").addEventListener("keydown", function (ev) {
    var el = ev.target.closest && ev.target.closest(".kb-karte");
    if (el && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); oeffne(karteVon(el.getAttribute("data-id"))); }
  });
  $("neu").addEventListener("click", function () { oeffne(null); });

  /* ---------- Filter-Leiste ---------- */
  function optionen(sel, liste) {
    sel.insertAdjacentHTML("beforeend", liste.map(function (o) { return "<option value='" + esc(o[0]) + "'>" + esc(o[1]) + "</option>"; }).join(""));
  }
  function filterAnzeigen() {
    $("fPerson").value = F.person; $("fGebaeude").value = F.gebaeude; $("fBereich").value = F.bereich;
    $("fWo").value = F.wo; $("fPhase").value = F.phase; $("gruppiert").checked = F.gruppiert;
    $("meine").setAttribute("aria-pressed", String(!!wer && F.person === wer.id));
  }
  [["fPerson", "person"], ["fGebaeude", "gebaeude"], ["fBereich", "bereich"], ["fWo", "wo"], ["fPhase", "phase"]].forEach(function (p) {
    $(p[0]).addEventListener("change", function () { F[p[1]] = this.value; filterMerken(); filterAnzeigen(); zeige(); });
  });
  $("gruppiert").addEventListener("change", function () { F.gruppiert = this.checked; filterMerken(); zeige(); });
  $("meine").addEventListener("click", function () {
    F.person = F.person === wer.id ? "" : wer.id; filterMerken(); filterAnzeigen(); zeige();
  });

  /* ---------- Start ---------- */
  Promise.all([
    C.ich(),
    C.ladeJSON("campus/campus.json").catch(function () { return { gebaeude: [] }; }),
    C.ladeJSON("team/liste.json").catch(function () { return []; })
  ]).then(function (r) {
    wer = r[0];
    schreiben = !!wer;
    gebaeudeListe = r[1].gebaeude;
    gebaeudeListe.forEach(function (g) { gebaeude[g.id] = g; });
    return Promise.all(r[2].map(function (id) { return C.ladeJSON("team/" + id + ".json").catch(function () { return null; }); }));
  }).then(function (profile) {
    leuteListe = profile.filter(Boolean);
    leuteListe.forEach(function (p) { leute[p.id] = p; });
    optionen($("fPerson"), leuteListe.map(function (p) { return [p.id, p.anzeigename]; }));
    optionen($("fGebaeude"), gebaeudeListe.map(function (g) { return [g.id, g.name]; }));
    optionen($("fBereich"), BEREICHE.map(function (b) { return [b, b]; }));
    optionen(ed.elements.gebaeude, gebaeudeListe.map(function (g) { return [g.id, g.name]; }));
    $("edLeute").innerHTML = leuteListe.map(function (p) {
      return "<label class='haken'><input type='checkbox' value='" + esc(p.id) + "'>" + C.avatar(p, 22) + " " + esc(p.anzeigename) + "</label>";
    }).join("");
    $("neu").hidden = $("meine").hidden = !schreiben;
    $("nurLesen").hidden = schreiben;
    return laden();
  }).then(function () {
    optionen($("fPhase"), d.phasen.map(function (p) { return [p.id, p.titel]; }));
    optionen(ed.elements.phase, d.phasen.map(function (p) { return [p.id, p.titel]; }));
    filterAnzeigen();
    if (schreiben) {
      live("live");
      setInterval(nachsehen, NEU_LADEN_ALLE);
      document.addEventListener("visibilitychange", nachsehen);
    }
  }).catch(function (e) { $("stand").innerHTML = "<p class='note'>Fehler: " + esc(e.message) + "</p>"; });
})();
