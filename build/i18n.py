# -*- coding: utf-8 -*-
"""Englische Fassung: liest jede fertige deutsche Seite und schreibt sie übersetzt nach en/<gleicher Pfad>.

Die deutsche Seite wird nicht neu zusammengesetzt, nur Textstellen und einzelne Attribute werden an ihrer
Position ersetzt. Übersetzt wird über eine Tabelle Deutsch → Englisch (content/i18n/en/*.json).

Schlüssel: der Text eines Blocks (Absatz, Überschrift, Listenpunkt, Button …) mit zusammengefasstem Leerraum.
Inline-Tags darin werden zu Platzhaltern: <t1>…</t1> für Elemente mit Inhalt, <t2/> für Bild, SVG, Zeilenumbruch.
Beispiel:  "Termin <t1>online</t1> anfragen"  →  "Book <t1>online</t1>"
"""
import glob
import hashlib
import html
import json
import os
import posixpath
import re
import urllib.parse
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
OPAQUE = {"script", "style", "svg", "textarea", "template", "noscript"}  # Inhalt wird nicht als Text behandelt
INLINE = {"a", "abbr", "b", "bdi", "br", "button", "cite", "code", "data", "del", "dfn", "em", "i", "img", "input", "ins", "kbd", "label",
          "mark", "q", "s", "samp", "small", "span", "strong", "sub", "sup", "svg", "time", "u", "var", "wbr"}
TEXT_ATTRS = {"alt", "title", "aria-label", "placeholder", "data-sb-text"}
META_TEXT = {"description", "og:title", "og:description", "og:image:alt", "twitter:title", "twitter:description"}
LD_SKIP = {"@context", "@type", "@id", "url", "image", "logo", "telephone", "email", "priceCurrency", "price", "sameAs", "datePublished",
           "dateModified", "dayOfWeek", "opens", "closes", "postalCode", "addressCountry", "addressRegion", "streetAddress", "addressLocality",
           "latitude", "longitude", "inLanguage", "priceRange", "contentUrl", "thumbnailUrl", "uploadDate", "duration", "ratingValue",
           "bestRating", "worstRating", "ratingCount", "reviewCount", "minPrice", "maxPrice", "validFrom", "validThrough", "item", "hasMap",
           "position", "foundingDate", "areaServed", "unitCode", "currenciesAccepted", "paymentAccepted", "keywords", "author", "legalName",
           "founder", "brand", "alternateName"}
LEGAL = {"impressum.html", "datenschutz.html", "agb.html", "widerruf.html"}
LEGAL_NOTE = ('<p class="legal-lang-note">This is a courtesy translation for our English-speaking customers. '
              'Only the German version is legally binding.</p>')
PH = re.compile(r"<(/?)t(\d+)(/?)>")


class Node:
    __slots__ = ("tag", "attrs", "s0", "s1", "e0", "e1", "children", "parent")

    def __init__(self, tag, attrs, s0, s1, parent):
        self.tag, self.attrs, self.s0, self.s1, self.parent = tag, dict(attrs), s0, s1, parent
        self.e0 = self.e1 = s1
        self.children = []


class _Parser(HTMLParser):
    """Baut einen Baum mit Quellpositionen (Start- und Endtag), ohne Text zu verändern."""

    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.src = src
        self.lines = [0]
        for m in re.finditer("\n", src):
            self.lines.append(m.end())
        self.root = Node("#root", [], 0, 0, None)
        self.root.e0 = self.root.e1 = len(src)
        self.stack = [self.root]
        self.opaque = []  # Kommentare und Doctype: nie Text

    def off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        s0 = self.off()
        n = Node(tag, attrs, s0, s0 + len(self.get_starttag_text()), self.stack[-1])
        self.stack[-1].children.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        s0 = self.off()
        n = Node(tag, attrs, s0, s0 + len(self.get_starttag_text()), self.stack[-1])
        self.stack[-1].children.append(n)

    def handle_endtag(self, tag):
        e0 = self.off()
        e1 = self.src.index(">", e0) + 1
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                for n in self.stack[i + 1:]:  # nicht geschlossene Elemente enden hier
                    n.e0 = n.e1 = e0
                self.stack[i].e0, self.stack[i].e1 = e0, e1
                del self.stack[i:]
                return

    def handle_comment(self, data):
        s0 = self.off()
        e = self.src.index("-->", s0) + 3
        n = Node("#comment", [], s0, e, self.stack[-1])
        self.stack[-1].children.append(n)

    def handle_decl(self, decl):
        s0 = self.off()
        self.opaque.append((s0, self.src.index(">", s0) + 1))


