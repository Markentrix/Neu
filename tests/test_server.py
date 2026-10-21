# -*- coding: utf-8 -*-
"""Unit-/Integrationstests für Generator und Server (nur Standardbibliothek).

    python3 -m unittest discover -s tests -p 'test_*.py'
"""
import datetime as dt
import http.cookiejar
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import warnings
import urllib.error
import urllib.parse
import urllib.request

warnings.simplefilter("ignore", ResourceWarning)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="elb-test-")
shutil.copytree(os.path.join(ROOT, "content"), os.path.join(TMP, "content"), ignore=shutil.ignore_patterns(".media-cache"))
os.environ.update({
    "ELB_DATA": os.path.join(TMP, "data"), "ELB_CONTENT": os.path.join(TMP, "content"), "ELB_SITE_ROOT": os.path.join(TMP, "site"),
    "ELB_SERVE_STATIC": "1", "ADMIN_USER": "admin", "ADMIN_PASSWORD": "Test-Passwort-123", "COOKIE_SECURE": "0",
    "RATE_LIMIT_ANFRAGEN": "1000", "SMTP_HOST": "", "PORT": "0",
})
sys.path.insert(0, os.path.join(ROOT, "server"))
sys.path.insert(0, os.path.join(ROOT, "build"))
import app  # noqa: E402
import md  # noqa: E402


def next_workday(days=3):
    d = dt.date.today() + dt.timedelta(days=days)
    while d.weekday() == 6:
        d += dt.timedelta(days=1)
    return d.isoformat()


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(app.Cfg.site_root, exist_ok=True)
        app.init_db()
        r = app.publish()
        assert r["ok"], r.get("log")
        cls.srv = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.jar = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.jar))

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, method, path, body=None, headers=None, raw=False, form=False):
        h = {"Accept": "application/json"}
        data = None
        if body is not None:
            if form:
                data = urllib.parse.urlencode(body, doseq=True).encode()
                h["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                data = json.dumps(body).encode()
                h["Content-Type"] = "application/json"
        h.update(headers or {})
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            resp = self.opener.open(r)
            code, txt = resp.status, resp.read()
        except urllib.error.HTTPError as e:
            code, txt = e.code, e.read()
        if raw:
            return code, txt
        try:
            return code, json.loads(txt or b"{}")
        except ValueError:
            return code, {"_raw": txt[:200]}

    def admin(self, method, path, body=None):
        return self.req(method, "/admin/api/" + path, body, {"X-ELB-Admin": "1"})

    def login(self):
        if any(c.name == "elb_s" for c in self.jar):
            return
        code, j = self.admin("POST", "login", {"user": "admin", "password": "Test-Passwort-123"})
        self.assertEqual(code, 200, j)


class TestMarkdown(unittest.TestCase):
    def test_escapes_html_and_links(self):
        out = md.render("## Titel\n\nText mit <script>alert(1)</script> und [Link](/termin.html) und [x](javascript:alert(1))", "../")
        self.assertIn('<h2 id="titel">', out)
        self.assertNotIn("<script>", out)
        self.assertIn('href="../termin.html"', out)
        self.assertNotIn("javascript:", out)

    def test_table_and_list(self):
        out = md.render("| A | B |\n|---|---|\n| 1 | 2 |\n\n- eins\n- zwei")
        self.assertIn("<table", out)
        self.assertIn("<li>zwei</li>", out)

    def test_frontmatter_roundtrip(self):
        meta, body = md.parse_frontmatter(md.write_frontmatter({"title": "T"}, "Hallo"))
        self.assertEqual(meta["title"], "T")
        self.assertEqual(body.strip(), "Hallo")


class TestBuild(Base):
    def test_pages_and_seo_files(self):
        site = app.site_dir()
        for p in ["index.html", "preise.html", "kontakt.html", "termin.html", "gutscheine.html", "firmenkunden.html", "aktion/winterschutz.html", "ratgeber/index.html",
                  "leistungen/lackpolitur-celle.html", "impressum.html", "datenschutz.html", "404.html", "danke.html",
                  "sitemap.xml", "robots.txt", "llms.txt", "llms-full.txt", "config.js", "ratgeber/feed.xml"]:
            self.assertTrue(os.path.exists(os.path.join(site, p)), p)
        sm = open(os.path.join(site, "sitemap.xml"), encoding="utf-8").read()
        self.assertIn("/ratgeber/", sm)
        self.assertIn("/preise.html", sm)
        self.assertNotIn("danke.html", sm)
        self.assertNotIn("entwurf", sm)
        robots = open(os.path.join(site, "robots.txt"), encoding="utf-8").read()
        self.assertIn("Disallow: /admin", robots)
        self.assertIn("GPTBot", robots)

    def test_json_ld_valid(self):
        import re
        site = app.site_dir()
        for root, _, files in os.walk(site):
            for f in files:
                if f.endswith(".html"):
                    t = open(os.path.join(root, f), encoding="utf-8").read()
                    for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
                        json.loads(blob)

    def test_seo_title_and_description_lengths(self):
        import build as builder
        site = app.site_dir()
        rel = [os.path.relpath(os.path.join(r, f), site) for r, _, fs in os.walk(site) for f in fs if f.endswith(".html")]
        self.assertGreater(len(rel), 20)
        self.assertEqual(builder.seo_lengths(site, rel), [])

    def test_price_placeholders_resolved(self):
        site = app.site_dir()
        for root, _, files in os.walk(site):
            for f in files:
                if f.endswith((".html", ".txt", ".xml")):
                    t = open(os.path.join(root, f), encoding="utf-8").read()
                    self.assertNotIn("{ab:", t, f)
                    self.assertNotIn("{preis:", t, f)
        self.assertIn("ab 299\u00a0€", open(os.path.join(site, "leistungen/innenaufbereitung-celle.html"), encoding="utf-8").read())

    def test_owner_card_and_verification_only_when_filled(self):
        import build as builder
        site = app.site_dir()
        home = open(os.path.join(site, "index.html"), encoding="utf-8").read()
        self.assertIn("owner-card", home)  # Startinhalt: Karte von René ist gefüllt
        self.assertNotIn("google-site-verification", home)
        tmp = tempfile.mkdtemp(prefix="elb-owner-")
        content = os.path.join(tmp, "content")
        shutil.copytree(os.path.join(ROOT, "content"), content, ignore=shutil.ignore_patterns(".media-cache"))
        p = os.path.join(content, "site.json")
        d = json.load(open(p, encoding="utf-8"))
        d["about"] = {"name": "", "role": "", "photo": "", "since": "", "text": ""}
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        builder.build(content, os.path.join(tmp, "leer"), os.path.join(ROOT, "static"), quiet=True)
        self.assertNotIn("owner-card", open(os.path.join(tmp, "leer", "index.html"), encoding="utf-8").read())
        d["about"] = {"name": "Max Muster", "role": "Inhaber", "photo": "", "since": "2023", "text": "Ich bereite jedes Auto selbst auf."}
        d["verification"] = {"google": "abc123", "bing": ""}
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        builder.build(content, os.path.join(tmp, "out"), os.path.join(ROOT, "static"), quiet=True)
        home = open(os.path.join(tmp, "out", "index.html"), encoding="utf-8").read()
        self.assertIn("owner-card", home)
        self.assertIn("Max Muster", home)
        self.assertIn('<meta name="google-site-verification" content="abc123">', home)
        self.assertNotIn("msvalidate.01", home)
        self.assertIn('"founder":{"@type":"Person","name":"Max Muster"', home)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_formal_address_everywhere(self):
        """Kund:innen werden gesiezt: keine Du-Ansprache in Seiten, Texten und E-Mail-Vorlagen."""
        import re
        pat = re.compile(r"\b(du|dich|dir|dein|deine|deinen|deinem|deiner|deines|euch|euer|eure|euren|eurem|eurer)\b", re.I)
        site = app.site_dir()
        hits = []
        for root, _, files in os.walk(site):
            for f in files:
                if f.endswith((".html", ".txt", ".xml", ".js")):
                    t = open(os.path.join(root, f), encoding="utf-8").read()
                    t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.S)
                    t = re.sub(r"<[^>]+>", " ", t)
                    hits += [f"{f}: {m.group(0)} …{t[max(0, m.start() - 30):m.end() + 30]!r}" for m in pat.finditer(t)]
        self.assertEqual(hits[:10], [])

    def test_no_inline_scripts_for_csp(self):
        import re
        site = app.site_dir()
        for root, _, files in os.walk(site):
            for f in files:
                if f.endswith(".html"):
                    t = open(os.path.join(root, f), encoding="utf-8").read()
                    self.assertIsNone(re.search(r'<script(?![^>]*(?:\bsrc=|type="application/ld\+json"))[^>]*>', t), f)
                    self.assertIsNone(re.search(r'\son(click|submit|load|change)=', t), f)


