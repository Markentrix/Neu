# -*- coding: utf-8 -*-
"""Tests für den Generator und die Upload-Regeln des Markentrix-Portals (nur Standardbibliothek + Pillow).

    python3 -m unittest discover -s tests -p 'test_*.py'
"""
import html
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
import build as builder  # noqa: E402
import md  # noqa: E402

OUT = tempfile.mkdtemp(prefix="elb-build-")
SITE = os.path.join(OUT, "website-fertig")
ALLOWED = {"html", "css", "js", "json", "xml", "txt", "ico", "png", "jpg", "webp", "avif", "gif", "svg", "woff", "woff2", "ttf", "otf",
           "webmanifest", "pdf", "mp4", "webm", "mp3"}


RESULT = {}


def setUpModule():
    RESULT.update(builder.build(os.path.join(ROOT, "content"), SITE, os.path.join(ROOT, "static"), quiet=True))


def tearDownModule():
    shutil.rmtree(OUT, ignore_errors=True)


def files(*ext):
    for root, _, fs in os.walk(SITE):
        for f in fs:
            if not ext or f.endswith(ext):
                yield os.path.join(root, f)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


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


class TestPortalUpload(unittest.TestCase):
    """Regeln des Markentrix-Uploads: sonst lehnt das Portal ab oder die Seite funktioniert nicht."""

    def test_required_pages_and_root_index(self):
        for p in ["index.html", "impressum.html", "datenschutz.html", "404.html", "danke.html", "agb.html", "widerruf.html",
                  "termin.html", "sitemap.xml", "robots.txt", "favicon.svg"]:
            self.assertTrue(os.path.exists(os.path.join(SITE, p)), p)

    def test_only_allowed_files(self):
        for p in files():
            name = os.path.basename(p)
            self.assertFalse(name.startswith("."), p)
            self.assertFalse(os.path.islink(p), p)
            self.assertIn(name.rsplit(".", 1)[-1].lower(), ALLOWED, p)

    def test_no_backend_localhost_http_or_cdn(self):
        bad = re.compile(r"localhost|127\.0\.0\.1|fonts\.googleapis|fonts\.gstatic|cdnjs|jsdelivr|unpkg|googletagmanager|\.php\b|lorem ipsum", re.I)
        for p in files(".html", ".css", ".js", ".json", ".xml", ".txt", ".svg", ".webmanifest"):
            t = read(p)
            self.assertIsNone(bad.search(t), f"{p}: {bad.search(t)}")
            self.assertNotIn("http://", t, p)

    def test_relative_paths_only(self):
        for p in files(".html"):
            for m in re.finditer(r'(?:href|src)="([^"]+)"', read(p)):
                u = m.group(1)
                self.assertFalse(u.startswith(("file:", "/Users", "C:")), f"{p}: {u}")

    def test_page_basics(self):
        for p in files(".html"):
            t = read(p)
            rel = os.path.relpath(p, SITE)
            self.assertIn('<html lang="en"' if rel.startswith("en" + os.sep) else '<html lang="de"', t, rel)
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1', t, rel)
            title = html.unescape(re.search(r"<title>(.*?)</title>", t, re.S).group(1))
            self.assertLess(len(title), 60, rel)
            self.assertRegex(t, r'<meta name="description" content="[^"]{20,}"', rel)
            self.assertEqual(len(re.findall(r"<h1\b", t)), 1, rel)
            self.assertRegex(t, r'href="(/en/|/|(\.\./)*)impressum\.html"', rel)
            self.assertIn('datenschutz.html"', t, rel)
            for img in re.findall(r"<img\b[^>]*>", t):
                self.assertRegex(img, r'\balt="', f"{rel}: {img}")
                self.assertRegex(img, r'\bwidth="\d+"', f"{rel}: {img}")
                self.assertRegex(img, r'\bheight="\d+"', f"{rel}: {img}")
        home = read(os.path.join(SITE, "index.html"))
        self.assertRegex(home, r'href="(tel|mailto):')

    def test_internal_links_exist(self):
        for p in files(".html"):
            base = os.path.dirname(p)
            for u in re.findall(r'(?:href|src|srcset)="([^"#?]+)', read(p)):
                for part in u.split(","):
                    part = part.strip().split(" ")[0]
                    if not part or re.match(r"^(https?:|mailto:|tel:|data:|javascript:)", part) or part.startswith("/api/"):
                        continue
                    target = os.path.normpath(os.path.join(SITE, part.lstrip("/")) if part.startswith("/") else os.path.join(base, part))
                    if os.path.isdir(target):
                        target = os.path.join(target, "index.html")
                    self.assertTrue(os.path.exists(target), f"{os.path.relpath(p, SITE)} → {part}")

    def test_images_small(self):
        for p in files(".jpg", ".png", ".webp", ".avif"):
            self.assertLess(os.path.getsize(p), 1_500_000, p)

    def test_portal_bausteine_and_no_own_banner(self):
        for p in files(".html"):
            t = read(p)
            self.assertIn('<span data-mk="cookies"></span>', t, p)
            self.assertNotIn("consent", re.sub(r"consent-row|t-consent|k-consent|g-consent|f-consent|w-consent", "", t), p)
            self.assertIsNone(re.search(r'<script[^>]+portal\.markentrix|data-site=', t), p)  # Skript setzt der Upload selbst ein
        self.assertIn('data-mk="bewertungen"', read(os.path.join(SITE, "index.html")))
        cfg = read(os.path.join(SITE, "config.js"))
        self.assertNotIn("ga4", cfg)
        self.assertNotIn("hosts", cfg)
        self.assertNotIn("paypalMe", cfg)  # kommt aus /api/verfuegbarkeit

    def test_forms_consent_honeypot_email(self):
        for p in files(".html"):
            t = read(p)
            for form in re.findall(r"<form\b[^>]*data-form=.*?</form>", t, re.S):  # Anfrageformulare (der Preisrechner sendet nichts)
                rel = os.path.relpath(p, SITE)
                self.assertRegex(form, r'name="einwilligung"[^>]*required', rel)
                self.assertRegex(form, r'name="website"[^>]*tabindex="-1"[^>]*autocomplete="off"', rel)
                self.assertRegex(form, r'name="email"[^>]*required', rel)
                self.assertIn('datenschutz.html"', form, rel)
        termin = read(os.path.join(SITE, "termin.html"))
        self.assertRegex(termin, r'name="telefon"[^>]*required')
        self.assertRegex(termin, r'name="agb"[^>]*required')


