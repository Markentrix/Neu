#!/usr/bin/env python3
"""Erzeugt thema.css: drei Farbvarianten (A Nebel, B Tiefsee-Rhythmus, C Küstennebel) als Überlagerung von mx.css.
Aufruf: python3 gen_thema.py <mx.css> <thema.css>   (nur Vorschau, nicht Teil der Auslieferung)"""
import re, sys

SRC, OUT = sys.argv[1], sys.argv[2]
css = open(SRC, encoding='utf-8').read()

THEMES_EXTRA = {}
THEMES = {
    # soft = Seitengrund, linen = Flächen/Linien, border = Rahmen, nebel = zarte Hinweisfläche
    'a': dict(soft='#F3F7F9', linen='#DCE7EC', border='#D5E1E7', nebel='#E6F1F6', neben='#465A62'),
    'b': dict(soft='#F4F6F7', linen='#E0E6E9', border='#D8DFE3', nebel='#E6F1F6', neben='#465A62'),
    'c': dict(soft='#0A1A20', linen='#0F2A33', border='#1E3F4B', nebel='#143743', neben='#A9BFC7'),
}

def flat_rules(text):
    """Liefert (media, selektor, deklarationen) für alle Regeln, auch innerhalb von @media."""
    res, i, n = [], 0, len(text)
    stack = []  # offene @media
    buf_start = 0
    depth = 0
    sel_start = 0
    while i < n:
        c = text[i]
        if text.startswith('/*', i):
            j = text.find('*/', i + 2); i = (j + 2) if j > 0 else n; sel_start = i if depth == 0 or stack and depth == len(stack) else sel_start; continue
        if c == '{':
            head = text[sel_start:i].strip()
            if head.startswith('@media') or head.startswith('@supports'):
                stack.append(head); depth += 1; sel_start = i + 1
            elif head.startswith('@'):
                # @font-face, @keyframes: überspringen
                d = 1; j = i + 1
                while j < n and d:
                    d += (text[j] == '{') - (text[j] == '}'); j += 1
                i = j; sel_start = i; continue
            else:
                j = text.find('}', i)
                res.append((tuple(stack), head, text[i + 1:j]))
                i = j + 1; sel_start = i; continue
            i += 1; continue
        if c == '}':
            if stack: stack.pop(); depth -= 1
            sel_start = i + 1
        i += 1
    return res

rules = flat_rules(css)

def split_props(decl):
    """Teilt Deklarationen an Semikolons außerhalb von Klammern und Anführungszeichen."""
    out, buf, depth, q = [], '', 0, ''
    for ch in decl:
        if q:
            buf += ch
            if ch == q: q = ''
            continue
        if ch in '"\'': q = ch; buf += ch; continue
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
        if ch == ';' and depth == 0:
            if buf.strip(): out.append(buf.strip())
            buf = ''
        else: buf += ch
    if buf.strip(): out.append(buf.strip())
    return out

def wrap(media, sel_list, prefix, body):
    parts = []
    for x in sel_list.split(','):
        x = x.strip()
        if not x: continue
        if re.match(r'html\b(?!\[)', x) and not x.startswith('html.'): parts.append(prefix + x[4:])
        else: parts.append(prefix + ' ' + x)
    r = '%s{%s}' % (','.join(parts), body)
    for m in reversed(media): r = '%s{%s}' % (m, r)
    return r

def mix(hexc, rgb_from, t):
    return hexc

BG_PROP = re.compile(r'^background(-color)?$', re.I)
COL_PROP = re.compile(r'^(color|fill|stroke|border(-top|-bottom|-left|-right)?-color|text-decoration-color|outline-color|caret-color)$', re.I)
BORD_PROP = re.compile(r'^(border(-top|-bottom|-left|-right)?|outline)$', re.I)
RGB = {'F7F4EE': (247, 244, 238), 'EAE2D3': (234, 226, 211)}

def hex_to_rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

out = ['/* Vorschau Farbvarianten, erzeugt von vorlagen/farbvarianten/gen_thema.py. Nicht Teil der Auslieferung. */']

# ── A und B: Creme (#F7F4EE) und Leinen (#EAE2D3) durch kühle Töne ersetzen, auch als rgba ──
LIT = re.compile(r'#(F7F4EE|EAE2D3)|rgba\((247,244,238|234,226,211),', re.I)
def lit_sub(v, t):
    def h(m):
        if m.group(1): return t['soft'] if m.group(1).upper() == 'F7F4EE' else t['linen']
        r, g, b = hex_to_rgb(t['soft'] if m.group(2).startswith('247') else t['linen'])
        return 'rgba(%d,%d,%d,' % (r, g, b)
    return LIT.sub(h, v)