class TestPublicAPI(Base):
    def test_health_and_availability(self):
        self.assertEqual(self.req("GET", "/api/health")[0], 200)
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertEqual(code, 200)
        self.assertIn(0, j["closedWeekdays"])

    def test_termin_ok(self):
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "essential", "klasse": "suv", "datum": next_workday(), "name": "Max",
                                                   "telefon": "0172 1234567", "einwilligung": "ja", "extras": ["Motorraumreinigung"]})
        self.assertEqual(code, 200, j)
        self.assertTrue(j["ref"].startswith("T"))

    def test_validation_errors(self):
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "gibtsnicht", "einwilligung": "nein"})
        self.assertEqual(code, 422)
        for k in ("name", "telefon", "paket", "datum", "einwilligung"):
            self.assertIn(k, j["errors"])

    def test_sunday_and_past_rejected(self):
        d = dt.date.today() + dt.timedelta(days=(6 - dt.date.today().weekday()) % 7 or 7)
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "refresh", "klasse": "kompakt", "datum": d.isoformat(), "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
        self.assertEqual(code, 422)
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "refresh", "klasse": "kompakt", "datum": "2020-01-01", "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
        self.assertEqual(code, 422)

    def test_form_encoded_redirect(self):
        r = urllib.request.Request(self.base + "/api/anfrage", method="POST",
                                   data=b"typ=kontakt&name=Erika&email=e%40example.com&paket=Komplettpflege&einwilligung=ja",
                                   headers={"Content-Type": "application/x-www-form-urlencoded"})

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        try:
            urllib.request.build_opener(NoRedirect).open(r)
            self.fail("kein Redirect")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 303)
            self.assertIn("/danke.html?typ=kontakt", e.headers["Location"])

    def test_honeypot_and_origin(self):
        code, j = self.req("POST", "/api/anfrage", {"typ": "kontakt", "website": "http://spam", "name": "x"})
        self.assertEqual((code, j.get("ref")), (200, "OK"))
        code, _ = self.req("POST", "/api/anfrage", {"typ": "kontakt"}, {"Origin": "https://evil.example"})
        self.assertEqual(code, 403)

    def test_capacity_and_next_free_day(self):
        self.login()
        day = next_workday(10)
        code, _ = self.admin("PUT", "kalender", {"dailyCapacity": 1, "leadDays": 1})
        self.assertEqual(code, 200)
        code, _ = self.admin("PUT", "kalender", {"dailyCapacity": "viele"})
        self.assertEqual(code, 422)
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertNotIn(day, j["blocked"])
        nf = dt.date.fromisoformat(j["nextFree"])
        self.assertGreater(nf, dt.date.today())
        self.assertNotEqual(nf.weekday(), 6)  # Sonntag ist Ruhetag
        with app.db() as c:  # ein bestätigter Termin füllt den Tag bei Kapazität 1
            c.execute("INSERT INTO anfragen(ref, typ, status, created, updated, name, datum, data) VALUES (?,?,?,?,?,?,?,?)",
                      ("TCAP1", "termin", "termin_bestaetigt", "x", "x", "Test", day, "{}"))
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertIn(day, j["blocked"])
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "essential", "klasse": "kompakt", "datum": day,
                                                    "name": "Eva", "telefon": "0170 1234567", "einwilligung": "ja"})
        self.assertEqual(code, 422)
        self.admin("PUT", "kalender", {"dailyCapacity": 2})
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertNotIn(day, j["blocked"])
        # Keramik belegt den ganzen Tag: an einem Tag mit einem anderen Termin ist keine Keramik möglich ...
        self.assertIn(day, j["blockedKeramik"])
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "keramik", "klasse": "kompakt", "datum": day,
                                                    "name": "Eva", "telefon": "0170 1234567", "einwilligung": "ja"})
        self.assertEqual(code, 422)
        # ... und eine bestätigte Keramik sperrt den Tag für alles andere, auch bei Kapazität 2
        day2 = next_workday(12)
        with app.db() as c:
            c.execute("INSERT INTO anfragen(ref, typ, status, created, updated, name, datum, data) VALUES (?,?,?,?,?,?,?,?)",
                      ("TCAP2", "termin", "termin_bestaetigt", "x", "x", "Test", day2, json.dumps({"paket": "keramik"})))
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertIn(day2, j["blocked"])
        d2 = dt.date.fromisoformat(day2)
        for k in (1, 2):  # Standzeit 3 Tage: auch die zwei Folgetage sind belegt
            self.assertIn((d2 + dt.timedelta(days=k)).isoformat(), j["blocked"])
        self.assertNotIn((d2 + dt.timedelta(days=3)).isoformat(), j["blocked"])
        # eine weitere Keramik darf nicht beginnen, wenn ihre Standzeit in die bestehende ragt
        self.assertIn((d2 - dt.timedelta(days=2)).isoformat(), j["blockedKeramik"])
        self.admin("PUT", "kalender", {"keramikDays": 1})
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertNotIn((d2 + dt.timedelta(days=1)).isoformat(), j["blocked"])
        self.assertEqual(self.admin("PUT", "kalender", {"keramikDays": 9})[0], 422)
        self.admin("PUT", "kalender", {"keramikDays": 3})
        self.admin("PUT", "kalender", {"keramikExclusive": False})
        code, j = self.req("GET", "/api/verfuegbarkeit")
        self.assertNotIn(day2, j["blocked"])
        self.assertNotIn(day, j["blockedKeramik"])
        self.admin("PUT", "kalender", {"keramikExclusive": True})
        with app.db() as c:
            c.execute("DELETE FROM anfragen WHERE ref IN ('TCAP1', 'TCAP2')")

    def test_keepalive_after_early_response(self):
        """Antworten ohne gelesenen Inhalt (Herkunft abgelehnt, Statistik-Limit) dürfen die nächste Anfrage
        auf derselben Verbindung nicht zerstören (wichtig hinter Caddy mit Keep-Alive)."""
        import http.client
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=5)
        try:
            body = json.dumps({"typ": "kontakt", "name": "x" * 500})
            con.request("POST", "/api/anfrage", body, {"Content-Type": "application/json", "Origin": "https://evil.example"})
            r = con.getresponse(); r.read()
            self.assertEqual(r.status, 403)
            for _ in range(130):  # über das Limit von 120 Ereignissen pro Minute
                con.request("POST", "/api/e", json.dumps({"t": "pv", "u": "/"}), {"Content-Type": "application/json"})
                r = con.getresponse(); r.read()
                self.assertEqual(r.status, 204)
            con.request("GET", "/api/health")
            r = con.getresponse()
            self.assertEqual((r.status, json.loads(r.read())), (200, {"ok": True}))
        finally:
            con.close()

    def test_voucher_order_creates_code(self):
        code, j = self.req("POST", "/api/anfrage", {"typ": "gutschein", "art": "wert", "betrag": "150", "name": "Lisa", "email": "l@example.com", "einwilligung": "ja"})
        self.assertEqual(code, 200, j)
        with app.db() as c:
            v = c.execute("SELECT * FROM gutscheine ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(v["wert"], 150)
        self.assertRegex(v["code"], r"^ELB-[A-Z0-9]{4}-[A-Z0-9]{4}$")
        code, _ = self.req("GET", f"/gutschein/{v['code']}?t={v['token']}", raw=True)
        self.assertEqual(code, 200)
        code, _ = self.req("GET", f"/gutschein/{v['code']}?t=falsch", raw=True)
        self.assertEqual(code, 404)

    def test_voucher_amount_limits(self):
        code, j = self.req("POST", "/api/anfrage", {"typ": "gutschein", "art": "wert", "wunschbetrag": "5", "name": "L", "email": "l@example.com", "einwilligung": "ja"})
        self.assertEqual(code, 422)

    def test_analytics_no_ip_stored(self):
        ua = {"User-Agent": "Mozilla/5.0 (Test) Firefox/130"}
        code, _ = self.req("POST", "/api/e", {"t": "pv", "u": "/termin.html?x=1", "r": "google.com", "w": 390, "utm": {"s": "google", "c": "winter"}}, ua, raw=True)
        self.assertEqual(code, 204)
        self.req("POST", "/api/e", {"t": "pv", "u": "/"}, {"User-Agent": "Googlebot/2.1"}, raw=True)
        with app.db() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM events")]
        self.assertTrue(any(r["path"] == "/termin.html" and r["device"] == "Mobil" for r in rows))
        self.assertFalse(any("127.0.0.1" in json.dumps(r) for r in rows))
        self.assertEqual(sum(1 for r in rows if r["path"] == "/" and r["utm_s"] == ""), 0)


class TestAdmin(Base):
    def test_requires_login(self):
        try:
            urllib.request.urlopen(self.base + "/admin/api/stats")
            self.fail("ohne Anmeldung erreichbar")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 401)

    def test_wrong_password(self):
        code, _ = self.admin("POST", "login", {"user": "admin", "password": "falsch"})
        self.assertEqual(code, 401)

    def test_csrf_header_required(self):
        self.login()
        code, _ = self.req("POST", "/admin/api/veroeffentlichen", {})
        self.assertEqual(code, 403)

    def test_workflow(self):
        self.login()
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "signature", "klasse": "mittel", "datum": next_workday(5), "name": "Erika Muster",
                                                   "telefon": "0172 7654321", "email": "erika@example.com", "einwilligung": "ja", "bewertung_ok": "ja"})
        ref = j["ref"]
        code, lst = self.admin("GET", "anfragen?typ=termin")
        self.assertIn(ref, [i["ref"] for i in lst["items"]])
        code, d = self.admin("GET", "anfragen/" + ref)
        self.assertEqual(d["preis"], 549)
        code, t = self.admin("GET", f"anfragen/{ref}/vorlage?art=antwort")
        self.assertIn("wa.me/491727654321", t["whatsapp"])
        code, t = self.admin("GET", f"anfragen/{ref}/vorlage?art=bewertung")
        self.assertEqual(t["warning"], "")
        self.assertEqual(self.admin("PATCH", "anfragen/" + ref, {"status": "termin_bestaetigt", "notizen": "ok"})[0], 200)
        self.assertEqual(self.admin("PATCH", "anfragen/" + ref, {"status": "quatsch"})[0], 422)
        code, s = self.admin("GET", "stats?days=30")
        self.assertGreaterEqual(s["totals"]["leads"], 1)
        code, csvtxt = self.req("GET", "/admin/api/anfragen.csv", raw=True)
        self.assertIn(ref.encode(), csvtxt)
        self.assertEqual(self.admin("DELETE", "anfragen/" + ref)[0], 200)

    def test_calendar_blocks_booking(self):
        self.login()
        day = next_workday(9)
        self.assertEqual(self.admin("POST", "kalender", {"day": day, "reason": "Urlaub"})[0], 200)
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "refresh", "klasse": "kompakt", "datum": day, "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
        self.assertEqual(code, 422)
        self.admin("DELETE", "kalender", {"day": day})

    def test_voucher_lifecycle(self):
        self.login()
        code, j = self.admin("POST", "gutscheine", {"wert": 80, "fuer": "Oma"})
        self.assertEqual(code, 200)
        code, chk = self.admin("GET", "gutscheine/pruefen?code=" + j["code"])
        self.assertEqual(chk["status"], "offen")
        self.assertEqual(self.admin("PATCH", f"gutscheine/{chk['id']}", {"status": "bezahlt"})[0], 200)
        self.assertEqual(self.admin("PATCH", f"gutscheine/{chk['id']}", {"status": "eingeloest"})[0], 200)
        code, chk = self.admin("GET", "gutscheine/pruefen?code=" + j["code"])
        self.assertEqual(chk["status"], "eingeloest")

    def test_content_edit_publish_and_traversal(self):
        self.login()
        code, d = self.admin("GET", "inhalte/pricing.json")
        data = d["data"]
        data["packages"][0]["prices"]["klein"] = 77
        self.assertEqual(self.admin("PUT", "inhalte/pricing.json", {"data": data})[0], 200)
        code, r = self.admin("POST", "veroeffentlichen", {})
        self.assertTrue(r["ok"], r.get("log"))
        html = open(os.path.join(app.site_dir(), "index.html"), encoding="utf-8").read()
        self.assertIn("ab 77 €", html)
        for bad in ["inhalte/..%2F..%2Fetc%2Fpasswd", "inhalte/services%2F..%2F..%2Fx.json", "inhalte/build.py"]:
            self.assertIn(self.admin("GET", bad)[0], (400, 404))
        self.assertEqual(self.admin("PUT", "inhalte/pricing.json", {"data": []})[0], 422)

    def test_offers_create_edit_schedule_delete(self):
        """Angebote: im Portal anlegen, sofort live auf Startseite und /angebote.html, Laufzeit, Bild, Validierung, Löschen."""
        self.login()
        code, r = self.admin("GET", "angebote")
        self.assertEqual(code, 200)
        self.assertTrue(all(len(o["id"]) == 8 for o in r["items"]))
        # Validierung: Titel fehlt, gefährliches Ziel, Enddatum vor Start, unbekanntes Bild
        code, e = self.admin("POST", "angebote", {"title": "", "ctaHref": "javascript:alert(1)", "validFrom": "2030-05-02", "validUntil": "2030-05-01", "image": "gibt-es-nicht.jpg"})
        self.assertEqual(code, 422)
        self.assertTrue({"title", "ctaHref", "validUntil", "image"} <= set(e["errors"]))
        # Bild hochladen und Angebot anlegen
        png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        self.assertEqual(self.admin("POST", "medien", {"name": "angebot-test.png", "data": png})[0], 200)
        code, r = self.admin("POST", "angebote", {"title": "Frühjahrs-Check Test", "badge": "Frühling", "text": "Wäsche und Kontrolle.", "price": "ab 99 €",
                                                 "ctaHref": "termin.html?paket=refresh", "icon": "spark", "image": "angebot-test.png", "highlight": True})
        self.assertEqual(code, 200, r)
        self.assertTrue(r["published"])
        oid = next(o["id"] for o in r["items"] if o["title"] == "Frühjahrs-Check Test")
        home = open(os.path.join(app.site_dir(), "index.html"), encoding="utf-8").read()
        page = open(os.path.join(app.site_dir(), "angebote.html"), encoding="utf-8").read()
        self.assertIn("Frühjahrs-Check Test", home)
        self.assertIn("Frühjahrs-Check Test", page)
        self.assertIn("angebot-test", page)
        # In der Zukunft geplant: nicht sichtbar, Status "geplant"
        future = (dt.date.today() + dt.timedelta(days=10)).isoformat()
        code, r = self.admin("PUT", "angebote/" + oid, {"title": "Frühjahrs-Check Test", "validFrom": future, "active": True})
        self.assertEqual(code, 200, r)
        self.assertEqual(next(o["state"] for o in r["items"] if o["id"] == oid), "geplant")
        self.assertNotIn("Frühjahrs-Check Test", open(os.path.join(app.site_dir(), "angebote.html"), encoding="utf-8").read())
        # Löschen
        self.assertEqual(self.admin("DELETE", "angebote/" + oid)[0], 200)
        self.assertEqual(self.admin("DELETE", "angebote/" + oid)[0], 404)
        self.admin("DELETE", "medien/angebot-test.png")

    def test_new_article_is_draft(self):
        self.login()
        code, j = self.admin("POST", "inhalte/neuer-artikel", {"title": "Testartikel Politur"})
        self.assertEqual(code, 200, j)
        r = app.publish()
        self.assertTrue(r["ok"])
        self.assertFalse(os.path.exists(os.path.join(app.site_dir(), "ratgeber", "testartikel-politur.html")))
        self.assertEqual(self.admin("DELETE", j["path"].replace("ratgeber/", "inhalte/ratgeber/"))[0], 200)

    def test_media_upload_validation(self):
        self.login()
        code, _ = self.admin("POST", "medien", {"name": "bild.jpg", "data": "data:image/jpeg;base64,AAAA"})
        self.assertEqual(code, 422)
        import base64
        import io
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow fehlt")
        buf = io.BytesIO()
        Image.new("RGB", (1600, 1200), (30, 80, 160)).save(buf, "JPEG")
        url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        code, j = self.admin("POST", "medien", {"name": "Golf Vorher.JPG", "data": url})
        self.assertEqual((code, j.get("name")), (200, "golf-vorher.jpg"))
        code, g = self.admin("GET", "inhalte/gallery.json")
        g["data"]["items"][0]["before"] = "golf-vorher.jpg"
        g["data"]["items"][0]["after"] = "golf-vorher.jpg"
        self.admin("PUT", "inhalte/gallery.json", {"data": g["data"]})
        r = app.publish()
        self.assertTrue(r["ok"])
        html = open(os.path.join(app.site_dir(), "index.html"), encoding="utf-8").read()
        self.assertIn('type="image/webp"', html)
        self.assertEqual(self.admin("DELETE", "medien/golf-vorher.jpg")[0], 200)

    def test_backup(self):
        out = app.make_backup()
        self.assertTrue(os.path.exists(out))