def parse(src):
    p = _Parser(src)
    p.feed(src)
    p.close()
    return p.root, p.opaque


def norm(s):
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip()


def has_words(s):
    return re.search(r"[A-Za-zÄÖÜäöüß]{2,}", PH.sub(" ", s)) is not None


class Translator:
    def __init__(self, table, site_url, rel):
        self.t, self.url, self.rel = table, site_url.rstrip("/"), rel
        self.missing = {}  # Schlüssel → Fundstelle
        self.seen = {}  # Schlüssel → Fundstellen (für das Werkzeug i18n_tool.py)
        self.bad = []

    # --------------------------------------------------------------- Nachschlagen
    def lookup(self, key, where):
        if not has_words(key):
            return key
        self.seen.setdefault(key, set()).add(f"{self.rel}|{where}")
        v = self.t.get(key)
        if v is None:
            self.missing.setdefault(key, f"{self.rel} ({where})")
            return key
        a = sorted(m.group(0) for m in PH.finditer(key))
        b = sorted(m.group(0) for m in PH.finditer(v))
        if a != b:
            self.bad.append(f"{self.rel}: Platzhalter passen nicht: {key!r} → {v!r}")
            return key
        if not set(numbers(key)) <= set(numbers(v)):
            self.bad.append(f"{self.rel}: Zahlen passen nicht: {key!r} → {v!r}")
        return v

    def text(self, s, where):
        """Schlichter Text (Attribut, JSON-LD): Leerraum am Rand bleibt."""
        if not s.strip():
            return s
        lead, trail = re.match(r"^\s*", s).group(0), re.search(r"\s*$", s).group(0)
        return lead + self.lookup(norm(s), where) + trail

    # --------------------------------------------------------------- Links
    def en_url(self, u):
        """Absolute Seiten-URL der eigenen Domain → englische Fassung."""
        if not u.startswith(self.url + "/") and u != self.url:
            return u
        path = u[len(self.url):] or "/"
        if path.startswith("/en/") or not is_page(path):
            return u
        return self.url + "/en" + path

    def link(self, u, attr):
        if not u:
            return u
        if u.startswith("https://wa.me/") and "?text=" in u:
            base, q = u.split("?text=", 1)
            return base + "?text=" + urllib.parse.quote(self.text(urllib.parse.unquote(q), "WhatsApp-Text"), safe="")
        if u.startswith("mailto:") and "?" in u:
            base, q = u.split("?", 1)
            parts = []
            for kv in q.split("&"):
                k, _, v = kv.partition("=")
                if k in ("subject", "body"):
                    v = urllib.parse.quote(self.text(urllib.parse.unquote(v), "E-Mail-Text"), safe="")
                parts.append(k + "=" + v)
            return base + "?" + "&".join(parts)
        if re.match(r"^[a-z][a-z0-9+.-]*:|^#|^//", u, re.I):
            return self.en_url(u) if attr in ("href", "content") else u
        if u.startswith("/"):
            if u.startswith(("/api/", "/en/")):
                return u
            path = u.split("#")[0].split("?")[0]
            return "/en" + u if is_page(path) or path == "/config.js" else u
        path = u.split("#")[0].split("?")[0]
        if not path or is_page(path) or posixpath.normpath(posixpath.join(posixpath.dirname(self.rel), path)) == "config.js":
            return u  # gleiche Ordnerstruktur unter en/
        return "../" + u

    # --------------------------------------------------------------- Tags
    def tag(self, raw, node):
        """Starttag: Textattribute übersetzen, Links umschreiben. Nur die Werte werden ersetzt."""
        a = node.attrs
        if node.tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            return raw
        if node.tag == "html":
            return re.sub(r'\blang="de"', 'lang="en"', raw)

        def rep(m):
            name, val = m.group(1), html.unescape(m.group(2))
            if name in TEXT_ATTRS:
                val = self.text(val, name)
            elif name == "content" and node.tag == "meta":
                key = a.get("name") or a.get("property") or ""
                if key in META_TEXT:
                    val = self.text(val, key)
                elif key == "og:locale":
                    val = "en_GB"
                elif key in ("og:url",):
                    val = self.en_url(val)
            elif name in ("href", "src", "action", "poster", "data-src"):
                val = self.link(val, "src" if node.tag == "link" and a.get("rel") != "canonical" else name)
            elif name == "srcset":
                val = ", ".join(" ".join([self.link(p.strip().split(" ")[0], "src")] + p.strip().split(" ")[1:]) for p in val.split(","))
            else:
                return m.group(0)
            return f'{m.group(0)[0]}{name}="{html.escape(val, quote=True)}"'
        return re.sub(r'\s([a-zA-Z:_-]+)="([^"]*)"', rep, raw)