for k, t in THEMES.items():
    p = 'html[data-thema="%s"]' % k
    if k == 'c':
        out.append(':root[data-thema="c"]{--kreide:#0A1A20;--soft:#0A1A20;--leinen:#0F2A33;--linen:#0F2A33;--cool:#0F2A33;--border:#1E3F4B;--border-strong:rgba(234,242,245,.5);--nebel:#143743;--grad-soft:#143743;--nebentext:#A9BFC7;--muted:#A9BFC7;--white:#11303A;--text:#EAF2F5;--ink:#EAF2F5;--link:#7CC3DF;--blue-text:#7CC3DF;--violet-text:#7CC3DF;--shadow-sm:0 1px 2px rgba(0,0,0,.4);--shadow-md:0 6px 16px rgba(0,0,0,.45);--shadow-lg:0 12px 28px rgba(0,0,0,.5);color-scheme:dark}')
        continue
    root = ':root[data-thema="K"]{--kreide:S;--soft:S;--leinen:L;--linen:L;--cool:L;--border:B;--nebel:N;--grad-soft:N;--nebentext:T;--muted:T}'
    for a, b in (('S', t['soft']), ('L', t['linen']), ('B', t['border']), ('N', t['nebel']), ('T', t['neben'])):
        root = root.replace(':' + a + ';', ':' + b + ';').replace(':' + a + '}', ':' + b + '}')
    out.append(root.replace('"K"', '"%s"' % k))
    for media, sel, decl in rules:
        if sel.startswith(':root') or not LIT.search(decl): continue
        ch = [pp for pp in split_props(decl) if LIT.search(pp)]
        ch = [lit_sub(pp, t) for pp in ch]
        out.append(wrap(media, sel, p, ';'.join(ch)))

# ── B: vorhandene Regeln für dunkle Flächen (.sec--dark) auf ausgewählte Abschnitte übertragen ──
B_TIEFSEE = ['.ba-sec']
B_PFAU = ['.deal-sec']
for media, sel, decl in rules:
    if '.sec--dark' not in sel: continue
    for tgt in B_TIEFSEE + B_PFAU:
        s2 = ','.join(x.strip().replace('.sec--dark', tgt) for x in sel.split(',') if '.sec--dark' in x)
        out.append(wrap(media, s2, 'html[data-thema="b"]', decl))

# ── C „Nacht“: Hell-Dunkel-Umkehr aus den vorhandenen Regeln, nur geänderte Eigenschaften ──
C = dict(ground='#0A1A20', linen='#0F2A33', card='#11303A', band='#0F3340')
KEEP_BG = re.compile(r'(--copper|--kupfer|#C67432|--pfau-hell|--kupfer-hell|#F1A268|#62B2D0)', re.I)
INKV = re.compile(r'var\(--(?:navy|text|tiefsee|black)\)|#0C2128', re.I)
PFAUV = re.compile(r'var\(--(?:pfau|blue|cyan|violet|link|blue-text|violet-text)\)|#045268', re.I)
EXCL_C = re.compile(r'\.ill\b|\.bk-(site|bar|logo|nav|hero|eyebrow|h1|sub|btns|btn|btn--2|btn--sm|btn--wa|orte|blocks|block|block--form|chips|tiles|social|profil)\b')
def c_bg(v):
    v = re.sub(r'#FFFFFF|#FFF\b', C['card'], v, flags=re.I)
    v = re.sub(r'rgba\(255,255,255,', 'rgba(10,26,32,', v)
    v = re.sub(r'rgba\(247,244,238,', 'rgba(10,26,32,', v); v = re.sub(r'rgba\(234,226,211,', 'rgba(15,42,51,', v)
    v = re.sub(r'#F7F4EE', C['ground'], v, flags=re.I); v = re.sub(r'#EAE2D3', C['linen'], v, flags=re.I); v = re.sub(r'#E1F0F6', '#143743', v, flags=re.I)
    v = INKV.sub(C['band'], v)
    return v
def c_col(v):
    v = INKV.sub('var(--ink)', v); v = PFAUV.sub('var(--pfau-hell)', v)
    v = re.sub(r'#F7F4EE', C['ground'], v, flags=re.I); v = re.sub(r'#EAE2D3', C['linen'], v, flags=re.I)
    v = re.sub(r'#4E5C5F', '#A9BFC7', v, flags=re.I)
    return v
def c_bord(v):
    v = re.sub(r'#EAE2D3|#F7F4EE', '#1E3F4B', v, flags=re.I)
    v = INKV.sub('rgba(234,242,245,.55)', v); v = PFAUV.sub('var(--pfau-hell)', v)
    return v
cn = 0
for media, sel, decl in rules:
    if sel.startswith(':root') or EXCL_C.search(sel): continue
    props = split_props(decl)
    keep = any(BG_PROP.match(pp.split(':', 1)[0].strip()) and KEEP_BG.search(pp) for pp in props if ':' in pp)
    ch = []
    for pp in props:
        if ':' not in pp: continue
        name, val = pp.split(':', 1); name = name.strip(); imp = ''
        if val.rstrip().endswith('!important'): imp = ' !important'; val = val.rstrip()[:-10]
        if BG_PROP.match(name): nv = c_bg(val)
        elif COL_PROP.match(name) and not keep: nv = c_col(val)
        elif BORD_PROP.match(name): nv = c_bord(val)
        else: continue
        if nv != val: ch.append('%s:%s%s' % (name, nv.strip(), imp))
    if not ch: continue
    out.append(wrap(media, sel, 'html[data-thema="c"]', ';'.join(ch))); cn += 1
print(cn, 'Regeln für Variante C')
out.append(open(__file__.replace('gen_thema.py', 'thema-hand.css'), encoding='utf-8').read())
open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print(len(out), 'Blöcke →', OUT)