class TestBooking(Base):
    """Online-Buchung: Uhrzeit reservieren, per Link bestätigen, Erinnerungen 24 h / 6 h, Absage, Kalender-Abo."""

    def setUp(self):
        self.mails = []
        self._orig = (app.send_mail, app.Cfg.smtp_host, app.Cfg.smtp_from)
        app.Cfg.smtp_host, app.Cfg.smtp_from = "smtp.test", "termine@example.com"
        app.send_mail = lambda to, subject, text, reply_to=None, attachments=None: self.mails.append(
            {"to": to, "subject": subject, "text": text, "att": attachments or []}) or True
        app.set_setting("mailApproval", {k: False for k in app.MAIL_KINDS})  # Standardfälle: ohne Freigabe; Freigabe eigener Test

    def tearDown(self):
        app.send_mail, app.Cfg.smtp_host, app.Cfg.smtp_from = self._orig
        with app.db() as c:  # andere Tests (Auslastung) sollen diese Buchungen nicht sehen
            c.execute("DELETE FROM anfragen WHERE name='Karla Kunde'")
            c.execute("DELETE FROM outbox")
        app.set_setting("mailApproval", {})

    def wait_mail(self, to, n=1):
        for _ in range(100):
            got = [m for m in self.mails if m["to"] == to]
            if len(got) >= n:
                return got
            threading.Event().wait(0.02)
        self.fail(f"keine E-Mail an {to}: {[m['subject'] for m in self.mails]}")

    def book(self, day, zeit, email="kunde@example.com", paket="essential"):
        return self.req("POST", "/api/anfrage", {"typ": "termin", "paket": paket, "klasse": "kompakt", "datum": day, "uhrzeit": zeit,
                                                 "name": "Karla Kunde", "telefon": "0171 2223334", "email": email, "einwilligung": "ja"})

    def test_full_flow(self):
        day = next_workday(9)
        code, j = self.req("GET", f"/api/slots?tag={day}")
        self.assertEqual(code, 200)
        self.assertTrue(j["selfBooking"])
        self.assertTrue(all(x["frei"] for x in j["slots"]), j)
        # ohne Uhrzeit oder E-Mail keine Online-Buchung
        self.assertEqual(self.book(day, "")[0], 422)
        self.assertEqual(self.book(day, "10:00", email="")[0], 422)
        code, j = self.book(day, "10:00")
        self.assertEqual(code, 200, j)
        self.assertEqual(j["status"], "reserviert")
        ref = j["ref"]
        mail = self.wait_mail("kunde@example.com")[0]
        self.assertIn("Bitte bestätigen", mail["subject"])
        m = re.search(r"/termin/" + ref + r"\?t=([\w-]+)", mail["text"])
        self.assertTrue(m, mail["text"])
        token = m.group(1)
        # Uhrzeit ist reserviert, eine zweite Buchung zur gleichen Zeit scheitert
        code, j = self.req("GET", f"/api/slots?tag={day}")
        self.assertFalse(next(x for x in j["slots"] if x["zeit"] == "10:00")["frei"])
        self.assertEqual(self.book(day, "10:00", email="andere@example.com")[0], 422)
        # Bestätigungsseite: falscher Token 404, richtiger Token zeigt den Button
        self.assertEqual(self.req("GET", f"/termin/{ref}?t=falsch", raw=True)[0], 404)
        code, page = self.req("GET", f"/termin/{ref}?t={token}", raw=True)
        self.assertEqual(code, 200)
        self.assertIn("Termin verbindlich bestätigen", page.decode())
        code, page = self.req("POST", f"/termin/{ref}/bestaetigen", {"t": token}, raw=True, form=True)
        self.assertIn("verbindlich gebucht", page.decode())
        with app.db() as c:
            self.assertEqual(c.execute("SELECT status FROM anfragen WHERE ref=?", (ref,)).fetchone()["status"], "termin_bestaetigt")
        conf = [m for m in self.wait_mail("kunde@example.com", 2) if "bestätigt" in m["subject"]][0]
        self.assertIn("meldet sich vorab telefonisch", conf["text"])
        self.assertIn("Fahrzeug vor der Aufbereitung", conf["text"])
        self.assertTrue(conf["att"] and b"BEGIN:VEVENT" in conf["att"][0][2])
        self.assertTrue(any("vom Kunden bestätigt" in m["subject"] for m in self.mails))
        # erneutes Absenden verschickt nichts doppelt
        n = len(self.mails)
        self.req("POST", f"/termin/{ref}/bestaetigen", {"t": token}, raw=True, form=True)
        threading.Event().wait(0.2)
        self.assertEqual(len(self.mails), n)
        # Erinnerungen 24 h und 6 h vorher sind geplant und gehen erst zum Zeitpunkt raus
        with app.db() as c:
            rem = [dict(x) for x in c.execute("SELECT id, send_after, status FROM outbox WHERE ref=? AND kind='erinnerung' ORDER BY send_after", (ref,))]
        self.assertEqual(len(rem), 2)
        st = app.termin_start(app.load_termin(ref)[1])
        self.assertEqual(rem[0]["send_after"], (st - dt.timedelta(hours=24)).isoformat())
        app.booking_tick()
        threading.Event().wait(0.1)
        self.assertFalse([m for m in self.mails if "Erinnerung" in m["subject"]])
        with app.db() as c:
            c.execute("UPDATE outbox SET send_after=? WHERE id=?", ((app.now() - dt.timedelta(minutes=1)).isoformat(), rem[0]["id"]))
        app.booking_tick()
        self.wait_mail("kunde@example.com", 3)
        app.booking_tick()  # keine doppelte Erinnerung
        threading.Event().wait(0.1)
        self.assertEqual(len([m for m in self.mails if "Erinnerung" in m["subject"]]), 1)
        # Verschieben durch den Kunden: neue Uhrzeit, Bestätigung neu, Erinnerungen neu geplant
        code, page = self.req("GET", f"/termin/{ref}?t={token}&aktion=verschieben&tag={day}", raw=True)
        self.assertIn("Auf diesen Termin verschieben", page.decode())
        self.assertNotIn('value="10:00"', page.decode())  # eigene alte Uhrzeit ist bereits belegt
        code, page = self.req("POST", f"/termin/{ref}/verschieben", {"t": token, "datum": day, "uhrzeit": "09:00"}, raw=True, form=True)
        self.assertIn("verschoben", page.decode())
        r, d = app.load_termin(ref)
        self.assertEqual((d["uhrzeit"], r["status"]), ("09:00", "termin_bestaetigt"))
        self.assertTrue(any("Termin verschoben" in m["subject"] for m in self.mails))
        code, page = self.req("POST", f"/termin/{ref}/verschieben", {"t": token, "datum": day, "uhrzeit": "07:00"}, raw=True, form=True)
        self.assertIn("nicht mehr frei", page.decode())
        # Kalender-Abo (iCal) nur mit Schlüssel
        self.assertEqual(self.req("GET", "/api/kalender.ics?key=falsch", raw=True)[0], 404)
        code, ics = self.req("GET", "/api/kalender.ics?key=" + app.ics_key(), raw=True)
        self.assertEqual(code, 200)
        self.assertIn(ref, ics.decode())
        # Absage durch den Kunden: erst Rückfrage (Verschieben anbieten), dann endgültig
        code, page = self.req("GET", f"/termin/{ref}?t={token}&aktion=absagen", raw=True)
        self.assertIn("Lieber verschieben", page.decode())
        self.req("POST", f"/termin/{ref}/absagen", {"t": token}, raw=True, form=True)  # ohne Bestätigung keine Absage
        self.assertEqual(app.load_termin(ref)[0]["status"], "termin_bestaetigt")
        code, page = self.req("POST", f"/termin/{ref}/absagen", {"t": token, "ok": "1"}, raw=True, form=True)
        self.assertIn("abgesagt", page.decode())
        with app.db() as c:
            self.assertEqual(c.execute("SELECT status FROM anfragen WHERE ref=?", (ref,)).fetchone()["status"], "storniert")

    def test_reservation_expires_and_frees_slot(self):
        day = next_workday(10)
        code, j = self.book(day, "09:00", email="spaet@example.com")
        self.assertEqual(code, 200, j)
        ref = j["ref"]
        self.wait_mail("spaet@example.com")  # Versand im Hintergrund setzt die Frist neu, erst danach manipulieren
        threading.Event().wait(0.1)
        r, d = app.load_termin(ref)
        d["hold_until"] = (app.now() - dt.timedelta(minutes=1)).isoformat()
        app.save_termin(r["id"], d)
        code, j = self.req("GET", f"/api/slots?tag={day}")
        self.assertTrue(next(x for x in j["slots"] if x["zeit"] == "09:00")["frei"])  # abgelaufene Reservierung belegt nichts
        app.booking_tick()
        with app.db() as c:
            self.assertEqual(c.execute("SELECT status FROM anfragen WHERE ref=?", (ref,)).fetchone()["status"], "verfallen")
        token = d["token"]
        code, page = self.req("GET", f"/termin/{ref}?t={token}", raw=True)
        self.assertIn("abgelaufen", page.decode())

    def test_paypal_deposit_confirms_booking(self):
        os.environ.update({"PAYPAL_CLIENT_ID": "id", "PAYPAL_SECRET": "geheim"})
        orig = (app.paypal_create, app.paypal_capture, app.paypal_refund)
        calls = {}
        app.paypal_create = lambda ref, d: (calls.setdefault("order", "ORDER-" + ref), self.base + "/api/health")
        app.paypal_capture = lambda oid: {"status": "COMPLETED", "capture_id": "CAP1", "capture_status": "COMPLETED", "currency": "EUR", "value": calls["value"], "ref": ""}
        app.paypal_refund = lambda cid, value, ref: calls.setdefault("refund", "COMPLETED")
        try:
            day = next_workday(13)
            code, j = self.book(day, "08:00", email="zahler@example.com")  # Essential, Kompaktwagen: 15 % von 329 €
            self.assertEqual(code, 200, j)
            ref = j["ref"]
            mail = self.wait_mail("zahler@example.com")[0]
            self.assertIn("Anzahlung von 49,35 €", mail["text"])
            token = re.search(r"\?t=([\w-]+)", mail["text"]).group(1)
            code, page = self.req("GET", f"/termin/{ref}?t={token}", raw=True)
            self.assertIn("mit PayPal leisten", page.decode())
            code, _ = self.req("POST", f"/termin/{ref}/bestaetigen", {"t": token}, raw=True, form=True)  # Weiterleitung zu PayPal
            r, d = app.load_termin(ref)
            self.assertEqual(r["status"], "reserviert")  # ohne Zahlung noch nicht bestätigt
            self.assertEqual(d["paypal_order"], "ORDER-" + ref)
            calls["value"] = 10.0  # zu wenig bezahlt: keine Bestätigung
            code, page = self.req("GET", f"/termin/{ref}/bezahlt?t={token}&token=ORDER-{ref}", raw=True)
            self.assertIn("nicht abgeschlossen", page.decode())
            calls["value"] = 49.35
            code, page = self.req("GET", f"/termin/{ref}/bezahlt?t={token}&token=FREMD", raw=True)
            self.assertIn("gehört nicht", page.decode())
            code, page = self.req("GET", f"/termin/{ref}/bezahlt?t={token}&token=ORDER-{ref}", raw=True)
            self.assertIn("Anzahlung ist eingegangen", page.decode())
            r, d = app.load_termin(ref)
            self.assertEqual(r["status"], "termin_bestaetigt")
            self.assertEqual(d["zahlung"]["capture_id"], "CAP1")
            conf = [m for m in self.wait_mail("zahler@example.com", 2) if "bestätigt" in m["subject"]][0]
            self.assertIn("Anzahlung von 49,35 € per PayPal ist eingegangen", conf["text"])
            code, page = self.req("GET", f"/termin/{ref}?t={token}&aktion=absagen", raw=True)
            self.assertIn("als Ausfallpauschale einbehalten", page.decode())
            self.req("POST", f"/termin/{ref}/absagen", {"t": token, "ok": "1"}, raw=True, form=True)
            r, d = app.load_termin(ref)
            self.assertEqual(r["status"], "storniert")
            self.assertTrue(d["zahlung"].get("einbehalten"))
            self.assertTrue(any("Ausfallpauschale" in m["text"] for m in self.mails if m["to"] == "zahler@example.com"))
            self.login()
            code, j = self.admin("POST", f"anfragen/{ref}/erstatten", {})  # Erstattung aus Kulanz bleibt möglich
            self.assertEqual(code, 200, j)
            self.assertTrue(app.load_termin(ref)[1]["zahlung"]["erstattet"])
        finally:
            app.paypal_create, app.paypal_capture, app.paypal_refund = orig
            for k in ("PAYPAL_CLIENT_ID", "PAYPAL_SECRET"):
                os.environ.pop(k, None)

    def test_approval_outbox(self):
        """Jede Kunden-E-Mail wartet im Postausgang; René legt die Anzahlung fest, ändert den Text und gibt frei."""
        app.set_setting("mailApproval", {})
        self.login()
        day = next_workday(14)
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "essential", "klasse": "sport", "datum": day, "uhrzeit": "09:00",
                                                    "name": "Karla Kunde", "telefon": "0171 2223334", "email": "frei@example.com", "einwilligung": "ja"})
        self.assertEqual(code, 200, j)
        ref = j["ref"]
        threading.Event().wait(0.2)
        self.assertFalse([m for m in self.mails if m["to"] == "frei@example.com"])  # noch nichts an den Kunden
        self.assertTrue(any("Anzahlung festlegen" in m["text"] for m in self.mails))  # Sportwagen: kein Festpreis
        code, ob = self.admin("GET", "postausgang")
        draft = next(o for o in ob["items"] if o["ref"] == ref and o["kind"] == "reservierung")
        self.assertEqual(draft["status"], "entwurf")
        self.assertIsNone(draft["anzahlung"])
        code, me = self.admin("GET", "me")
        self.assertGreaterEqual(me["outbox"], 1)
        code, j = self.admin("PUT", f"postausgang/{draft['id']}", {"anzahlung": "120"})
        self.assertIn("120", j["body"])
        self.assertEqual(app.load_termin(ref)[1]["anzahlung"], 120.0)
        body = j["body"] + "\nPS: Bitte Fahrzeugschein mitbringen."
        code, j = self.admin("POST", f"postausgang/{draft['id']}/freigeben", {"subject": j["subject"], "body": body})
        self.assertEqual(code, 200, j)
        mail = self.wait_mail("frei@example.com")[0]
        self.assertIn("Fahrzeugschein", mail["text"])
        self.assertIn("120 €", mail["text"])
        self.assertEqual(self.admin("POST", f"postausgang/{draft['id']}/freigeben", {})[0], 409)  # schon gesendet
        # Frist läuft ab Versand
        hold = dt.datetime.fromisoformat(app.load_termin(ref)[1]["hold_until"])
        self.assertLess(hold, app.now() + dt.timedelta(hours=25))
        # Bestätigung durch den Kunden landet ebenfalls als Entwurf im Postausgang
        token = app.load_termin(ref)[1]["token"]
        self.req("POST", f"/termin/{ref}/bestaetigen", {"t": token}, raw=True, form=True)
        code, ob = self.admin("GET", f"postausgang?ref={ref}")
        kinds = sorted(o["kind"] for o in ob["items"] if o["status"] == "entwurf")
        self.assertEqual(kinds, ["bestaetigung", "erinnerung", "erinnerung"])
        conf = next(o for o in ob["items"] if o["kind"] == "bestaetigung")
        self.admin("POST", f"postausgang/{conf['id']}/freigeben", {})
        self.assertTrue([m for m in self.wait_mail("frei@example.com", 2) if "bestätigt" in m["subject"]])
        rem = next(o for o in ob["items"] if o["kind"] == "erinnerung")
        code, j = self.admin("POST", f"postausgang/{rem['id']}/freigeben", {})
        self.assertIn("geplanten Zeitpunkt", j["message"])
        code, j = self.admin("PUT", "postausgang", {"approval": {"erinnerung": False}})
        self.assertFalse(self.admin("GET", "postausgang")[1]["approval"]["erinnerung"])

    def test_winter_offer_booking(self):
        day = next_workday(15)
        code, j = self.book(day, "08:00", email="winter@example.com", paket="winter")
        self.assertEqual(code, 200, j)
        d = app.load_termin(j["ref"])[1]
        self.assertEqual(d["anzahlung"], 56.85)  # 15 % vom Winterpreis Kompaktwagen (379 €)
        self.assertIn("Winterangebot mit Wachs", app.summary_text(d))

    def test_reviews_sync_updates_site(self):
        orig = app.reviews_fetch
        app.reviews_fetch = lambda: {"value": "4,9", "count": 23}
        try:
            r = app.reviews_sync()
            self.assertTrue(r["ok"] and r["changed"], r)
            self.assertEqual(app.site_info()["rating"]["count"], 23)
            html = open(os.path.join(app.site_dir(), "index.html"), encoding="utf-8").read()
            self.assertIn("23", html)
            self.assertFalse(app.reviews_sync()["changed"])  # unverändert: nichts neu veröffentlichen
        finally:
            app.reviews_fetch = orig

    def test_admin_confirm_sends_mail(self):
        self.login()
        day = next_workday(11)
        code, j = self.book(day, "10:00", email="portal@example.com")
        ref = j["ref"]
        self.wait_mail("portal@example.com")
        code, _ = self.admin("PATCH", f"anfragen/{ref}", {"status": "termin_bestaetigt", "uhrzeit": "10:00", "datum": day})
        self.assertEqual(code, 200)
        conf = [m for m in self.wait_mail("portal@example.com", 2) if "bestätigt" in m["subject"]]
        self.assertTrue(conf)
        code, j = self.admin("GET", "kalender")
        self.assertIn("icsUrl", j)
        self.assertFalse(j["google"]["configured"])


if __name__ == "__main__":
    unittest.main()