class TestBuild(unittest.TestCase):
    def test_sitemap_and_robots(self):
        import xml.etree.ElementTree as ET
        sm = read(os.path.join(SITE, "sitemap.xml"))
        root = ET.fromstring(sm.encode())  # Namensraum trotz Zeichenreferenz korrekt
        self.assertEqual(root.tag, "{http" + "://www.sitemaps.org/schemas/sitemap/0.9}urlset")
        self.assertIn("/ratgeber/", sm)
        self.assertIn("/agb.html", sm)
        self.assertNotIn("danke.html", sm)
        robots = read(os.path.join(SITE, "robots.txt"))
        self.assertIn("Disallow: /api/", robots)
        self.assertNotIn("/admin", robots)
        self.assertIn("GPTBot", robots)

    def test_json_ld_valid(self):
        for p in files(".html"):
            for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', read(p), re.S):
                json.loads(blob)

    def test_seo_title_and_description_lengths(self):
        rel = [os.path.relpath(p, SITE) for p in files(".html")]
        self.assertGreater(len(rel), 20)
        self.assertEqual(builder.seo_lengths(SITE, rel), [])

    def test_price_placeholders_resolved(self):
        for p in files(".html", ".txt", ".xml"):
            t = read(p)
            self.assertNotIn("{ab:", t, p)
            self.assertNotIn("{preis:", t, p)
        self.assertIn("ab 299 €", read(os.path.join(SITE, "leistungen/innenaufbereitung-celle.html")))

    def test_formal_address_everywhere(self):
        """Kund:innen werden gesiezt: keine Du-Ansprache in Seiten, Texten und Skripten."""
        pat = re.compile(r"\b(du|dich|dir|dein|deine|deinen|deinem|deiner|deines|euch|euer|eure|euren|eurem|eurer|ruf|schick|melde)\b", re.I)
        hits = []
        for p in files(".html", ".txt", ".xml", ".js"):
            t = read(p)
            if p.endswith(".js"):
                t = " ".join(re.findall(r'"([^"]*)"', t))
            t = re.sub(r"<script[^>]*>.*?</script>", " ", t, flags=re.S)
            t = re.sub(r"<[^>]+>", " ", t)
            hits += [f"{os.path.basename(p)}: {m.group(0)} …{t[max(0, m.start() - 30):m.end() + 30]!r}" for m in pat.finditer(t)]
        self.assertEqual(hits[:10], [])

    def test_no_inline_scripts(self):
        for p in files(".html"):
            t = read(p)
            self.assertIsNone(re.search(r'<script(?![^>]*(?:\bsrc=|type="application/ld\+json"))[^>]*>', t), p)
            self.assertIsNone(re.search(r'\son(click|submit|load|change)=', t), p)

    def test_owner_card_and_verification_only_when_filled(self):
        home = read(os.path.join(SITE, "index.html"))
        self.assertIn("owner-card", home)
        self.assertNotIn("google-site-verification", home)
        tmp = tempfile.mkdtemp(prefix="elb-owner-")
        content = os.path.join(tmp, "content")
        shutil.copytree(os.path.join(ROOT, "content"), content, ignore=shutil.ignore_patterns(".media-cache"))
        p = os.path.join(content, "site.json")
        d = json.load(open(p, encoding="utf-8"))
        d["about"] = {"name": "", "role": "", "photo": "", "since": "", "text": ""}
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        builder.build(content, os.path.join(tmp, "leer"), os.path.join(ROOT, "static"), quiet=True)
        self.assertNotIn("owner-card", read(os.path.join(tmp, "leer", "index.html")))
        d["about"] = {"name": "Max Muster", "role": "Inhaber", "photo": "", "since": "2023", "text": "Ich bereite jedes Auto selbst auf."}
        d["verification"] = {"google": "abc123", "bing": ""}
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        builder.build(content, os.path.join(tmp, "out"), os.path.join(ROOT, "static"), quiet=True)
        home = read(os.path.join(tmp, "out", "index.html"))
        self.assertIn("Max Muster", home)
        self.assertIn('<meta name="google-site-verification" content="abc123">', home)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_scheiben_promo_and_hours(self):
        t = read(os.path.join(SITE, "leistungen/scheibenversiegelung-celle.html"))
        if "2027-02-28" >= __import__("datetime").date.today().isoformat():
            self.assertIn("is-promo", t)
        ld = read(os.path.join(SITE, "index.html"))
        self.assertIn('"dayOfWeek":["Wednesday"],"opens":"09:00"', ld)


