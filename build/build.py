#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ElbDetail – statischer Website-Generator.

    python3 build/build.py                         # baut nach ./website-fertig (Upload ins Markentrix-Portal)

Liest alle Inhalte aus content/ (JSON + Markdown), kopiert static/ und erzeugt
die komplette Website inklusive Sitemap, robots.txt, llms.txt und config.js.
"""
import argparse
import email.utils
import datetime
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import agb  # noqa: E402
import core  # noqa: E402
import conversion  # noqa: E402
import i18n  # noqa: E402
import images  # noqa: E402
import pages  # noqa: E402
import ratgeber  # noqa: E402
import seo  # noqa: E402

ROOT = os.path.dirname(HERE)


def minify_css(css):
    """Einfacher, sicherer CSS-Minifier: Kommentare und Leerraum entfernen, Zeichenketten bleiben unverändert."""
    import re
    out, i, n = [], 0, len(css)
    while i < n:
        ch = css[i]
        if ch in "\"'":
            j = i + 1
            while j < n and css[j] != ch:
                j += 2 if css[j] == "\\" else 1
            out.append(css[i:j + 1]); i = j + 1; continue
        if css.startswith("/*", i):
            j = css.find("*/", i + 2); i = n if j == -1 else j + 2; continue
        out.append(ch); i += 1
    s = "".join(out)
    parts = re.split(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')', s)
    for k in range(0, len(parts), 2):
        t = re.sub(r"\s+", " ", parts[k])
        t = re.sub(r"\s*([{};,>])\s*", r"\1", t)
        t = re.sub(r":\s+", ":", t)
        t = t.replace(";}", "}")
        parts[k] = t
    return "".join(parts).strip() + "\n"


def config_js(site):
    pr = site.pricing
    cfg = {
        "name": site.s["name"],
        "whatsapp": site.s["whatsapp"],
        "phone": site.s["phone"],
        "phoneDisplay": site.s["phoneDisplay"],
        "email": site.s["email"],
        "api": "/api",
        "classes": [{"key": c["key"], "name": c["name"], "short": c["short"], "onRequest": bool(c.get("onRequest")), "note": c.get("note", "")} for c in pr["classes"]],
        "packages": [{"key": p["key"], "name": p["name"], "prices": p["prices"]} for p in pr["packages"]]
                    + ([{"key": "winter", "name": site.winter()["name"], "prices": site.winter()["prices"]}] if site.winter() else [])
                    + ([{"key": "scheiben", "name": "Scheibenkeramik (C² Glass Ceramic)", "scope": {n: p for n, p, _ in site.addon_items("scheiben")}}]
                       if site.addon("scheiben") else []),
        "vouchers": site.s["vouchers"],
        "voucherValidYear": int(site.s["standIso"][:4]) + 3,
        "booking": {"owner": (site.s.get("about") or {}).get("name") or "",
                    "depositPercent": (site.s.get("booking") or {}).get("depositPercent", 15),
                    "surcharge": (site.s.get("booking") or {}).get("conditionSurcharge") or {}, "keramikMin": site.min_price("keramik") if pr.get("ceramic") else None},
    }
    return "/* automatisch erzeugt – nicht bearbeiten */\nwindow.ELB=" + json.dumps(cfg, ensure_ascii=False, separators=(",", ":")) + ";\n"


def build(content_dir, out_dir, static_dir, quiet=False):
    t0 = time.time()
    site = core.Site(content_dir)
    site.static_dir = static_dir
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(static_dir, out_dir)
    written = []

    def write(rel, text):
        p = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(rel)

    write("config.js", config_js(site))
    css_path = os.path.join(out_dir, "styles.css")
    with open(css_path, encoding="utf-8") as f:
        css = f.read()
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(minify_css(css))
    for name in ("styles.css", "script.js", "config.js"):
        with open(os.path.join(out_dir, name), "rb") as f:
            site.asset_v[name] = hashlib.sha1(f.read()).hexdigest()[:10]

    site.media = images.process(os.path.join(content_dir, "media"), out_dir, os.path.join(content_dir, ".media-cache"))

    pages.build_home(site, write)
    pages.build_preise(site, write)
    pages.build_kontakt(site, write)
    for sv in site.services:
        pages.build_service(site, sv, write)
    conversion.build_termin(site, write)
    conversion.build_gutscheine(site, write)
    conversion.build_firmen(site, write)
    conversion.build_winter(site, write)
    conversion.build_care(site, write)
    conversion.build_angebote(site, write)
    pages.build_about(site, write)
    pages.build_zertifikate(site, write)
    ratgeber.build_index(site, write)
    for a in site.articles:
        ratgeber.build_article(site, a, write)
    pages.build_legal(site, write)
    agb.build_agb(site, write)
    agb.build_widerruf(site, write)
    pages.build_404(site, write)
    pages.build_danke(site, write)

    iso = site.s["standIso"]
    sm = [("/", iso, "1.0", "weekly")]
    sm += [(f"/leistungen/{s['slug']}.html", iso, "0.8", "monthly") for s in site.services]
    sm += [("/preise.html", iso, "0.9", "monthly"), ("/kontakt.html", iso, "0.5", "yearly"), ("/ueber-uns.html", iso, "0.6", "yearly"), ("/zertifikate.html", iso, "0.6", "yearly"),
           ("/elbdetail-care.html", iso, "0.7", "monthly"), ("/angebote.html", iso, "0.8", "weekly")]
    sm += [("/termin.html", iso, "0.9", "monthly"), ("/gutscheine.html", iso, "0.7", "monthly"), ("/firmenkunden.html", iso, "0.7", "monthly"),
           ("/aktion/winterschutz.html", iso, "0.7", "monthly"), ("/ratgeber/index.html", iso, "0.7", "weekly"), ("/ratgeber/winter.html", iso, "0.7", "monthly")]
    sm += [(f"/ratgeber/{a['slug']}.html", a.get("updated") or a.get("date") or iso, "0.6", "monthly") for a in site.articles]
    sm += [("/impressum.html", iso, "0.2", "yearly"), ("/datenschutz.html", iso, "0.2", "yearly"), ("/agb.html", iso, "0.2", "yearly")]
    with open(os.path.join(static_dir, "script.js"), encoding="utf-8") as f:
        en = i18n.build_en(out_dir, written, content_dir, site.url, config_js(site), f.read())
    written += en["written"]
    sm += [("/en" + p, d, pr, f) for p, d, pr, f in sm]
    home_links(out_dir, [w for w in written if w.endswith(".html")])
    write("sitemap.xml", seo.sitemap(site, sm))
    write("robots.txt", seo.robots(site))
    write("llms.txt", seo.llms(site))
    write("llms-full.txt", seo.llms(site, full=True))
    write("site.webmanifest", seo.manifest(site))
    rss = seo.rss(site)
    for a in site.articles:  # RFC-822-Datum für RSS
        d = a.get("date")
        if d:
            dt = datetime.datetime.strptime(d, "%Y-%m-%d").replace(hour=8, tzinfo=datetime.timezone.utc)
            rss = rss.replace(f"<pubDate>{d}</pubDate>", f"<pubDate>{email.utils.format_datetime(dt)}</pubDate>")
    write("ratgeber/feed.xml", rss)
    write("build-info.json", json.dumps({"built": datetime.datetime.now().isoformat(timespec="seconds"), "pages": len([w for w in written if w.endswith(".html")]),
                                          "articles": len(site.articles), "images": len(site.media)}, ensure_ascii=False))

    warnings = []
    L = site.s.get("legal", {})
    for k, label in (("owner", "Inhaber im Impressum (vollständiger Name)"), ("vatId", "USt-IdNr."), ("mailProvider", "E-Mail-Anbieter in der Datenschutzerklärung")):
        if k == "vatId" and L.get("smallBusiness"):
            continue
        if not L.get(k):
            warnings.append(f"Platzhalter offen: {label}")
    if not site.s.get("googleReviewUrl"):
        warnings.append("Google-Bewertungslink fehlt (Grunddaten → googleReviewUrl)")
    if not any(g.get("before") in site.media and g.get("after") in site.media for g in site.gallery):
        warnings.append("Keine Vorher/Nachher-Fotos hochgeladen")
    if not (site.s.get("about") or {}).get("photo") in site.media:
        warnings.append("Foto von René fehlt (Grunddaten → Über uns → Foto)")
    if not (site.s.get("about") or {}).get("name"):
        warnings.append("Inhaber-Karte fehlt (Grunddaten → Über uns: Name, Foto, kurzer Text)")
    if en["missing"]:
        warnings.append(f"{len(en['missing'])} Texte ohne englische Übersetzung (python3 build/i18n_tool.py fehlend)")
    warnings += en["bad"]
    warnings += seo_lengths(out_dir, written)
    if not quiet:
        print(f"Fertig: {len(written)} Dateien, {len([w for w in written if w.endswith('.html')])} Seiten, {len(site.articles)} Artikel, "
              f"{len(site.media)} Bilder in {time.time() - t0:.1f}s → {out_dir}")
        for w in warnings:
            print("Hinweis:", w)
    return {"files": len(written), "warnings": warnings, "missing": en["missing"], "seen": en["seen"]}


HOMES = ("index.html", "en/index.html")  # Startseiten: kanonisch ist die Ordner-Adresse („/“ bzw. „/en/“)


def home_links(out_dir, pages):
    """Links auf index.html der Startseite auf die Ordner-Adresse umstellen (index.html → ./, ../index.html → ../).
    Sonst kennt Google zwei Adressen derselben Seite und meldet „Alternative Seite mit richtigem kanonischen Tag“."""
    pat = re.compile(r'href="(/|(?:\.\./)*)((?:en/)?)index\.html(#[^"]*)?"')
    for rel in pages:
        p = os.path.join(out_dir, rel)
        with open(p, encoding="utf-8") as f:
            src = f.read()
        base = os.path.dirname(rel)

        def rep(m):
            pre, en, frag = m.group(1), m.group(2), m.group(3) or ""
            target = (en + "index.html") if pre == "/" else os.path.normpath(os.path.join(base, pre + en + "index.html")).replace(os.sep, "/")
            if target not in HOMES:
                return m.group(0)  # z. B. ratgeber/index.html: bleibt, so steht sie auch als kanonische Adresse
            return f'href="{(pre + en) or "./"}{frag}"'
        new = pat.sub(rep, src)
        if new != src:
            with open(p, "w", encoding="utf-8") as f:
                f.write(new)


TITLE_MAX, DESC_MIN, DESC_MAX = 59, 110, 160  # Markentrix: Titel unter 60 Zeichen


def seo_lengths(out_dir, written):
    """Prüft Titel- und Beschreibungslängen aller indexierbaren Seiten (Google kürzt sonst in der Trefferliste)."""
    out = []
    for rel in sorted(w for w in written if w.endswith(".html")):
        with open(os.path.join(out_dir, rel), encoding="utf-8") as f:
            h = f.read()
        if 'name="robots" content="noindex' in h:
            continue
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        d = re.search(r'<meta name="description" content="(.*?)"', h, re.S)
        t = html.unescape(t.group(1)) if t else ""
        d = html.unescape(d.group(1)) if d else ""
        if len(t) > TITLE_MAX:
            out.append(f"Titel zu lang ({len(t)} von max. {TITLE_MAX} Zeichen): {rel}")
        if not DESC_MIN <= len(d) <= DESC_MAX:
            out.append(f"Beschreibung {'zu kurz' if len(d) < DESC_MIN else 'zu lang'} ({len(d)} Zeichen, ideal {DESC_MIN}–155): {rel}")
    return out


def main():
    ap = argparse.ArgumentParser(description="ElbDetail Website bauen")
    ap.add_argument("--content", default=os.path.join(ROOT, "content"))
    ap.add_argument("--static", default=os.path.join(ROOT, "static"))
    ap.add_argument("--out", default=os.path.join(ROOT, "website-fertig"))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    build(a.content, a.out, a.static, a.quiet)


if __name__ == "__main__":
    main()