def numbers(s):
    """Zahlen, die in der Übersetzung wieder vorkommen müssen (Preise, Jahre, Telefonnummern), ohne Datumsangaben."""
    s = re.sub(r"\b\d{1,2}\.\d{1,2}\.(\d{2,4})?", " ", PH.sub(" ", s))
    return re.findall(r"\d+", re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", s))


def is_page(path):
    return path in ("", "/") or path.endswith((".html", "/"))


# ----------------------------------------------------------------------------- Einheiten finden
def atom(n):
    """Ohne eigenen Text: wird im Schlüssel zu <tN/>."""
    return n.tag in VOID or n.tag in ("svg", "#comment")


def all_inline(n):
    if n.tag == "#comment":
        return True
    if n.tag in OPAQUE:
        return n.tag == "svg"
    if n.tag not in INLINE:
        return False
    return all(all_inline(c) for c in n.children)


def units(node, out):
    """Sammelt Textläufe: zusammenhängende Kinder aus Text und reinen Inline-Elementen innerhalb eines Blocks."""
    if node.tag in OPAQUE:
        return
    run, cursor = [], node.s1
    kids = node.children
    for c in kids:
        if all_inline(c):
            run.append(c)
            continue
        if run or node.s1 < c.s0:
            out.append((node, run, cursor, c.s0))
        run, cursor = [], c.e1
        units(c, out)
    out.append((node, run, cursor, node.e0))


class Unit:
    """Ein Textlauf zwischen den Quellpositionen a und b mit den Inline-Elementen darin."""

    def __init__(self, src, a, b, items):
        self.src, self.a, self.b, self.items = src, a, b, items

    def has_text(self, n):
        return not atom(n) and re.sub(r"<[^>]*>", "", self.src[n.s1:n.e0]).strip() != ""

    def segments(self):
        """Leerraum, Symbole am Rand und einzelne umschließende Elemente gehören nicht zum Schlüssel.
        Stehen mehrere Elemente mit Text nur durch Leerraum getrennt nebeneinander (Karten, Auswahlfelder),
        wird jedes für sich übersetzt."""
        src = self.src
        while True:
            while self.a < self.b and src[self.a].isspace():
                self.a += 1
            while self.b > self.a and src[self.b - 1].isspace():
                self.b -= 1
            it = self.items
            if it and it[0].s0 == self.a and not self.has_text(it[0]):
                self.a = _end(it[0])
                self.items = it[1:]
                continue
            if it and _end(it[-1]) == self.b and not self.has_text(it[-1]):
                self.b = it[-1].s0
                self.items = it[:-1]
                continue
            if len(it) == 1 and it[0].s0 == self.a and _end(it[0]) == self.b and not atom(it[0]):
                self.a, self.b, self.items = it[0].s1, it[0].e0, it[0].children
                continue
            if len(it) > 1 and sum(map(self.has_text, it)) > 1:
                gaps = [src[self.a:it[0].s0]] + [src[_end(x):y.s0] for x, y in zip(it, it[1:])] + [src[_end(it[-1]):self.b]]
                if all(not g.strip() for g in gaps):
                    out = []
                    for n in it:
                        if self.has_text(n):
                            out += Unit(src, n.s0, _end(n), [n]).segments()
                    return out
            return [self] if self.a < self.b else []

    def key(self):
        """Schlüssel mit Platzhaltern; parts merkt sich, welcher Platzhalter welchem Quelltext entspricht."""
        self.parts = {}
        counter = [0]
        out = []

        def walk(a, b, items):
            pos = a
            for n in items:
                out.append(html.unescape(self.src[pos:n.s0]))
                counter[0] += 1
                k = counter[0]
                if atom(n):
                    self.parts[f"<t{k}/>"] = (n, n.s0, _end(n))
                    out.append(f"<t{k}/>")
                else:
                    self.parts[f"<t{k}>"] = (n, n.s0, n.s1)
                    self.parts[f"</t{k}>"] = (None, n.e0, n.e1)
                    out.append(f"<t{k}>")
                    walk(n.s1, n.e0, n.children)
                    out.append(f"</t{k}>")
                pos = _end(n)
            out.append(html.unescape(self.src[pos:b]))
        walk(self.a, self.b, self.items)
        return norm("".join(out))


def _end(n):
    return n.s1 if n.tag in VOID or n.tag == "#comment" else n.e1


# ----------------------------------------------------------------------------- Seite übersetzen
def translate_page(src, rel, tr):
    root, _ = parse(src)
    edits = []  # (a, b, neuer Text)
    covered = []  # Bereiche, deren Starttags schon in einer Einheit bearbeitet werden

    def restore(raw_tag_src, node):
        return tr.tag(raw_tag_src, node) if node is not None else raw_tag_src

    raw_units = []
    units(root, raw_units)
    for parent, items, a, b in raw_units:
        if parent.tag in OPAQUE or parent.tag == "#root" and not items:
            continue
        for u in Unit(src, a, b, items).segments():
            key = u.key()
            if not key or not has_words(key):
                continue
            val = tr.lookup(key, parent.tag)
            pieces, pos = [], 0
            for m in PH.finditer(val):
                pieces.append(html.escape(val[pos:m.start()], quote=False))
                node, s, e = u.parts[m.group(0)]
                if node is not None and node.tag in ("svg", "#comment"):
                    pieces.append(src[s:e])
                elif node is not None:
                    pieces.append(restore(src[s:node.s1], node))
                else:
                    pieces.append(src[s:e])
                pos = m.end()
            pieces.append(html.escape(val[pos:], quote=False))
            out = re.sub(r"(\d) €", "\\1\u00a0€", "".join(pieces))
            edits.append((u.a, u.b, out))
            covered.append((u.a, u.b))

    def inside(p):
        return any(a <= p < b for a, b in covered)

    def walk(n):
        for c in n.children:
            if not inside(c.s0):
                new = tr.tag(src[c.s0:c.s1], c)
                if new != src[c.s0:c.s1]:
                    edits.append((c.s0, c.s1, new))
            if c.tag == "script" and c.attrs.get("type") == "application/ld+json":
                data = json.loads(src[c.s1:c.e0])
                data = ld(data, tr)
                edits.append((c.s1, c.e0, json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
            elif c.tag not in OPAQUE:
                walk(c)
    walk(root)

    edits.sort()
    out, pos = [], 0
    for a, b, t in edits:
        if a < pos:
            raise ValueError(f"{rel}: überlappende Ersetzung bei {a}")
        out.append(src[pos:a])
        out.append(t)
        pos = b
    out.append(src[pos:])
    res = "".join(out)
    if os.path.basename(rel) in LEGAL and rel.count("/") == 0:
        res = re.sub(r"(</h1>)", r"\1\n" + LEGAL_NOTE, res, count=1)
    return res


def ld(o, tr, key=None):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k == "inLanguage":
                out[k] = "en"
            elif k in ("url", "item") and isinstance(v, str):
                out[k] = tr.en_url(v)
            elif k in LD_SKIP:
                out[k] = v
            else:
                out[k] = ld(v, tr, k)
        return out
    if isinstance(o, list):
        return [ld(x, tr, key) for x in o]
    if isinstance(o, str) and has_words(o) and not re.match(r"^(https?:|mailto:|tel:|\+?\d)", o):
        return tr.text(o, "JSON-LD " + (key or ""))
    return o


# ----------------------------------------------------------------------------- Sprachumschalter
SWITCH = "<!--lang-switch-->"


def fill_switch(src, rel, lang):
    """Platzhalter im Kopf durch den Umschalter ersetzen: relative Links auf dieselbe Seite in der anderen Sprache."""
    depth = rel.count("/")
    name = posixpath.basename(rel)
    if lang == "de":
        de, en = name, "../" * depth + "en/" + rel
    else:
        de, en = "../" * (depth + 1) + rel, name
    cur = ' aria-current="true"'
    label = "Sprache wählen" if lang == "de" else "Choose language"
    sw = (f'<nav class="lang-switch" aria-label="{label}">'
          f'<a href="{de}" hreflang="de" lang="de" aria-label="Deutsch"{cur if lang == "de" else ""}>DE</a>'
          f'<a href="{en}" hreflang="en" lang="en" aria-label="English"{cur if lang == "en" else ""}>EN</a></nav>')
    return src.replace(SWITCH, sw)


# ----------------------------------------------------------------------------- Tabelle laden
def load_table(content_dir):
    t = {}
    for p in sorted(glob.glob(os.path.join(content_dir, "i18n", "en", "*.json"))):
        with open(p, encoding="utf-8") as f:
            for k, v in json.load(f).items():
                t[norm(k)] = v.strip() if isinstance(v, str) else v
    return t


def js_keys(script_src):
    """Alle Texte, die script.js über t("…") übersetzen lässt."""
    return sorted({json.loads('"' + m.group(1) + '"') for m in re.finditer(r'\bt\("((?:[^"\\]|\\.)*)"', script_src)})


def build_en(out_dir, written, content_dir, site_url, config_src, script_src):
    """Schreibt en/<seite> für jede deutsche Seite. Gibt fehlende Übersetzungen und Fehler zurück."""
    table = load_table(content_dir)
    missing, bad, done, seen = {}, [], [], {}
    cfg_src = en_config(table, site_url, config_src, script_src, missing, seen, bad)
    os.makedirs(os.path.join(out_dir, "en"), exist_ok=True)
    with open(os.path.join(out_dir, "en", "config.js"), "w", encoding="utf-8") as f:
        f.write(cfg_src)
    done.append("en/config.js")
    de_v = hashlib.sha1(config_src.encode("utf-8")).hexdigest()[:10]
    en_v = hashlib.sha1(cfg_src.encode("utf-8")).hexdigest()[:10]
    for rel in sorted(w for w in written if w.endswith(".html")):
        p = os.path.join(out_dir, rel)
        with open(p, encoding="utf-8") as f:
            src = f.read()
        tr = Translator(table, site_url, rel)
        en = translate_page(src, rel, tr)
        for k, v in tr.missing.items():
            missing.setdefault(k, v)
        for k, v in tr.seen.items():
            seen.setdefault(k, set()).update(v)
        bad += tr.bad
        with open(p, "w", encoding="utf-8") as f:
            f.write(fill_switch(src, rel, "de"))
        q = os.path.join(out_dir, "en", rel)
        os.makedirs(os.path.dirname(q), exist_ok=True)
        with open(q, "w", encoding="utf-8") as f:
            f.write(fill_switch(en, rel, "en").replace(f"config.js?v={de_v}", f"config.js?v={en_v}"))
        done.append("en/" + rel)
    return {"missing": missing, "bad": bad, "written": done, "seen": seen}


def en_config(table, site_url, config_src, script_src, missing, seen, bad):
    """config.js für /en/: Namen und Hinweise übersetzt, dazu die Texte für script.js (ELB.t)."""
    tr = Translator(table, site_url, "config.js")
    cfg = json.loads(re.search(r"window\.ELB=(.*);\s*$", config_src, re.S).group(1))
    for c in cfg.get("classes", []):
        for k in ("name", "short", "note"):
            if c.get(k):
                c[k] = tr.text(c[k], "Fahrzeugklasse")
    for pk in cfg.get("packages", []):
        pk["name"] = tr.text(pk["name"], "Paket")  # scope-Schlüssel bleiben: sie entsprechen den Formularwerten
    cfg["lang"] = "en"
    cfg["t"] = {k: tr.text(k, "script.js") for k in js_keys(script_src)}
    for k, v in tr.missing.items():
        missing.setdefault(k, v)
    for k, v in tr.seen.items():
        seen.setdefault(k, set()).update(v)
    bad += tr.bad
    return "/* automatisch erzeugt – nicht bearbeiten */\nwindow.ELB=" + json.dumps(cfg, ensure_ascii=False, separators=(",", ":")) + ";\n"