class TestEnglish(unittest.TestCase):
    """Englische Fassung unter /en/: vollständig übersetzt, gleiche Struktur, Umschalter und hreflang."""

    def de_pages(self):
        return sorted(os.path.relpath(p, SITE) for p in files(".html") if not os.path.relpath(p, SITE).startswith("en" + os.sep))

    def test_every_page_has_english_twin(self):
        for rel in self.de_pages():
            self.assertTrue(os.path.exists(os.path.join(SITE, "en", rel)), rel)

    def test_nothing_missing_and_no_broken_translation(self):
        self.assertEqual(list(RESULT["missing"])[:10], [])
        self.assertEqual([w for w in RESULT["warnings"] if "Platzhalter" in w or "Zahlen" in w], [])

    def test_lang_meta_hreflang_and_switch(self):
        for rel in self.de_pages():
            de, en = read(os.path.join(SITE, rel)), read(os.path.join(SITE, "en", rel))
            url = "/" + rel.replace(os.sep, "/")
            url = "/" if url == "/index.html" else url
            self.assertIn('<meta property="og:locale" content="en_GB">', en, rel)
            self.assertIn(f'<link rel="canonical" href="https://www.elbdetail.de/en{url}">', en, rel)
            for t in (de, en):
                self.assertIn(f'hreflang="en" href="https://www.elbdetail.de/en{url}"', t, rel)
                self.assertIn(f'hreflang="de" href="https://www.elbdetail.de{url}"', t, rel)
                self.assertIn('hreflang="x-default"', t, rel)
                self.assertEqual(t.count('class="lang-switch"'), 1, rel)
                self.assertNotIn("<!--lang-switch-->", t, rel)
            self.assertRegex(en, r'<a href="[^"]+" hreflang="en" lang="en" aria-label="English" aria-current="true">EN</a>', rel)
            self.assertRegex(de, r'<a href="[^"]+" hreflang="de" lang="de" aria-label="Deutsch" aria-current="true">DE</a>', rel)

    def test_no_german_left_in_english_pages(self):
        pat = re.compile(r"\b(und|oder|nicht|Sie|Ihr|Ihre|Ihren|Ihrem|für|mit|bei|wir|unser|unsere|ist|sind|werden|auf|zum|zur|vom)\b")
        hits = []
        for rel in self.de_pages():
            t = read(os.path.join(SITE, "en", rel))
            t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S)
            t = re.sub(r'<a [^>]*lang="de"[^>]*>.*?</a>', " ", t)
            for attr in re.findall(r'(?:alt|title|aria-label|placeholder|content)="([^"]*)"', t):
                hits += [f"{rel} [Attribut]: {attr[:80]}" for _ in pat.finditer(attr)][:1]
            text = html.unescape(re.sub(r"<[^>]+>", " ", t))
            hits += [f"{rel}: …{text[max(0, m.start() - 40):m.end() + 40]!r}" for m in pat.finditer(text)]
        self.assertEqual(hits[:15], [])

    def test_english_config_and_legal_note(self):
        cfg = read(os.path.join(SITE, "en", "config.js"))
        self.assertIn('"lang":"en"', cfg)
        self.assertIn('"t":{', cfg)
        self.assertNotIn("paypalMe", cfg)
        for rel in ("impressum.html", "datenschutz.html", "agb.html", "widerruf.html"):
            self.assertIn("Only the German version is legally binding", read(os.path.join(SITE, "en", rel)), rel)
            self.assertNotIn("legal-lang-note", read(os.path.join(SITE, rel)), rel)
        self.assertIn('data-mk="bewertungen"', read(os.path.join(SITE, "en", "index.html")))

    def test_sitemap_has_both_languages(self):
        sm = read(os.path.join(SITE, "sitemap.xml"))
        self.assertIn("<loc>https://www.elbdetail.de/en/</loc>", sm)
        self.assertIn("<loc>https://www.elbdetail.de/en/termin.html</loc>", sm)


if __name__ == "__main__":
    unittest.main()
