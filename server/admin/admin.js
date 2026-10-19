/* ElbDetail Verwaltungsportal – ohne Abhängigkeiten */
(function () {
  "use strict";

  var app = document.getElementById("app");
  var toastEl = document.getElementById("toast");
  var ME = null;

  /* ------------------------------------------------------------ Hilfen */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function h(tag, attrs, kids) {
    var el = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k === "html") el.innerHTML = v;
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c != null) el.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return el;
  }
  var ROUTE_ID = 0;
  function api(method, path, body) {
    var rid = ROUTE_ID;
    var opt = { method: method, headers: { "Accept": "application/json" }, credentials: "same-origin" };
    if (method !== "GET") opt.headers["X-ELB-Admin"] = "1";
    if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
    return fetch("/admin/api/" + path, opt).then(function (r) {
      if (r.status === 401 && path !== "login") { ME = null; renderLogin(); throw new Error("Bitte anmelden."); }
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) { var e = new Error(j.message || ("Fehler " + r.status)); e.data = j; throw e; }
        if (method === "GET" && rid !== ROUTE_ID) return new Promise(function () {}); // Ansicht inzwischen gewechselt
        return j;
      });
    });
  }
  function toast(msg, bad) {
    toastEl.textContent = msg; toastEl.className = "toast" + (bad ? " bad" : ""); toastEl.hidden = false;
    clearTimeout(toast.t); toast.t = setTimeout(function () { toastEl.hidden = true; }, 3200);
  }
  function fail(e) { toast(e.message || "Fehler", true); }
  var STATUS = { neu: "Neu", in_bearbeitung: "In Bearbeitung", angebot_gesendet: "Angebot gesendet", termin_bestaetigt: "Termin bestätigt", erledigt: "Erledigt", abgelehnt: "Abgelehnt" };
  var VSTATUS = { offen: "Offen (unbezahlt)", bezahlt: "Bezahlt / gültig", eingeloest: "Eingelöst", storniert: "Storniert" };
  var TYP = { kontakt: "Anfrage", termin: "Termin", gutschein: "Gutschein", firma: "Firma" };
  function pill(st, map) { return '<span class="pill st-' + esc(st) + '">' + esc((map || STATUS)[st] || st) + "</span>"; }
  function deDate(iso) { if (!iso) return ""; var d = iso.slice(0, 10).split("-"); return d.length === 3 ? d[2] + "." + d[1] + "." + d[0] : iso; }
  function deDateTime(iso) { return iso ? deDate(iso) + " " + iso.slice(11, 16) : ""; }
  function fmt(n) { return String(n == null ? 0 : n).replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
  function copy(text) {
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { toast("Kopiert"); }, function () { prompt("Kopieren:", text); });
    else prompt("Kopieren:", text);
  }

  /* ------------------------------------------------------------ Login */
  function renderLogin() {
    app.className = "";
    app.innerHTML = '<div class="login"><form id="lf"><img src="/logo.svg" alt="ElbDetail"><h1>Verwaltung</h1>' +
      '<label class="f">Benutzername<input type="text" name="user" autocomplete="username" required></label>' +
      '<label class="f">Passwort<input type="password" name="password" autocomplete="current-password" required></label>' +
      '<p class="err" id="lerr"></p><button class="btn primary" type="submit">Anmelden</button></form></div>';
    var f = document.getElementById("lf");
    f.user.focus();
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      api("POST", "login", { user: f.user.value, password: f.password.value }).then(boot).catch(function (err) { document.getElementById("lerr").textContent = err.message; });
    });
  }

  /* ------------------------------------------------------------ Grundgerüst */
  var NAV = [["", "Übersicht"], ["anfragen", "Anfragen"], ["gutscheine", "Gutscheine"], ["kalender", "Kalender"], ["angebote", "Angebote"], ["inhalte", "Inhalte"], ["medien", "Fotos"], ["veroeffentlichen", "Veröffentlichen"], ["einstellungen", "Einstellungen"]];
  function shell(active) {
    app.className = "app";
    var side = '<a class="logo" href="#/"><img src="/logo.svg" alt="ElbDetail"></a>' + NAV.map(function (n) {
      return '<a class="nav' + (active === n[0] ? " active" : "") + '" href="#/' + n[0] + '">' + n[1] + (n[0] === "anfragen" && ME.open ? '<span class="badge">' + ME.open + "</span>" : "") + "</a>";
    }).join("") + '<div class="spacer"></div><div class="foot"><a href="/" target="_blank" rel="noopener">Website ansehen ↗</a><span>Angemeldet als ' + esc(ME.user) + '</span><a href="#" id="logout">Abmelden</a></div>';
    app.innerHTML = '<aside class="side" id="side">' + side + '</aside><div><div class="mobile-bar"><img src="/logo.svg" alt="ElbDetail"><button class="btn small" id="menuBtn" type="button">Menü</button></div><main class="main" id="main"></main></div>';
    document.getElementById("logout").addEventListener("click", function (e) { e.preventDefault(); api("POST", "logout", {}).then(function () { ME = null; renderLogin(); }); });
    document.getElementById("menuBtn").addEventListener("click", function () { document.getElementById("side").classList.toggle("open"); });
    document.getElementById("side").addEventListener("click", function (e) { if (e.target.closest("a.nav")) this.classList.remove("open"); });
    return document.getElementById("main");
  }

  function route() {
    if (!ME) return;
    ROUTE_ID++;
    var parts = location.hash.replace(/^#\/?/, "").split("/");
    var page = parts[0] || "";
    var main = shell(page);
    var arg = decodeURIComponent(parts.slice(1).join("/"));
    ({ "": viewDashboard, anfragen: viewRequests, gutscheine: viewVouchers, kalender: viewCalendar, angebote: viewOffers, inhalte: viewContent, medien: viewMedia, veroeffentlichen: viewPublish, einstellungen: viewSettings }[page] || viewDashboard)(main, arg);
  }
  window.addEventListener("hashchange", route);

  function boot() {
    return api("GET", "me").then(function (me) { ME = me; route(); }).catch(function () {});
  }

  /* ------------------------------------------------------------ Diagramme */
  function niceMax(v) { if (v <= 4) return 4; var p = Math.pow(10, Math.floor(Math.log10(v))); var n = v / p; return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p; }
  function barChart(series, key, unit) {
    var W = 720, H = 220, L = 34, R = 8, T = 10, B = 26;
    var max = niceMax(Math.max.apply(null, series.map(function (d) { return d[key]; }).concat([1])));
    var n = series.length, bw = (W - L - R) / n, gap = n > 60 ? 1 : 2;
    var y = function (v) { return T + (H - T - B) * (1 - v / max); };
    var svg = '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + esc(unit) + ' pro Tag"><g class="grid">';
    for (var i = 0; i <= 4; i++) { var v = max * i / 4, yy = y(v); svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + yy + '" y2="' + yy + '"/>'; }
    svg += '</g><g class="axis">';
    for (i = 0; i <= 4; i++) { v = max * i / 4; svg += '<text x="' + (L - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end">' + fmt(Math.round(v)) + "</text>"; }
    var every = Math.ceil(n / 8);
    series.forEach(function (d, k) { if ((k % every === 0 && n - 1 - k >= every / 2) || k === n - 1) svg += '<text x="' + (L + bw * k + bw / 2) + '" y="' + (H - 8) + '" text-anchor="middle">' + deDate(d.day).slice(0, 5) + "</text>"; });
    svg += "</g>";
    series.forEach(function (d, k) {
      var v = d[key], x = L + bw * k + gap / 2, w = Math.max(1, bw - gap), top = y(v), base = y(0), r = Math.min(4, w / 2, base - top);
      var path = v > 0 ? "M" + x + "," + base + "V" + (top + r) + "Q" + x + "," + top + " " + (x + r) + "," + top + "H" + (x + w - r) + "Q" + (x + w) + "," + top + " " + (x + w) + "," + (top + r) + "V" + base + "Z" : "";
      svg += '<g class="col" data-k="' + k + '"><rect class="hit" x="' + (L + bw * k) + '" y="' + T + '" width="' + bw + '" height="' + (H - T - B) + '"/>' + (path ? '<path class="bar" d="' + path + '"/>' : "") + "</g>";
    });
    svg += "</svg>";
    var wrap = h("div", { class: "chart", html: svg });
    var tip = h("div", { class: "tip", hidden: true }); wrap.appendChild(tip);
    wrap.addEventListener("mousemove", function (e) {
      var g = e.target.closest("g.col"); if (!g) { tip.hidden = true; return; }
      var d = series[+g.getAttribute("data-k")], rect = wrap.getBoundingClientRect();
      tip.hidden = false; tip.textContent = deDate(d.day) + ": " + fmt(d[key]) + " " + unit;
      tip.style.left = (e.clientX - rect.left) + "px"; tip.style.top = (e.clientY - rect.top) + "px";
    });
    wrap.addEventListener("mouseleave", function () { tip.hidden = true; });
    return wrap;
  }
  function hbars(rows, label, value, fmtLabel) {
    if (!rows.length) return h("p", { class: "empty", text: "Noch keine Daten im Zeitraum." });
    var max = Math.max.apply(null, rows.map(function (r) { return r[value]; }).concat([1]));
    var box = h("div", { class: "hbar" });
    rows.forEach(function (r) {
      box.appendChild(h("span", { class: "lbl", title: r[label], text: fmtLabel ? fmtLabel(r[label]) : r[label] }));
      box.appendChild(h("span", { class: "val", text: fmt(r[value]) }));
      var tr = h("div", { class: "track" }); tr.appendChild(h("div", { class: "fill", style: "width:" + (100 * r[value] / max).toFixed(1) + "%" })); box.appendChild(tr);
    });
    return box;
  }

  /* ------------------------------------------------------------ Übersicht */
  function viewDashboard(main) {
    var days = +(sessionStorage.getItem("elb-days") || 30);
    main.innerHTML = '<div class="head"><div><h1>Übersicht</h1><p>Besucher, Anfragen und Termine auf einen Blick. Statistik ohne Cookies, direkt auf eurem Server.</p></div><div class="filters" id="range"></div></div><div id="dash"><p class="empty">Lädt …</p></div>';
    var range = document.getElementById("range");
    [7, 30, 90].forEach(function (d) {
      range.appendChild(h("button", { class: "chip" + (d === days ? " on" : ""), type: "button", text: d + " Tage", onclick: function () { sessionStorage.setItem("elb-days", d); viewDashboard(main); } }));
    });
    api("GET", "stats?days=" + days).then(function (s) {
      var t = s.totals, p = s.previous;
      function delta(a, b) { if (!b) return '<span class="delta">–</span>'; var d = Math.round(100 * (a - b) / b); return '<span class="delta ' + (d > 0 ? "up" : d < 0 ? "down" : "") + '">' + (d > 0 ? "+" : "") + d + " % zum Vorzeitraum</span>"; }
      function kpi(label, val, prev, suffix) { return '<div class="panel kpi"><span class="label">' + label + '</span><span class="value">' + fmt(val) + (suffix || "") + "</span>" + delta(val, prev) + "</div>"; }
      var dash = document.getElementById("dash");
      dash.innerHTML = '<div class="grid g4">' + kpi("Besucher", t.visitors, p.visitors) + kpi("Anfragen über Formulare", t.leads, p.leads) +
        kpi("WhatsApp- und Anruf-Klicks", t.whatsapp + t.calls, p.whatsapp + p.calls) + kpi("Kontaktquote", t.conversion, p.conversion, " %") + "</div>";
      var row1 = h("div", { class: "grid g2", style: "margin-top:16px" });
      var c1 = h("section", { class: "panel" }, [h("h2", { text: "Besucher pro Tag" }), h("p", { class: "sub", text: "Eindeutige Besucher je Tag, ohne Bots." }), barChart(s.series, "visitors", "Besucher")]);
      var c2 = h("section", { class: "panel" }, [h("h2", { text: "Anfragen pro Tag" }), h("p", { class: "sub", text: "Kontakt-, Termin-, Gutschein- und Firmenanfragen." }), barChart(s.series, "leads", "Anfragen")]);
      row1.appendChild(c1); row1.appendChild(c2); dash.appendChild(row1);

      var up = h("section", { class: "panel" }, [h("h2", { text: "Nächste Wunschtermine" })]);
      if (!s.upcoming.length) up.appendChild(h("p", { class: "empty", text: "Keine offenen Terminwünsche." }));
      else {
        var tb = h("table", { html: "<thead><tr><th>Datum</th><th>Name</th><th>Status</th></tr></thead>" }), body = h("tbody");
        s.upcoming.forEach(function (u) { body.appendChild(h("tr", { html: '<td class="num">' + deDate(u.datum) + "</td><td>" + esc(u.name) + "</td><td>" + pill(u.status) + "</td>", onclick: function () { location.hash = "#/anfragen/" + u.ref; } })); });
        tb.appendChild(body); up.appendChild(h("div", { class: "tablewrap" }, [tb]));
      }
      var funnel = s.funnel.map(function (f) { return { l: f.step === "gesendet" ? "Anfrage gesendet" : ["", "Paket", "Fahrzeug", "Extras", "Termin", "Kontakt"][f.step], n: f.n }; });
      var row2 = h("div", { class: "grid g3", style: "margin-top:16px" }, [
        up,
        h("section", { class: "panel" }, [h("h2", { text: "Terminbuchung: Schritte" }), h("p", { class: "sub", text: "Wie viele Besucher welchen Schritt erreichen." }), hbars(funnel, "l", "n")]),
        h("section", { class: "panel" }, [h("h2", { text: "Klicks & Ereignisse" }), hbars(s.events, "name", "n")])
      ]);
      dash.appendChild(row2);
      var row3 = h("div", { class: "grid g3", style: "margin-top:16px" }, [
        h("section", { class: "panel" }, [h("h2", { text: "Meistbesuchte Seiten" }), hbars(s.pages, "path", "v")]),
        h("section", { class: "panel" }, [h("h2", { text: "Herkunft" }), h("p", { class: "sub", text: "Verweisende Website oder utm_source." }), hbars(s.sources, "src", "v")]),
        h("section", { class: "panel" }, [h("h2", { text: "Geräte" }), hbars(s.devices, "device", "v"), h("h2", { text: "Kampagnen", style: "margin-top:16px" }), hbars(s.campaigns.map(function (c) { return { l: c.c + (c.s ? " · " + c.s : ""), v: c.v }; }), "l", "v")])
      ]);
      dash.appendChild(row3);
      var tbl = h("details", { class: "panel", style: "margin-top:16px" }, [h("summary", { text: "Tageswerte als Tabelle" })]);
      var t2 = h("table", { html: "<thead><tr><th>Tag</th><th>Besucher</th><th>Seitenaufrufe</th><th>Anfragen</th></tr></thead>" }), b2 = h("tbody");
      s.series.slice().reverse().forEach(function (d) { b2.appendChild(h("tr", { html: '<td class="num">' + deDate(d.day) + '</td><td class="num">' + d.visitors + '</td><td class="num">' + d.pageviews + '</td><td class="num">' + d.leads + "</td>" })); });
      t2.appendChild(b2); tbl.appendChild(h("div", { class: "tablewrap" }, [t2])); dash.appendChild(tbl);
    }).catch(fail);
  }

  /* ------------------------------------------------------------ Anfragen */
  var reqFilter = { typ: "", status: "", q: "" };
  function viewRequests(main, ref) {
    main.innerHTML = '<div class="head"><div><h1>Anfragen</h1><p>Alle Anfragen aus Kontakt-, Termin-, Gutschein- und Firmenformular.</p></div><div class="btn-row"><a class="btn" href="/admin/api/anfragen.csv">Als CSV exportieren</a></div></div>' +
      '<div class="filters" id="ft"></div><div class="filters" id="fs"></div><div class="filters"><input type="search" id="fq" placeholder="Suche nach Name, Telefon, Vorgang …" style="max-width:360px"></div><section class="panel"><div class="tablewrap" id="list"><p class="empty">Lädt …</p></div></section>';
    var ft = document.getElementById("ft"), fs = document.getElementById("fs"), fq = document.getElementById("fq");
    fq.value = reqFilter.q;
    [["", "Alle Arten"]].concat(Object.keys(TYP).map(function (k) { return [k, TYP[k]]; })).forEach(function (o) {
      ft.appendChild(h("button", { class: "chip" + (reqFilter.typ === o[0] ? " on" : ""), type: "button", text: o[1], onclick: function () { reqFilter.typ = o[0]; viewRequests(main); } }));
    });
    var load = function () {
      var qs = "anfragen?typ=" + reqFilter.typ + "&status=" + reqFilter.status + "&q=" + encodeURIComponent(reqFilter.q);
      api("GET", qs).then(function (r) {
        fs.innerHTML = "";
        [["", "Alle Status"]].concat(Object.keys(STATUS).map(function (k) { return [k, STATUS[k]]; })).forEach(function (o) {
          var n = o[0] ? (r.counts[o[0]] || 0) : null;
          fs.appendChild(h("button", { class: "chip" + (reqFilter.status === o[0] ? " on" : ""), type: "button", html: esc(o[1]) + (n != null ? '<span class="n">' + n + "</span>" : ""), onclick: function () { reqFilter.status = o[0]; viewRequests(main); } }));
        });
        var list = document.getElementById("list");
        if (!r.items.length) { list.innerHTML = '<p class="empty">Keine Anfragen gefunden.</p>'; return; }
        var t = h("table", { html: "<thead><tr><th>Eingang</th><th>Art</th><th>Name</th><th>Details</th><th>Wunschtermin</th><th>Status</th></tr></thead>" }), b = h("tbody");
        r.items.forEach(function (it) {
          var det = it.typ === "gutschein" ? (it.wert ? it.wert + " €" : "") : it.typ === "firma" ? it.firma : (it.paket || "") + (it.preis ? " · ab " + it.preis + " €" : "");
          b.appendChild(h("tr", {
            html: '<td class="num">' + deDateTime(it.created) + '<br><span class="muted">' + esc(it.ref) + '</span></td><td><span class="typ">' + esc(TYP[it.typ]) + "</span></td><td><strong>" + esc(it.name) + '</strong><br><span class="muted">' + esc(it.telefon || it.email) + "</span></td><td>" + esc(det) + '</td><td class="num">' + deDate(it.datum) + "</td><td>" + pill(it.status) + "</td>",
            onclick: function () { location.hash = "#/anfragen/" + it.ref; }
          }));
        });
        t.appendChild(b); list.innerHTML = ""; list.appendChild(t);
      }).catch(fail);
    };
    var tq; fq.addEventListener("input", function () { clearTimeout(tq); tq = setTimeout(function () { reqFilter.q = fq.value; load(); }, 300); });
    load();
    if (ref) openRequest(ref);
  }

  function drawer(content, onclose) {
    var bg = h("div", { class: "drawer-bg" }), dr = h("div", { class: "drawer", role: "dialog", "aria-modal": "true" });
    var close = function () { bg.remove(); dr.remove(); document.removeEventListener("keydown", key); if (onclose) onclose(); };
    var key = function (e) { if (e.key === "Escape") close(); };
    bg.addEventListener("click", close); document.addEventListener("keydown", key);
    dr.appendChild(h("button", { class: "btn small close", type: "button", text: "Schließen", onclick: close }));
    dr.appendChild(content);
    document.body.appendChild(bg); document.body.appendChild(dr);
    var f = dr.querySelector("select, textarea, button:not(.close)"); if (f) f.focus();
    return close;
  }

  function openRequest(ref) {
    api("GET", "anfragen/" + ref).then(function (r) {
      var d = r.data, box = h("div", { class: "grid" });
      box.appendChild(h("div", {}, [h("span", { class: "typ", text: TYP[r.typ] + " · " + r.ref }), h("h2", { text: r.name, style: "font-size:1.6rem;margin-top:4px" }), h("p", { class: "muted", text: "Eingegangen am " + deDateTime(r.created) })]));
      var contact = h("div", { class: "btn-row" });
      if (r.telefon) { contact.appendChild(h("a", { class: "btn", href: "tel:" + r.telefon, text: "Anrufen " + r.telefon })); }
      if (r.email) contact.appendChild(h("a", { class: "btn", href: "mailto:" + r.email, text: "E-Mail schreiben" }));
      box.appendChild(contact);
      if (r.preis) box.appendChild(h("p", { class: "note info", text: "Richtpreis laut Website: ab " + r.preis + " €" }));
      if (r.gutschein) box.appendChild(h("p", { class: "note " + (r.gutschein.status === "bezahlt" ? "ok" : ""), text: "Gutscheincode " + r.gutschein.code + ": " + (VSTATUS[r.gutschein.status] || "nicht gefunden") + (r.gutschein.wert ? " · Wert " + r.gutschein.wert + " €" : "") }));
      box.appendChild(h("section", {}, [h("h3", { text: "Angaben", style: "margin-bottom:8px" }), h("pre", { class: "text", text: r.summary })]));
      var st = h("select", { id: "rst" }); Object.keys(STATUS).forEach(function (k) { st.appendChild(h("option", { value: k, text: STATUS[k], selected: k === r.status })); });
      var notes = h("textarea", { id: "rno", rows: 4, placeholder: "Interne Notizen, z. B. Angebot 189 €, Termin bestätigt für Di 9 Uhr" }); notes.value = r.notizen || "";
      box.appendChild(h("label", { class: "f" }, ["Status", st]));
      box.appendChild(h("label", { class: "f" }, ["Notizen", notes]));
      box.appendChild(h("div", { class: "btn-row" }, [h("button", { class: "btn primary", type: "button", text: "Speichern", onclick: function () {
        api("PATCH", "anfragen/" + r.ref, { status: st.value, notizen: notes.value }).then(function () { toast("Gespeichert"); ME.open = Math.max(0, ME.open - (r.status === "neu" && st.value !== "neu" ? 1 : 0)); r.status = st.value; }).catch(fail);
      } })]));
      var tpl = h("section", { class: "grid" }, [h("h3", { text: "Antworten" })]);
      var out = h("div", { class: "grid" });
      var mk = function (art, label) {
        return h("button", { class: "btn" + (art === "antwort" ? " wa" : ""), type: "button", text: label, onclick: function () {
          api("GET", "anfragen/" + r.ref + "/vorlage?art=" + art).then(function (t) {
            out.innerHTML = "";
            if (t.warning) out.appendChild(h("p", { class: "note", text: t.warning }));
            var ta = h("textarea", { rows: 6 }); ta.value = t.text; out.appendChild(ta);
            var row = h("div", { class: "btn-row" });
            if (t.whatsapp) row.appendChild(h("button", { class: "btn wa", type: "button", text: "In WhatsApp öffnen", onclick: function () { window.open("https://wa.me/" + t.whatsapp.split("wa.me/")[1].split("?")[0] + "?text=" + encodeURIComponent(ta.value), "_blank", "noopener"); } }));
            if (t.mailto) row.appendChild(h("button", { class: "btn", type: "button", text: "Als E-Mail öffnen", onclick: function () { location.href = t.mailto.split("&body=")[0] + "&body=" + encodeURIComponent(ta.value); } }));
            row.appendChild(h("button", { class: "btn", type: "button", text: "Text kopieren", onclick: function () { copy(ta.value); } }));
            out.appendChild(row);
          }).catch(fail);
        } });
      };
      tpl.appendChild(h("div", { class: "btn-row" }, [mk("antwort", "Antwort mit Angebot vorbereiten"), mk("bewertung", "Bewertung anfragen")]));
      tpl.appendChild(out);
      box.appendChild(tpl);
      if (r.typ === "gutschein") {
        box.appendChild(r.voucher ? h("p", { class: "note info", html: "Gutschein <strong>" + esc(r.voucher.code) + "</strong> · " + esc(VSTATUS[r.voucher.status]) + ' · <a href="#/gutscheine/' + r.voucher.id + '">öffnen</a>' }) :
          h("button", { class: "btn", type: "button", text: "Gutschein anlegen", onclick: function () { api("POST", "gutscheine", { fromRequest: r.ref }).then(function (x) { toast("Gutschein " + x.code + " angelegt"); }).catch(fail); } }));
      }
      box.appendChild(h("button", { class: "btn danger", type: "button", text: "Anfrage endgültig löschen", onclick: function () {
        if (!confirm("Anfrage " + r.ref + " endgültig löschen? Das kann nicht rückgängig gemacht werden.")) return;
        api("DELETE", "anfragen/" + r.ref).then(function () { toast("Gelöscht"); closeD(); }).catch(fail);
      } }));
      var closeD = drawer(box, function () { if (/^#\/anfragen\//.test(location.hash)) history.replaceState(null, "", "#/anfragen"); viewRequests(document.getElementById("main")); });
    }).catch(fail);
  }

  /* ------------------------------------------------------------ Gutscheine */
  function viewVouchers(main, id) {
    main.innerHTML = '<div class="head"><div><h1>Gutscheine</h1><p>Bestellungen aus der Website und manuell ausgestellte Gutscheine. Codes prüfen und als eingelöst markieren.</p></div></div>' +
      '<div class="grid g2"><section class="panel"><h2>Code prüfen</h2><div class="btn-row"><input type="text" id="vcode" placeholder="ELB-XXXX-XXXX" style="max-width:220px"><button class="btn primary" id="vchk" type="button">Prüfen</button></div><div id="vres" style="margin-top:10px"></div></section>' +
      '<section class="panel"><h2>Gutschein manuell anlegen</h2><form id="vnew" class="grid g2"><label class="f">Wert in €<input type="number" name="wert" min="1"></label><label class="f">oder Paket<select name="paket"><option value="">–</option><option value="frisch">Frisch &amp; Sauber</option><option value="komplett">Komplettpflege</option><option value="premium">Premium Politur</option></select></label>' +
      '<label class="f">Für<input type="text" name="fuer"></label><label class="f">Von<input type="text" name="von"></label><label class="f">Käufer<input type="text" name="kaeufer"></label><label class="f">E-Mail<input type="email" name="email"></label><div><button class="btn primary" type="submit">Anlegen</button></div></form></section></div>' +
      '<section class="panel" style="margin-top:16px"><div class="tablewrap" id="vlist"><p class="empty">Lädt …</p></div></section>';
    document.getElementById("vchk").addEventListener("click", function () {
      var code = document.getElementById("vcode").value.trim().toUpperCase(), res = document.getElementById("vres");
      api("GET", "gutscheine/pruefen?code=" + encodeURIComponent(code)).then(function (v) {
        res.innerHTML = '<p class="note ' + (v.status === "bezahlt" && !v.expired ? "ok" : "") + '">' + esc(v.code) + ": " + esc(VSTATUS[v.status]) + (v.expired ? " · abgelaufen" : "") + " · " + (v.art === "paket" ? esc(v.paket) : esc(v.wert) + " €") + " · gültig bis " + deDate(v.valid_until) + "</p>";
        if (v.status === "bezahlt") res.appendChild(h("button", { class: "btn", type: "button", text: "Als eingelöst markieren", onclick: function () { api("PATCH", "gutscheine/" + v.id, { status: "eingeloest" }).then(function () { toast("Eingelöst"); viewVouchers(main); }).catch(fail); } }));
      }).catch(function (e) { res.innerHTML = '<p class="note">' + esc(e.message) + "</p>"; });
    });
    document.getElementById("vnew").addEventListener("submit", function (e) {
      e.preventDefault(); var f = e.target;
      api("POST", "gutscheine", { wert: f.wert.value, paket: f.paket.value, fuer: f.fuer.value, von: f.von.value, kaeufer: f.kaeufer.value, email: f.email.value })
        .then(function (r) { toast("Gutschein " + r.code + " angelegt"); viewVouchers(main); }).catch(fail);
    });
    api("GET", "gutscheine").then(function (rows) {
      var list = document.getElementById("vlist");
      if (!rows.length) { list.innerHTML = '<p class="empty">Noch keine Gutscheine.</p>'; return; }
      var t = h("table", { html: "<thead><tr><th>Code</th><th>Wert</th><th>Für / Von</th><th>Käufer</th><th>Gültig bis</th><th>Status</th></tr></thead>" }), b = h("tbody");
      rows.forEach(function (v) {
        b.appendChild(h("tr", { html: '<td class="num"><strong>' + esc(v.code) + '</strong><br><span class="muted">' + deDate(v.created) + "</span></td><td>" + (v.art === "paket" ? esc(v.paket) : esc(v.wert) + " €") + "</td><td>" + esc(v.fuer) + (v.von ? " / " + esc(v.von) : "") + "</td><td>" + esc(v.kaeufer) + '<br><span class="muted">' + esc(v.email) + '</span></td><td class="num">' + deDate(v.valid_until) + "</td><td>" + pill(v.status, VSTATUS) + "</td>",
          onclick: function () { openVoucher(v, main); } }));
        if (String(v.id) === String(id)) setTimeout(function () { openVoucher(v, main); }, 0);
      });
      t.appendChild(b); list.innerHTML = ""; list.appendChild(t);
    }).catch(fail);
  }
  function openVoucher(v, main) {
    var box = h("div", { class: "grid" }, [h("span", { class: "typ", text: "Gutschein" }), h("h2", { text: v.code, style: "font-size:1.6rem" }), h("div", { html: pill(v.status, VSTATUS) })]);
    box.appendChild(h("dl", { class: "kv", html: "<dt>Wert</dt><dd>" + (v.art === "paket" ? esc(v.paket) : esc(v.wert) + " €") + "</dd><dt>Für</dt><dd>" + esc(v.fuer) + "</dd><dt>Von</dt><dd>" + esc(v.von) + "</dd><dt>Widmung</dt><dd>" + esc(v.widmung) +
      "</dd><dt>Käufer</dt><dd>" + esc(v.kaeufer) + "</dd><dt>E-Mail</dt><dd>" + esc(v.email) + "</dd><dt>Zustellung</dt><dd>" + (v.zustellung === "abholung" ? "Gedruckt abholen" : "PDF per E-Mail") + "</dd><dt>Gültig bis</dt><dd>" + deDate(v.valid_until) +
      "</dd><dt>Bezahlt</dt><dd>" + deDateTime(v.paid_at) + "</dd><dt>Eingelöst</dt><dd>" + deDateTime(v.redeemed_at) + "</dd>" }));
    box.appendChild(h("div", { class: "btn-row" }, [h("a", { class: "btn", href: v.link, target: "_blank", rel: "noopener", text: "Gutschein ansehen / drucken" }), h("button", { class: "btn", type: "button", text: "Link kopieren", onclick: function () { copy(v.link); } })]));
    var send = h("input", { type: "checkbox", checked: !!v.email });
    var actions = h("div", { class: "grid" });
    if (v.status === "offen") {
      actions.appendChild(h("label", { class: "chk" }, [send, "Gutschein-Link per E-Mail an Käufer senden"]));
      actions.appendChild(h("button", { class: "btn primary", type: "button", text: "Zahlung eingegangen: als bezahlt markieren", onclick: function () {
        api("PATCH", "gutscheine/" + v.id, { status: "bezahlt", sendMail: send.checked }).then(function (r) { toast(r.mailSent ? "Bezahlt, E-Mail gesendet" : "Als bezahlt markiert"); close(); }).catch(fail);
      } }));
    }
    if (v.status === "bezahlt") actions.appendChild(h("button", { class: "btn primary", type: "button", text: "Als eingelöst markieren", onclick: function () { api("PATCH", "gutscheine/" + v.id, { status: "eingeloest" }).then(function () { toast("Eingelöst"); close(); }).catch(fail); } }));
    if (v.status !== "storniert" && v.status !== "eingeloest") actions.appendChild(h("button", { class: "btn danger", type: "button", text: "Stornieren", onclick: function () { if (confirm("Gutschein stornieren?")) api("PATCH", "gutscheine/" + v.id, { status: "storniert" }).then(function () { toast("Storniert"); close(); }).catch(fail); } }));
    box.appendChild(actions);
    var close = drawer(box, function () { viewVouchers(main); });
  }

  /* ------------------------------------------------------------ Kalender */
  var calMonth = null;
  function viewCalendar(main) {
    var t = new Date(); if (!calMonth) calMonth = new Date(t.getFullYear(), t.getMonth(), 1);
    main.innerHTML = '<div class="head"><div><h1>Kalender</h1><p>Gesperrte Tage sind in der Online-Terminanfrage nicht wählbar. Zahlen zeigen Terminwünsche pro Tag.</p></div></div><div class="grid g2" id="calwrap"><p class="empty">Lädt …</p></div>';
    api("GET", "kalender").then(function (c) {
      var blocked = {}; c.blocked.forEach(function (b) { blocked[b.day] = b.reason || "gesperrt"; });
      var req = {}; c.requests.forEach(function (r) { req[r.day] = r; });
      var wrap = document.getElementById("calwrap"); wrap.innerHTML = "";
      var iso = function (d) { return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
      var todayIso = iso(t);
      var reason = h("input", { type: "text", placeholder: "Grund (optional), z. B. Urlaub" });
      var panel = h("section", { class: "panel" });
      var title = calMonth.toLocaleDateString("de-DE", { month: "long", year: "numeric" });
      panel.appendChild(h("div", { class: "head", style: "margin-bottom:10px" }, [h("h2", { text: title }), h("div", { class: "btn-row" }, [
        h("button", { class: "btn small", type: "button", text: "‹ Vorher", onclick: function () { calMonth = new Date(calMonth.getFullYear(), calMonth.getMonth() - 1, 1); viewCalendar(main); } }),
        h("button", { class: "btn small", type: "button", text: "Weiter ›", onclick: function () { calMonth = new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 1); viewCalendar(main); } })])]));
      var grid = h("div", { class: "cal" });
      ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"].forEach(function (d) { grid.appendChild(h("div", { class: "dow", text: d })); });
      var first = (calMonth.getDay() + 6) % 7;
      for (var i = 0; i < first; i++) grid.appendChild(h("div", { class: "pad" }));
      var days = new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 0).getDate();
      for (var d = 1; d <= days; d++) {
        (function (date) {
          var di = iso(date), past = di < todayIso, closed = c.closedWeekdays.indexOf(date.getDay()) !== -1, r = req[di];
          var cls = "day" + (past ? " past" : "") + (closed ? " closed" : "") + (blocked[di] ? " blocked" : "") + (di === todayIso ? " today" : "");
          grid.appendChild(h("button", { class: cls, type: "button", title: blocked[di] || (closed ? "Ruhetag" : ""), disabled: past,
            html: '<span class="d">' + date.getDate() + "</span>" + (r ? '<span class="req">' + r.n + " Wunsch" + (r.n > 1 ? "e" : "") + (r.ok ? " · " + r.ok + " best." : "") + "</span>" : ""),
            onclick: function () {
              (blocked[di] ? api("DELETE", "kalender", { day: di }) : api("POST", "kalender", { day: di, reason: reason.value })).then(function () { viewCalendar(main); }).catch(fail);
            } }));
        })(new Date(calMonth.getFullYear(), calMonth.getMonth(), d));
      }
      panel.appendChild(grid);
      panel.appendChild(h("label", { class: "f", style: "margin-top:12px" }, ["Grund für neu gesperrte Tage", reason]));
      wrap.appendChild(panel);
      var side = h("section", { class: "panel" }, [h("h2", { text: "Ruhetage" }), h("p", { class: "sub", text: "An diesen Wochentagen ist grundsätzlich kein Termin möglich." })]);
      var wd = h("div", { class: "grid" });
      [[1, "Montag"], [2, "Dienstag"], [3, "Mittwoch"], [4, "Donnerstag"], [5, "Freitag"], [6, "Samstag"], [0, "Sonntag"]].forEach(function (x) {
        wd.appendChild(h("label", { class: "chk" }, [h("input", { type: "checkbox", value: x[0], checked: c.closedWeekdays.indexOf(x[0]) !== -1 }), x[1]]));
      });
      side.appendChild(wd);
      side.appendChild(h("button", { class: "btn primary", type: "button", style: "margin-top:12px", text: "Ruhetage speichern", onclick: function () {
        var vals = Array.prototype.map.call(wd.querySelectorAll("input:checked"), function (i) { return +i.value; });
        api("PUT", "kalender", { closedWeekdays: vals }).then(function () { toast("Gespeichert"); viewCalendar(main); }).catch(fail);
      } }));
      side.appendChild(h("h2", { text: "Auslastung", style: "margin-top:20px" }));
      side.appendChild(h("p", { class: "sub", text: "Ab so vielen bestätigten Terminen gilt ein Tag als ausgebucht. Die Website zeigt dann automatisch den nächsten freien Tag (aktuell: " + (c.nextFree ? deDate(c.nextFree) : "keiner in Sicht") + "). 0 = Auslastung nicht berücksichtigen." }));
      var cap = h("input", { type: "number", min: 0, max: 20, value: c.dailyCapacity });
      var lead = h("input", { type: "number", min: 0, max: 30, value: c.leadDays });
      var ker = h("input", { type: "checkbox", checked: c.keramikExclusive !== false });
      side.appendChild(h("div", { class: "grid g2" }, [h("label", { class: "f" }, ["Fahrzeuge pro Tag", cap]), h("label", { class: "f" }, ["Vorlauf in Tagen (1 = frühestens morgen)", lead])]));
      side.appendChild(h("label", { class: "chk", style: "margin-top:8px" }, [ker, "Keramikversiegelung belegt den ganzen Tag (nur 1 Fahrzeug)"]));
      side.appendChild(h("button", { class: "btn", type: "button", style: "margin-top:10px", text: "Auslastung speichern", onclick: function () {
        api("PUT", "kalender", { dailyCapacity: +cap.value, leadDays: +lead.value, keramikExclusive: ker.checked }).then(function () { toast("Gespeichert"); viewCalendar(main); }).catch(fail);
      } }));
      var up = c.blocked.filter(function (b) { return b.day >= todayIso; });
      side.appendChild(h("h2", { text: "Gesperrte Tage", style: "margin-top:20px" }));
      side.appendChild(up.length ? h("ul", { html: up.map(function (b) { return "<li>" + deDate(b.day) + (b.reason ? " · " + esc(b.reason) : "") + "</li>"; }).join("") }) : h("p", { class: "empty", text: "Keine Tage gesperrt." }));
      wrap.appendChild(side);
    }).catch(fail);
  }

  /* ------------------------------------------------------------ Inhalte (JSON- und Markdown-Editor) */
  var KEYS = { name: "Name", tagline: "Unterzeile", url: "Website-Adresse", phone: "Telefon (international, ohne Leerzeichen)", phoneDisplay: "Telefon (Anzeige)", phoneIntl: "Telefon (Anzeige international)",
    whatsapp: "WhatsApp-Nummer (nur Ziffern, mit 49)", email: "E-Mail", address: "Adresse", street: "Straße", zip: "PLZ", city: "Ort", region: "Bundesland", country: "Land (Kürzel)",
    openingHours: "Öffnungszeiten", days: "Wochentage (englisch, für Google)", opens: "Öffnet", closes: "Schließt", text: "Text", detail: "Detail", rating: "Google-Bewertung", value: "Wert",
    count: "Anzahl", asOf: "Stand", googleMapsUrl: "Google-Maps-Link", googleReviewUrl: "Google-Bewertungslink (für Bewertungsanfragen)", social: "Social Media", areas: "Einzugsgebiet",
    legal: "Rechtliches (Impressum & Datenschutz)", owner: "Inhaber:in / Firma laut Gewerbeanmeldung", vatId: "USt-IdNr.", responsible: "Verantwortlich nach § 18 MStV", mailProvider: "E-Mail-Anbieter (Name, Anschrift)",
    hosting: "Rechenzentrum", vouchers: "Gutscheine", amounts: "Betragsvorschläge", minAmount: "Mindestbetrag", maxAmount: "Höchstbetrag", stand: "Stand (Text)", standIso: "Stand (Datum JJJJ-MM-TT)",
    classes: "Fahrzeugklassen", key: "Schlüssel (nicht ändern)", short: "Kurzname", examples: "Beispiele", packages: "Pakete", for: "Für wen", duration: "Dauer", featured: "Hervorheben",
    prices: "Richtpreise je Klasse (€)", kompakt: "Kompakt", mittel: "Limousine / Kombi", suv: "SUV / Van", sport: "Sport / Premium", onRequest: "Preis nur auf Anfrage", features: "Leistungen", included: "Enthalten", extras: "Einzelleistungen", compare: "Vergleichstabelle",
    label: "Bezeichnung", frisch: "Frisch & Sauber", komplett: "Komplettpflege", premium: "Premium Politur", note: "Hinweistext", featuredQuote: "Hervorgehobenes Zitat", items: "Einträge", source: "Quelle",
    q: "Frage", a: "Antwort", title: "Titel", sub: "Untertitel", before: "Foto vorher (Dateiname)", after: "Foto nachher (Dateiname)", alt: "Bildbeschreibung", slug: "Adresse (nicht ändern)",
    order: "Reihenfolge", teaser: "Kurzbeschreibung", seoTitle: "Seitentitel für Google (max. 60 Zeichen)", description: "Beschreibung für Google (120–155 Zeichen, Preise als {ab:frisch}, {ab:komplett}, {ab:premium})", h1: "Überschrift (*kursiv* = blau)",
    lead: "Einleitung (**fett** möglich)", facts: "Kennzahlen", package: "Passendes Paket (Schlüssel)", intro: "Haupttext (Markdown)", includes: "Leistungsumfang", steps: "Ablauf", faq: "Häufige Fragen",
    related: "Verwandte Leistungen (Adressen)", date: "Veröffentlicht (JJJJ-MM-TT)", updated: "Aktualisiert (JJJJ-MM-TT)", category: "Kategorie", readingTime: "Lesezeit (Min.)", excerpt: "Teaser",
    about: "Über uns (Inhaber-Karte auf der Startseite, erscheint wenn Name und Text gefüllt sind)", role: "Rolle", fullName: "Vor- und Nachname (für strukturierte Daten)", photo: "Foto (Dateiname aus Fotos)", since: "Seit (z. B. 2023)",
    verification: "Bestätigungscodes für Google Search Console / Bing", google: "Google (nur der Code aus dem Meta-Tag)", bing: "Bing (nur der Code)",
    active: "Aktiv (auf der Website zeigen)", highlight: "Auf der Startseite hervorheben", icon: "Symbol (snow, gift, spark, brief, tag, key)", badge: "Etikett", price: "Preisangabe", validUntil: "Gültig bis (JJJJ-MM-TT, leer = unbegrenzt)", ctaLabel: "Button-Text", ctaHref: "Button-Ziel (z. B. termin.html)",
    subtitle: "Untertitel", kind: "Art (z. B. Zertifikat)", issuer: "Aussteller", issuerUrl: "Website des Ausstellers", place: "Ort", date: "Datum (JJJJ-MM-TT)", benefit: "Ihr Vorteil (ein Satz)", image: "Bild (Dateiname aus Fotos)",
    references: "Referenzen (Firmenkunden, nur mit Erlaubnis)", type: "Branche", logo: "Logo-Datei (z. B. ref-firma.svg)", url: "Website (https://…)",
    analytics: "Google Analytics (lädt nur nach Einwilligung)", ga4: "Mess-ID Google Analytics 4 (G-…), leer = aus", hinweis: "Hinweis", hostingLocation: "Serverstandort (Stadt)",
    smallBusiness: "Kleinunternehmer nach § 19 UStG (keine Umsatzsteuer)", partners: "Partner & Qualifikationen", pickup: "Abhol- und Bringservice",
    freeRadiusKm: "Kostenloser Umkreis in km (0 = nicht anzeigen)", bookAs: "Anfrage-Art in der Buchung (Schlüssel)",
    service: "Passende Leistung (Adresse)", summary: "Das Wichtigste in Kürze", draft: "Entwurf (nicht veröffentlichen)", city_: "Stadtteile" };
  function lbl(k) { return KEYS[k] || String(k).replace(/([A-Z])/g, " $1").replace(/^./, function (c) { return c.toUpperCase(); }); }
  function blank(tpl) {
    if (Array.isArray(tpl)) return [];
    if (tpl && typeof tpl === "object") { var o = {}; Object.keys(tpl).forEach(function (k) { o[k] = blank(tpl[k]); }); return o; }
    return typeof tpl === "number" ? 0 : typeof tpl === "boolean" ? false : "";
  }
  function editor(obj, onchange) {
    function field(parent, key, holder) {
      var v = holder[key];
      if (Array.isArray(v)) return parent.appendChild(arrayEditor(key, holder));
      if (v && typeof v === "object") {
        var fs = h("fieldset", {}, [h("legend", { text: lbl(key) })]);
        Object.keys(v).forEach(function (k) { field(fs, k, v); });
        return parent.appendChild(fs);
      }
      var input;
      if (typeof v === "boolean") {
        input = h("input", { type: "checkbox", checked: v, onchange: function () { holder[key] = input.checked; onchange(); } });
        return parent.appendChild(h("label", { class: "chk" }, [input, lbl(key)]));
      }
      if (typeof v === "number") input = h("input", { type: "number", value: v, step: "any", oninput: function () { holder[key] = input.value === "" ? 0 : +input.value; onchange(); } });
      else if (String(v).length > 90 || String(v).indexOf("\n") !== -1 || key === "intro" || key === "a" || key === "text") {
        input = h("textarea", { rows: key === "intro" ? 14 : Math.min(8, Math.max(3, Math.ceil(String(v).length / 90))), oninput: function () { holder[key] = input.value; onchange(); } }); input.value = v;
      } else {
        input = h("input", { type: "text", value: v, oninput: function () { holder[key] = input.value; onchange(); } });
        if (key === "before" || key === "after" || key === "photo") input.setAttribute("list", "media-names");
      }
      var hint = key === "seoTitle" || key === "description" ? h("small", { text: String(v).length + " Zeichen" }) : null;
      if (hint) input.addEventListener("input", function () { hint.textContent = input.value.length + " Zeichen"; });
      return parent.appendChild(h("label", { class: "f" }, [lbl(key), hint, input]));
    }
    function arrayEditor(key, holder) {
      var arr = holder[key], fs = h("fieldset", {}, [h("legend", { text: lbl(key) + " (" + arr.length + ")" })]);
      arr.forEach(function (item, i) {
        var box = h("div", { class: "arr-item" });
        var tools = h("div", { class: "arr-tools" }, [
          h("button", { class: "btn small", type: "button", text: "↑", title: "nach oben", disabled: i === 0, onclick: function () { arr.splice(i - 1, 0, arr.splice(i, 1)[0]); rerender(); } }),
          h("button", { class: "btn small", type: "button", text: "↓", title: "nach unten", disabled: i === arr.length - 1, onclick: function () { arr.splice(i + 1, 0, arr.splice(i, 1)[0]); rerender(); } }),
          h("button", { class: "btn small danger", type: "button", text: "Entfernen", onclick: function () { arr.splice(i, 1); rerender(); } })]);
        box.appendChild(tools);
        if (item && typeof item === "object" && !Array.isArray(item)) Object.keys(item).forEach(function (k) { field(box, k, item); });
        else { var wrapObj = { v: item }; var proxy = {}; Object.defineProperty(proxy, "v", { get: function () { return arr[i]; }, set: function (x) { arr[i] = x; }, enumerable: true }); KEYS.v = "Eintrag " + (i + 1); field(box, "v", proxy); }
        fs.appendChild(box);
      });
      fs.appendChild(h("button", { class: "btn small", type: "button", text: "+ Eintrag hinzufügen", onclick: function () { arr.push(arr.length ? blank(arr[0]) : ""); rerender(); } }));
      function rerender() { onchange(); fs.replaceWith(arrayEditor(key, holder)); }
      return fs;
    }
    var root = h("div", { class: "je" });
    Object.keys(obj).forEach(function (k) { field(root, k, obj); });
    return root;
  }

  function viewContent(main, path) {
    main.innerHTML = '<div class="head"><div><h1>Inhalte</h1><p>Preise, Texte, Bewertungen, Leistungsseiten und Ratgeber bearbeiten. Änderungen werden nach „Speichern &amp; veröffentlichen“ live.</p></div></div><div class="split"><nav class="panel filelist" id="files"></nav><section class="panel" id="ed"><p class="empty">Links eine Datei auswählen.</p></section></div>';
    api("GET", "inhalte").then(function (files) {
      var nav = document.getElementById("files"), groups = {};
      files.forEach(function (f) { (groups[f.group] = groups[f.group] || []).push(f); });
      Object.keys(groups).forEach(function (g) {
        nav.appendChild(h("h3", { text: g }));
        groups[g].forEach(function (f) { nav.appendChild(h("a", { href: "#/inhalte/" + f.path, class: f.path === path ? "on" : "", text: f.label })); });
      });
      nav.appendChild(h("button", { class: "btn small", type: "button", style: "margin-top:10px", text: "+ Neuer Ratgeber-Artikel", onclick: function () {
        var t = prompt("Titel des neuen Artikels:"); if (!t) return;
        api("POST", "inhalte/neuer-artikel", { title: t }).then(function (r) { location.hash = "#/inhalte/" + r.path; }).catch(fail);
      } }));
    }).catch(fail);
    if (!path) return;
    var ed = document.getElementById("ed");
    api("GET", "medien").then(function (m) {
      var dl = h("datalist", { id: "media-names" }); m.forEach(function (x) { dl.appendChild(h("option", { value: x.name })); }); document.body.appendChild(dl);
    }).catch(function () {});
    api("GET", "inhalte/" + path).then(function (doc) {
      var dirty = false, mark = function () { dirty = true; status.textContent = "Ungespeicherte Änderungen"; };
      var status = h("span", { class: "muted" });
      var save = function (andPublish) {
        var body = doc.kind === "md" ? { meta: doc.meta, body: bodyTa.value } : { data: doc.data };
        return api("PUT", "inhalte/" + path, body).then(function () {
          dirty = false; status.textContent = "Gespeichert";
          if (andPublish) { status.textContent = "Wird veröffentlicht …"; return api("POST", "veroeffentlichen", {}).then(function (r) { status.textContent = r.ok ? "Gespeichert und veröffentlicht" : "Fehler beim Veröffentlichen"; toast(r.ok ? "Live auf der Website" : "Veröffentlichen fehlgeschlagen", !r.ok); }); }
          toast("Gespeichert");
        }).catch(fail);
      };
      var bar = h("div", { class: "btn-row", style: "position:sticky;top:0;background:#fff;padding:6px 0 12px;z-index:2;align-items:center" }, [
        h("button", { class: "btn", type: "button", text: "Speichern", onclick: function () { save(false); } }),
        h("button", { class: "btn primary", type: "button", text: "Speichern & veröffentlichen", onclick: function () { save(true); } }), status]);
      ed.innerHTML = ""; ed.appendChild(h("h2", { text: path })); ed.appendChild(bar);
      var bodyTa = null;
      if (doc.kind === "md") {
        ed.appendChild(editor(doc.meta, mark));
        bodyTa = h("textarea", { class: "code", oninput: function () { mark(); schedule(); } }); bodyTa.value = doc.body;
        var prev = h("div", { class: "preview" });
        var tm; var schedule = function () { clearTimeout(tm); tm = setTimeout(function () { api("POST", "vorschau", { md: bodyTa.value }).then(function (r) { prev.innerHTML = r.html; }).catch(function () {}); }, 400); };
        ed.appendChild(h("h3", { text: "Artikeltext", style: "margin:16px 0 4px" }));
        ed.appendChild(h("p", { class: "muted", html: "Markdown: <code>## Überschrift</code>, <code>**fett**</code>, <code>- Liste</code>, <code>[Link](/termin.html)</code>, Tabellen mit <code>| a | b |</code>." }));
        ed.appendChild(h("div", { class: "md-grid" }, [bodyTa, prev]));
        schedule();
        if (path.indexOf("ratgeber/") === 0) ed.appendChild(h("button", { class: "btn danger", type: "button", style: "margin-top:14px", text: "Artikel löschen", onclick: function () {
          if (confirm("Artikel löschen? Eine Sicherung bleibt auf dem Server.")) api("DELETE", "inhalte/" + path).then(function () { toast("Gelöscht"); location.hash = "#/inhalte"; }).catch(fail);
        } }));
      } else ed.appendChild(editor(doc.data, mark));
      window.onbeforeunload = function () { return dirty ? "Ungespeicherte Änderungen" : undefined; };
    }).catch(fail);
  }

  /* ------------------------------------------------------------ Fotos */
  function viewMedia(main) {
    main.innerHTML = '<div class="head"><div><h1>Fotos</h1><p>Vorher-/Nachher-Fotos hochladen (JPG, PNG oder WebP, Format 4:3). Danach unter Inhalte → Vorher/Nachher-Galerie den Dateinamen eintragen und veröffentlichen. Die Website erzeugt automatisch optimierte Größen.</p></div></div>' +
      '<section class="panel"><div class="drop" id="drop"><p><strong>Fotos hierher ziehen</strong> oder</p><input type="file" id="file" accept="image/jpeg,image/png,image/webp" multiple></div><div class="media-grid" id="mg" style="margin-top:16px"></div></section>';
    var load = function () {
      api("GET", "medien").then(function (m) {
        var g = document.getElementById("mg"); g.innerHTML = m.length ? "" : '<p class="empty">Noch keine Fotos hochgeladen.</p>';
        m.forEach(function (x) {
          g.appendChild(h("figure", {}, [h("img", { src: "/admin/api/medien/" + encodeURIComponent(x.name), alt: x.name, loading: "lazy" }), h("figcaption", {}, [h("strong", { text: x.name }), h("span", { class: "muted", text: Math.round(x.size / 1024) + " KB" }),
            h("div", { class: "btn-row" }, [h("button", { class: "btn small", type: "button", text: "Name kopieren", onclick: function () { copy(x.name); } }),
              h("button", { class: "btn small danger", type: "button", text: "Löschen", onclick: function () { if (confirm(x.name + " löschen?")) api("DELETE", "medien/" + encodeURIComponent(x.name)).then(load).catch(fail); } })])])]));
        });
      }).catch(fail);
    };
    var upload = function (files) {
      Array.prototype.forEach.call(files, function (f) {
        if (f.size > 15 * 1024 * 1024) { toast(f.name + ": größer als 15 MB", true); return; }
        var rd = new FileReader();
        rd.onload = function () { api("POST", "medien", { name: f.name, data: rd.result }).then(function (r) { toast(r.name + " hochgeladen"); load(); }).catch(fail); };
        rd.readAsDataURL(f);
      });
    };
    document.getElementById("file").addEventListener("change", function (e) { upload(e.target.files); });
    var drop = document.getElementById("drop");
    drop.addEventListener("dragover", function (e) { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", function () { drop.classList.remove("over"); });
    drop.addEventListener("drop", function (e) { e.preventDefault(); drop.classList.remove("over"); upload(e.dataTransfer.files); });
    load();
  }

  /* ------------------------------------------------------------ Angebote */
  var OFFER_STATE = { aktiv: "Live", geplant: "Geplant", abgelaufen: "Abgelaufen", aus: "Ausgeblendet" };
  var OFFER_ICON = { spark: "✦ Funkeln", snow: "❄ Schneeflocke", gift: "🎁 Geschenk", tag: "🏷 Preisschild", brief: "💼 Aktentasche", key: "🔑 Schlüssel", shield: "🛡 Schild", star: "★ Stern" };
  var OFFER_TARGETS = [["termin.html", "Terminanfrage"], ["termin.html?paket=komplett", "Terminanfrage: Komplettpflege"], ["termin.html?paket=premium", "Terminanfrage: Premium Politur"],
    ["termin.html?paket=keramik", "Terminanfrage: Keramikversiegelung"], ["gutscheine.html", "Gutscheine"], ["elbdetail-care.html", "ElbDetail Care"],
    ["firmenkunden.html#firmenanfrage", "Firmenanfrage"], ["aktion/winterschutz.html", "Winter-Lackschutz"], ["kontakt.html", "Kontakt"], ["", "Eigene Adresse …"]];
  function offerPeriod(o) {
    if (o.validFrom && o.validUntil) return deDate(o.validFrom) + " bis " + deDate(o.validUntil);
    if (o.validFrom) return "ab " + deDate(o.validFrom);
    if (o.validUntil) return "bis " + deDate(o.validUntil);
    return "ohne Enddatum";
  }
  function offerSaved(r) {
    if (r.published) toast("Gespeichert und auf der Website live");
    else toast("Gespeichert, aber das Veröffentlichen ist fehlgeschlagen. Bitte unter „Veröffentlichen“ erneut versuchen.", true);
  }
  function viewOffers(main, arg) {
    main.innerHTML = '<div class="head"><div><h1>Angebote</h1><p>Aktionen und Angebote für die Website. Live-Angebote erscheinen auf der Startseite (hervorgehobene zuerst, bis zu drei) und auf der Seite „Angebote“. Mit Start- und Enddatum gehen sie automatisch online und wieder offline. Jede Änderung ist sofort live.</p></div>' +
      '<div class="btn-row"><a class="btn" href="/angebote.html" target="_blank" rel="noopener">Seite ansehen ↗</a><button class="btn primary" type="button" id="newOffer">+ Neues Angebot</button></div></div><div id="ol"><p class="empty">Lädt …</p></div>';
    var data = null;
    var render = function () {
      var box = document.getElementById("ol"); box.innerHTML = "";
      if (!data.items.length) { box.appendChild(h("section", { class: "panel" }, [h("p", { class: "empty", text: "Noch keine Angebote. Legen Sie Ihr erstes Angebot an." })])); return; }
      data.items.forEach(function (o, i) {
        var move = function (dir) {
          var ids = data.items.map(function (x) { return x.id; }), j = i + dir; if (j < 0 || j >= ids.length) return;
          var t = ids[i]; ids[i] = ids[j]; ids[j] = t;
          api("PUT", "angebote/reihenfolge", { ids: ids }).then(function (r) { data = r; render(); offerSaved(r); }).catch(fail);
        };
        var toggle = function () {
          var body = Object.assign({}, o, { active: !o.active }); delete body.state;
          api("PUT", "angebote/" + o.id, body).then(function (r) { data = r; render(); offerSaved(r); }).catch(fail);
        };
        box.appendChild(h("section", { class: "panel offer-row" + (o.state === "aktiv" ? "" : " is-off") }, [
          o.image ? h("img", { class: "offer-thumb", src: "/admin/api/medien/" + encodeURIComponent(o.image), alt: "" }) : h("div", { class: "offer-thumb empty-thumb", text: (OFFER_ICON[o.icon] || "✦").split(" ")[0] }),
          h("div", { class: "offer-info" }, [
            h("div", { class: "offer-line" }, [h("strong", { text: o.title }), o.highlight ? h("span", { class: "pill st-neu", text: "Startseite oben" }) : null, h("span", { class: "pill st-" + o.state, text: OFFER_STATE[o.state] || o.state })]),
            h("p", { class: "muted", text: [o.badge, o.priceShown || o.price, offerPeriod(o)].filter(Boolean).join(" · ") })]),
          h("div", { class: "btn-row" }, [
            h("button", { class: "btn small", type: "button", text: "↑", title: "Nach oben", disabled: i === 0, onclick: function () { move(-1); } }),
            h("button", { class: "btn small", type: "button", text: "↓", title: "Nach unten", disabled: i === data.items.length - 1, onclick: function () { move(1); } }),
            h("button", { class: "btn small", type: "button", text: o.active ? "Ausblenden" : "Einblenden", onclick: toggle }),
            h("button", { class: "btn small primary", type: "button", text: "Bearbeiten", onclick: function () { editOffer(o); } }),
            h("button", { class: "btn small danger", type: "button", text: "Löschen", onclick: function () {
              if (confirm("Angebot „" + o.title + "“ löschen? Es verschwindet sofort von der Website.")) api("DELETE", "angebote/" + o.id).then(function (r) { data = r; render(); offerSaved(r); }).catch(fail);
            } })])]));
      });
    };
    var editOffer = function (o) {
      o = o || { title: "", badge: "", text: "", price: "", validFrom: "", validUntil: "", ctaLabel: "Jetzt anfragen", ctaHref: "termin.html", icon: "spark", image: "", imageAlt: "", active: true, highlight: false };
      var isNew = !o.id;
      var inp = function (name, attrs) { var el = h("input", Object.assign({ name: name, value: o[name] || "" }, attrs || {})); el.value = o[name] || ""; return el; };
      var f = {
        title: inp("title", { maxlength: 80, required: true, placeholder: "z. B. Frühjahrs-Check" }),
        badge: inp("badge", { maxlength: 30, placeholder: "z. B. Frühlings-Aktion" }),
        text: h("textarea", { name: "text", rows: 4, maxlength: 400, placeholder: "Was ist enthalten, für wen lohnt es sich?" }),
        price: inp("price", { maxlength: 60, placeholder: "z. B. ab 149 € oder 10 % auf die Komplettpflege" }),
        validFrom: inp("validFrom", { type: "date" }), validUntil: inp("validUntil", { type: "date" }),
        ctaLabel: inp("ctaLabel", { maxlength: 40 }),
        target: h("select", {}), custom: inp("ctaHref", { maxlength: 300, placeholder: "z. B. leistungen/lackpolitur-celle.html oder https://…" }),
        icon: h("select", {}), imageAlt: inp("imageAlt", { maxlength: 140, placeholder: "Was ist auf dem Bild zu sehen?" }),
        active: h("input", { type: "checkbox", checked: o.active !== false }), highlight: h("input", { type: "checkbox", checked: !!o.highlight })
      };
      f.text.value = o.text || "";
      OFFER_TARGETS.forEach(function (t) { f.target.appendChild(h("option", { value: t[0], text: t[1] })); });
      var known = OFFER_TARGETS.some(function (t) { return t[0] && t[0] === o.ctaHref; });
      f.target.value = known ? o.ctaHref : "";
      f.custom.hidden = known;
      Object.keys(OFFER_ICON).forEach(function (k) { f.icon.appendChild(h("option", { value: k, text: OFFER_ICON[k] })); });
      f.icon.value = o.icon || "spark";
      var image = o.image || "";
      var imgPrev = h("div", { class: "offer-img-prev" });
      var fileIn = h("input", { type: "file", accept: "image/jpeg,image/png,image/webp" });
      var showImg = function () {
        imgPrev.innerHTML = "";
        if (image) imgPrev.appendChild(h("img", { src: "/admin/api/medien/" + encodeURIComponent(image), alt: "" }));
        imgPrev.appendChild(h("div", { class: "btn-row" }, [h("label", { class: "btn small" }, [image ? "Bild ersetzen" : "Bild hochladen", fileIn]),
          image ? h("button", { class: "btn small danger", type: "button", text: "Bild entfernen", onclick: function () { image = ""; showImg(); preview(); } }) : null]));
        imgPrev.appendChild(h("small", { class: "muted", text: "Optional. Querformat (16:9), JPG/PNG/WebP, max. 15 MB. Nur eigene Fotos oder Bilder mit Nutzungsrecht." }));
      };
      fileIn.addEventListener("change", function () {
        var file = fileIn.files[0]; if (!file) return;
        if (file.size > 15 * 1024 * 1024) { toast("Bild größer als 15 MB", true); return; }
        var rd = new FileReader();
        rd.onload = function () {
          var base = (file.name.replace(/\.[^.]+$/, "") || "angebot").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "angebot";
          var ext = (file.type === "image/png" ? "png" : file.type === "image/webp" ? "webp" : "jpg");
          api("POST", "medien", { name: "angebot-" + base + "-" + Date.now().toString(36) + "." + ext, data: rd.result }).then(function (r) { image = r.name; showImg(); preview(); toast("Bild hochgeladen"); }).catch(fail);
        };
        rd.readAsDataURL(file);
      });
      var card = h("article", { class: "offer-prev" });
      var preview = function () {
        var g = function (k) { return (f[k].value || "").trim(); };
        card.className = "offer-prev" + (f.highlight.checked ? " is-highlight" : "");
        card.innerHTML = (image ? '<img src="/admin/api/medien/' + encodeURIComponent(image) + '" alt="">' : "") +
          '<div class="op-top"><span class="op-icon">' + esc((OFFER_ICON[f.icon.value] || "✦").split(" ")[0]) + "</span>" + (g("badge") ? '<span class="op-badge">' + esc(g("badge")) + "</span>" : "") + "</div>" +
          "<h3>" + esc(g("title") || "Titel des Angebots") + "</h3><p>" + esc(g("text") || "Beschreibung") + "</p>" +
          '<div class="op-foot"><strong>' + esc(g("price")) + "</strong>" + (g("validUntil") ? "<span>gültig bis " + deDate(g("validUntil")) + "</span>" : "") + "</div>" +
          '<span class="op-btn">' + esc(g("ctaLabel") || "Jetzt anfragen") + "</span>";
      };
      var errBox = h("div", {});
      var form = h("form", { class: "grid offer-form" }, [
        h("label", { class: "f" }, ["Titel *", f.title]),
        h("div", { class: "grid g2" }, [h("label", { class: "f" }, ["Etikett", f.badge]), h("label", { class: "f" }, ["Symbol", f.icon])]),
        h("label", { class: "f" }, ["Beschreibung ", h("small", { text: "kurz und konkret, max. 400 Zeichen" }), f.text]),
        h("label", { class: "f" }, ["Preisangabe ", h("small", { text: "Endpreis angeben, z. B. „ab 149 €“. Keine erfundenen Streichpreise." }), f.price]),
        h("div", { class: "grid g2" }, [h("label", { class: "f" }, ["Gültig ab ", h("small", { text: "leer = sofort" }), f.validFrom]), h("label", { class: "f" }, ["Gültig bis ", h("small", { text: "leer = unbegrenzt" }), f.validUntil])]),
        h("div", { class: "grid g2" }, [h("label", { class: "f" }, ["Button-Text", f.ctaLabel]), h("label", { class: "f" }, ["Button führt zu", f.target, f.custom])]),
        h("div", { class: "f" }, [h("strong", { text: "Bild" }), imgPrev]),
        h("label", { class: "f" }, ["Bildbeschreibung (für Barrierefreiheit und Google)", f.imageAlt]),
        h("label", { class: "chk" }, [f.active, "Auf der Website zeigen"]),
        h("label", { class: "chk" }, [f.highlight, "Auf der Startseite ganz vorn zeigen"]),
        errBox,
        h("div", { class: "btn-row" }, [h("button", { class: "btn primary", type: "submit", text: isNew ? "Anlegen und veröffentlichen" : "Speichern und veröffentlichen" }),
          h("button", { class: "btn", type: "button", text: "Abbrechen", onclick: function () { close(); } })])]);
      f.target.addEventListener("change", function () { f.custom.hidden = !!f.target.value; if (f.target.value) f.custom.value = ""; });
      form.addEventListener("input", preview); form.addEventListener("change", preview);
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var body = { title: f.title.value, badge: f.badge.value, text: f.text.value, price: f.price.value, validFrom: f.validFrom.value, validUntil: f.validUntil.value,
          ctaLabel: f.ctaLabel.value, ctaHref: f.target.value || f.custom.value, icon: f.icon.value, image: image, imageAlt: f.imageAlt.value,
          active: f.active.checked, highlight: f.highlight.checked };
        var btn = form.querySelector('button[type="submit"]'); btn.disabled = true; btn.textContent = "Wird veröffentlicht …"; errBox.innerHTML = "";
        api(isNew ? "POST" : "PUT", isNew ? "angebote" : "angebote/" + o.id, body).then(function (r) { data = r; close(); render(); offerSaved(r); })
          .catch(function (err) {
            var ers = (err.data && err.data.errors) || {};
            errBox.appendChild(h("p", { class: "note", text: Object.keys(ers).length ? Object.keys(ers).map(function (k) { return ers[k]; }).join(" ") : err.message }));
            btn.disabled = false; btn.textContent = isNew ? "Anlegen und veröffentlichen" : "Speichern und veröffentlichen";
          });
      });
      showImg(); preview();
      var close = drawer(h("div", { class: "grid" }, [h("h2", { text: isNew ? "Neues Angebot" : "Angebot bearbeiten" }), h("p", { class: "sub", text: "Vorschau" }), card, form]));
      f.title.focus();
    };
    document.getElementById("newOffer").addEventListener("click", function () { editOffer(null); });
    api("GET", "angebote").then(function (r) { data = r; render(); if (arg === "neu") editOffer(null); }).catch(fail);
  }

  /* ------------------------------------------------------------ Veröffentlichen */
  function viewPublish(main) {
    var lp = ME.lastPublish;
    main.innerHTML = '<div class="head"><div><h1>Veröffentlichen</h1><p>Baut die komplette Website neu aus den gespeicherten Inhalten und schaltet sie ohne Ausfallzeit live. Die letzten fünf Stände bleiben als Sicherung erhalten.</p></div></div>' +
      '<section class="panel"><div class="btn-row"><button class="btn primary" id="pub" type="button">Jetzt veröffentlichen</button></div><div id="pres" style="margin-top:14px"></div></section>';
    var show = function (r) {
      var box = document.getElementById("pres"); box.innerHTML = "";
      if (!r) { box.appendChild(h("p", { class: "muted", text: "Noch nicht über das Portal veröffentlicht." })); return; }
      box.appendChild(h("p", { class: "note " + (r.ok ? "ok" : ""), text: r.ok ? "Live seit " + deDateTime(r.at) + " (" + r.seconds + " s, Stand " + r.release + ")" : "Fehler beim Veröffentlichen" }));
      (r.warnings || []).forEach(function (w) { box.appendChild(h("p", { class: "note", text: "Offen: " + w })); });
      if (r.log) box.appendChild(h("details", {}, [h("summary", { text: "Protokoll" }), h("pre", { class: "log", text: r.log })]));
    };
    show(lp);
    document.getElementById("pub").addEventListener("click", function () {
      var b = this; b.disabled = true; b.textContent = "Wird gebaut …";
      api("POST", "veroeffentlichen", {}).then(function (r) { ME.lastPublish = r; show(r); toast(r.ok ? "Website aktualisiert" : "Fehler", !r.ok); })
        .catch(fail).then(function () { b.disabled = false; b.textContent = "Jetzt veröffentlichen"; });
    });
  }

  /* ------------------------------------------------------------ Einstellungen */
  function viewSettings(main) {
    main.innerHTML = '<div class="head"><div><h1>Einstellungen</h1><p>Benachrichtigungen, Zahlungshinweis für Gutscheine und Protokoll.</p></div></div><div class="grid g2" id="sw"><p class="empty">Lädt …</p></div>';
    Promise.all([api("GET", "einstellungen"), api("GET", "audit")]).then(function (res) {
      var s = res[0], log = res[1], w = document.getElementById("sw"); w.innerHTML = "";
      var ta = h("textarea", { rows: 6, placeholder: "z. B. Bitte überweise den Betrag an: ElbDetail, IBAN DE.., Verwendungszweck: Vorgangsnummer" }); ta.value = s.zahlungshinweis || "";
      w.appendChild(h("section", { class: "panel grid" }, [h("h2", { text: "Zahlungshinweis für Gutscheine" }), h("p", { class: "sub", text: "Wird in der automatischen Bestätigungs-E-Mail an Gutschein-Käufer eingefügt." }), ta,
        h("div", {}, [h("button", { class: "btn primary", type: "button", text: "Speichern", onclick: function () { api("PUT", "einstellungen", { zahlungshinweis: ta.value }).then(function () { toast("Gespeichert"); }).catch(fail); } })])]));
      w.appendChild(h("section", { class: "panel grid" }, [h("h2", { text: "E-Mail-Benachrichtigungen" }),
        h("p", { class: "note " + (s.mail ? "ok" : ""), text: s.mail ? "E-Mail-Versand eingerichtet über " + s.smtpHost + ". Benachrichtigungen gehen an " + s.notify + "." : "E-Mail-Versand ist nicht eingerichtet. In der Server-Datei .env die SMTP-Zugangsdaten eintragen." }),
        h("p", { class: "muted", text: "Eingangsbestätigung an Kund:innen: " + (s.autoreply ? "an" : "aus") + ". Unbearbeitete Anfragen werden nach " + s.retentionDays + " Tagen automatisch gelöscht (DSGVO)." }),
        h("div", {}, [h("button", { class: "btn", type: "button", text: "Test-E-Mail senden", onclick: function () { api("POST", "testmail", {}).then(function (r) { toast(r.message, !r.ok); }).catch(fail); } })])]));
      w.appendChild(h("section", { class: "panel", style: "grid-column:1/-1" }, [h("h2", { text: "Protokoll" }),
        h("div", { class: "tablewrap" }, [h("table", { html: "<thead><tr><th>Zeit</th><th>Aktion</th><th>Detail</th></tr></thead><tbody>" + log.map(function (l) { return '<tr><td class="num">' + deDateTime(l.ts) + "</td><td>" + esc(l.action) + "</td><td>" + esc(l.detail) + "</td></tr>"; }).join("") + "</tbody>" })])]));
    }).catch(fail);
  }

  /* Start */
  api("GET", "me").then(function (me) { ME = me; route(); }).catch(function () { if (!ME) renderLogin(); });
})();
