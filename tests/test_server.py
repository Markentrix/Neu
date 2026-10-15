# -*- coding: utf-8 -*-
"""Unit-/Integrationstests für Generator und Server (nur Standardbibliothek).

    python3 -m unittest discover -s tests -p 'test_*.py'
"""
import datetime as dt
import http.cookiejar
import json
import os
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
                    self.assertNotIn("{ab:", open(os.path.join(root, f), encoding="utf-8").read(), f)
        self.assertIn("ab 179 €", open(os.path.join(site, "leistungen/innenaufbereitung-celle.html"), encoding="utf-8").read())

    def test_owner_card_and_verification_only_when_filled(self):
        import build as builder
        site = app.site_dir()
        home = open(os.path.join(site, "index.html"), encoding="utf-8").read()
        self.assertNotIn("owner-card", home)
        self.assertNotIn("google-site-verification", home)
        tmp = tempfile.mkdtemp(prefix="elb-owner-")
        content = os.path.join(tmp, "content")
        shutil.copytree(os.path.join(ROOT, "content"), content, ignore=shutil.ignore_patterns(".media-cache"))
        p = os.path.join(content, "site.json")
        d = json.load(open(p, encoding="utf-8"))
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
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "komplett", "klasse": "suv", "datum": next_workday(), "name": "Max",
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
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "frisch", "klasse": "kompakt", "datum": d.isoformat(), "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
        self.assertEqual(code, 422)
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "frisch", "klasse": "kompakt", "datum": "2020-01-01", "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
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
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "premium", "klasse": "mittel", "datum": next_workday(5), "name": "Erika Muster",
                                                   "telefon": "0172 7654321", "email": "erika@example.com", "einwilligung": "ja", "bewertung_ok": "ja"})
        ref = j["ref"]
        code, lst = self.admin("GET", "anfragen?typ=termin")
        self.assertIn(ref, [i["ref"] for i in lst["items"]])
        code, d = self.admin("GET", "anfragen/" + ref)
        self.assertEqual(d["preis"], 399)
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
        code, j = self.req("POST", "/api/anfrage", {"typ": "termin", "paket": "frisch", "klasse": "kompakt", "datum": day, "name": "A", "telefon": "0172 1111111", "einwilligung": "ja"})
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
        data["packages"][0]["prices"]["kompakt"] = 77
        self.assertEqual(self.admin("PUT", "inhalte/pricing.json", {"data": data})[0], 200)
        code, r = self.admin("POST", "veroeffentlichen", {})
        self.assertTrue(r["ok"], r.get("log"))
        html = open(os.path.join(app.site_dir(), "index.html"), encoding="utf-8").read()
        self.assertIn("ab 77 €", html)
        for bad in ["inhalte/..%2F..%2Fetc%2Fpasswd", "inhalte/services%2F..%2F..%2Fx.json", "inhalte/build.py"]:
            self.assertIn(self.admin("GET", bad)[0], (400, 404))
        self.assertEqual(self.admin("PUT", "inhalte/pricing.json", {"data": []})[0], 422)

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


if __name__ == "__main__":
    unittest.main()
