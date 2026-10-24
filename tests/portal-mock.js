// Nur für die Browser-Tests: liefert website-fertig/ statisch aus und spielt die Website-API des Markentrix-Portals nach.
// Gehört nicht zur Website und wird nicht hochgeladen.
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "website-fertig");
const PORT = Number(process.env.PORT || 8099);
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".woff2": "font/woff2", ".xml": "application/xml", ".txt": "text/plain; charset=utf-8",
  ".webmanifest": "application/manifest+json" };
const SLOT_TIMES = ["08:00", "09:00", "10:00"];
const booked = new Set();   // "JJJJ-MM-TT 08:00": vergeben
const anfragen = [];
let paypalMe = "";
let fotos = 0;          // PayPal.me-Name, wie ihn das Portal in /api/verfuegbarkeit liefert
let n = 0;

const iso = (d) => d.toISOString().slice(0, 10);
function nextFree() {
  const d = new Date(); d.setDate(d.getDate() + 1);
  while (d.getDay() === 0) d.setDate(d.getDate() + 1);
  return iso(d);
}
function json(res, code, obj) { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(obj)); }

function api(req, res, url, body) {
  if (url.pathname === "/api/verfuegbarkeit") return json(res, 200, { blocked: [], closedWeekdays: [0], nextFree: nextFree(), selfBooking: true, slotTimes: SLOT_TIMES, paypalMe });
  if (url.pathname === "/api/slots") {
    const tag = url.searchParams.get("tag") || "";
    return json(res, 200, { tag, slots: SLOT_TIMES.map((z) => ({ zeit: z, frei: !booked.has(tag + " " + z) })) });
  }
  if (url.pathname === "/api/e") { res.writeHead(204); return res.end(); }
  if (url.pathname === "/api/foto" && req.method === "GET") return json(res, 200, { aktiv: true, max: 3, tage: 30, hinweis: "Die Fotos werden nach 30 Tagen automatisch gelöscht." });
  if (url.pathname === "/api/foto" && req.method === "POST") {
    if (!body || body.length < 100) return json(res, 422, { ok: false, message: "Kein Bild erkannt." });
    fotos++; return json(res, 200, { token: "foto-" + fotos });
  }
  if (url.pathname === "/api/anfrage" && req.method === "POST") {
    let d = {};
    try { d = JSON.parse(body || "{}"); } catch (e) { return json(res, 400, { ok: false }); }
    if (d.website) return json(res, 200, { ok: true, ref: "OK" });
    const errors = {};
    if (!d.name) errors.name = "Bitte den Namen angeben.";
    if (d.einwilligung !== "ja") errors.einwilligung = "Bitte die Datenschutzhinweise bestätigen.";
    if (["termin", "kontakt", "gutschein", "firma", "widerruf"].includes(d.typ) && !d.email) errors.email = "Bitte eine E-Mail-Adresse angeben.";
    if (d.typ === "termin") {
      if (!d.datum) errors.datum = "Bitte einen Tag wählen.";
      if (!d.telefon) errors.telefon = "Bitte eine Telefonnummer angeben.";
      if (d.uhrzeit && booked.has(d.datum + " " + d.uhrzeit)) errors.uhrzeit = "Diese Uhrzeit wurde gerade vergeben. Bitte eine andere wählen.";
    }
    if (Object.keys(errors).length) return json(res, 422, { ok: false, errors });
    if (d.typ === "termin" && d.uhrzeit) booked.add(d.datum + " " + d.uhrzeit);
    const ref = ({ kontakt: "K", termin: "T", gutschein: "G", firma: "F", widerruf: "W" }[d.typ] || "A") + "261023-" + String(++n).padStart(4, "0");
    anfragen.push({ ref, ...d });
    return json(res, 200, { ok: true, ref });
  }
  // Test-Hilfen
  if (url.pathname === "/__mock/anfragen") return json(res, 200, anfragen);
  if (url.pathname === "/__mock/paypal" && req.method === "POST") { paypalMe = JSON.parse(body || "{}").name || ""; return json(res, 200, { ok: true }); }
  if (url.pathname === "/__mock/belegen" && req.method === "POST") { const d = JSON.parse(body || "{}"); booked.add(d.datum + " " + d.uhrzeit); return json(res, 200, { ok: true }); }
  return json(res, 404, { ok: false });
}

http.createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1");
  let body = "";
  req.on("data", (c) => { body += c; });
  req.on("end", () => {
    if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/__mock/")) return api(req, res, url, body);
    let p = path.normalize(path.join(ROOT, decodeURIComponent(url.pathname)));
    if (!p.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, "index.html");
    if (!fs.existsSync(p)) {
      res.writeHead(404, { "Content-Type": TYPES[".html"] });
      return res.end(fs.readFileSync(path.join(ROOT, "404.html")));
    }
    res.writeHead(200, { "Content-Type": TYPES[path.extname(p)] || "application/octet-stream" });
    res.end(fs.readFileSync(p));
  });
}).listen(PORT, "127.0.0.1", () => console.log("Portal-Attrappe auf Port " + PORT));
