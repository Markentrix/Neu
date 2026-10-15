# -*- coding: utf-8 -*-
"""Kleiner, abhängigkeitsfreier Markdown-Konverter für ElbDetail.

Unterstützt: Überschriften (## / ###), Absätze, Listen (- / 1.), Zitate (>),
Tabellen mit Kopfzeile, Trennlinie (---), **fett**, *kursiv*, `code`, [Links](url).
HTML im Quelltext wird immer escaped, damit gepflegte Inhalte die Seite nicht brechen.
"""
import html
import json
import re

_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)")
_CODE = re.compile(r"`([^`]+)`")


def _safe_href(url, prefix):
    url = url.strip()
    if url.startswith("/"):
        return prefix + url[1:] if url != "/" else (prefix or "./") + "index.html"
    if re.match(r"^(https?:|mailto:|tel:|#)", url):
        return url
    if re.match(r"^[\w\-./#?=&]+$", url):
        return url
    return "#"


def inline(text, prefix=""):
    """Wandelt Inline-Markdown in sicheres HTML um."""
    out = html.escape(text, quote=False)
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    out = _CODE.sub(keep_code, out)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        href = _safe_href(url, prefix)
        ext = href.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{html.escape(href)}"{attrs}>{label}</a>'

    out = _LINK.sub(link, out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _ITAL.sub(r"<em>\1</em>", out)
    out = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", out)
    return out


def _slug(text):
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:60] or "abschnitt"


def render(md, prefix="", heading_ids=True, toc=None):
    """Markdown -> HTML. `toc` (Liste) sammelt (id, Text) aller H2."""
    lines = md.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)
    used = set()

    def para(buf):
        if buf:
            out.append("<p>" + inline(" ".join(s.strip() for s in buf), prefix) + "</p>")

    buf = []
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            para(buf); buf = []; i += 1; continue
        m = re.match(r"^(#{2,4})\s+(.*)$", s)
        if m:
            para(buf); buf = []
            level = len(m.group(1))
            text = m.group(2).strip().rstrip("#").strip()
            attr = ""
            if heading_ids and level == 2:
                hid = _slug(text)
                while hid in used:
                    hid += "-2"
                used.add(hid)
                attr = f' id="{hid}"'
                if toc is not None:
                    toc.append((hid, text))
            out.append(f"<h{level}{attr}>{inline(text, prefix)}</h{level}>")
            i += 1; continue
        if re.match(r"^(-{3,}|\*{3,})$", s):
            para(buf); buf = []; out.append("<hr>"); i += 1; continue
        if s.startswith(">"):
            para(buf); buf = []
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote class="note"><p>' + inline(" ".join(q), prefix) + "</p></blockquote>")
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            para(buf); buf = []
            def cells(row):
                row = row.strip().strip("|")
                return [c.strip() for c in row.split("|")]
            head = cells(s); i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            th = "".join(f'<th scope="col">{inline(c, prefix)}</th>' for c in head)
            trs = ""
            for r in rows:
                tds = "".join((f'<th scope="row">{inline(c, prefix)}</th>' if k == 0 else f"<td>{inline(c, prefix)}</td>") for k, c in enumerate(r))
                trs += f"<tr>{tds}</tr>"
            out.append(f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tabelle, seitlich scrollbar"><table class="md-table"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        lm = re.match(r"^([-*]|\d+[.)])\s+(.*)$", s)
        if lm:
            para(buf); buf = []
            ordered = lm.group(1)[0].isdigit()
            items = []
            while i < n:
                t = lines[i].strip()
                mm = re.match(r"^([-*]|\d+[.)])\s+(.*)$", t)
                if mm:
                    items.append(mm.group(2)); i += 1
                elif t and items and lines[i].startswith(("  ", "\t")):
                    items[-1] += " " + t; i += 1
                else:
                    break
            check = all(re.match(r"^\[( |x|X)\]\s", it) for it in items)
            lis = []
            for it in items:
                if check:
                    done = it[1] in "xX"
                    it = it[3:].strip()
                    lis.append(f'<li class="{"done" if done else ""}">{inline(it, prefix)}</li>')
                else:
                    lis.append(f"<li>{inline(it, prefix)}</li>")
            tag = "ol" if ordered else "ul"
            cls = ' class="checklist"' if check else ""
            out.append(f"<{tag}{cls}>" + "".join(lis) + f"</{tag}>")
            continue
        buf.append(line); i += 1
    para(buf)
    return "\n".join(out)


def parse_frontmatter(text):
    """Liest JSON-Frontmatter (optional zwischen --- Zeilen) und gibt (meta, body) zurück."""
    t = text.lstrip("﻿").lstrip()
    if t.startswith("---"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
    meta, end = json.JSONDecoder().raw_decode(t)
    body = t[end:].lstrip()
    if body.startswith("---"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    return meta, body.strip() + "\n"


def write_frontmatter(meta, body):
    return json.dumps(meta, ensure_ascii=False, indent=2) + "\n\n" + body.strip() + "\n"


def plain(md):
    """Markdown -> Klartext (für llms-full.txt und Wortzählung)."""
    t = re.sub(r"^#{2,4}\s+", "", md, flags=re.M)
    t = _LINK.sub(r"\1", t)
    t = t.replace("**", "").replace("`", "")
    t = re.sub(r"(?<!\w)\*(\S.*?\S|\S)\*(?!\w)", r"\1", t)
    t = re.sub(r"^\|?\s*:?-{2,}.*$", "", t, flags=re.M)
    return t
