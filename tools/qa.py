#!/usr/bin/env python3
"""Markentrix · Qualitäts-Gate. Ein Aufruf, ein Ergebnis: python3 tools/qa.py

Baut die Seite, führt Build-Linkcheck, SEO-Audit und Crawl-Audit aus und prüft die Regeln, über die wir in der Praxis gestolpert sind
(siehe docs/QUALITAETSREGELN.md). Exit-Code 1 bei jedem FEHLER. HINWEISE sind keine Fehler, gehören aber angesehen.
tools/paket.sh ruft dieses Skript vor dem Packen auf. Browser-Tests (axe, Einwilligung, Formulare): tools/browser_tests/.
"""
import os, re, sys, glob, html, subprocess, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
errors, notes = [], []
def err(m): errors.append(m)
def note(m): notes.append(m)

def run(cmd, env=None):
    e = dict(os.environ); e.update(env or {})
    return subprocess.run(cmd, cwd=ROOT, env=e, capture_output=True, text=True)

# 1 Bauen und vorhandene Prüfungen --------------------------------------------------------------------------------
r = run([sys.executable, 'tools/build.py', '--check'])
if r.returncode != 0: err('Build oder Linkcheck fehlgeschlagen:\n' + '\n'.join(r.stdout.splitlines()[-6:]))
r = run([sys.executable, 'tools/seo_audit.py'])
if r.returncode != 0: err('SEO-Audit meldet Fehler:\n' + '\n'.join(l for l in r.stdout.splitlines() if l.startswith('FEHLER')))
r = run([sys.executable, '-I', 'tools/crawl_audit.py'])
sec = None
for line in r.stdout.splitlines():
    m = re.match(r'## (\S+)\s.*\((\d+) Einträge\)', line)
    if m: sec = m.group(1); continue
    if sec in ('1', '1b', '1c', '1d', '2', '5', '7') and line.startswith('  - ') and 'Title 6' not in line: err(f'Crawl-Audit {sec}: {line.strip()[2:]}')

# 2 Aktion nach Fristende wirklich aus dem HTML (nicht nur per Skript) ----------------------------------------------
run([sys.executable, 'tools/build.py'], env={'MX_TODAY': '2099-01-01'})
if re.search(r'data-deal-until|id="aktion"', open(os.path.join(DIST, 'index.html'), encoding='utf-8').read()):
    err('Befristetes Angebot steht nach Fristende noch im HTML (build.py expire_deals prüfen)')
run([sys.executable, 'tools/build.py'])  # wieder normal bauen

# 3 Seiten lesen -----------------------------------------------------------------------------------------------------
pages = {}
for f in sorted(glob.glob(DIST + '/**/*.html', recursive=True)):
    rel = f[len(DIST) + 1:-5]
    pages[rel] = open(f, encoding='utf-8').read()
def text_of(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
def main_of(t):
    m = re.search(r'<main.*?</main>', t, re.S); t = m.group(0) if m else t
    return re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', '', t, flags=re.S)
LEGAL = ('datenschutz', 'agb', 'impressum')
BAD = [('rechtssicher', 'Rechtssicherheit nicht zusagen'), ('24/7', 'Verfügbarkeitszusage'), ('nahtlos', 'Floskel'), ('ganzheitlich', 'Floskel'),
       ('maßgeschneidert', 'Floskel'), ('innovativ', 'Floskel'), ('Ihr Partner für', 'Floskel'), ('auf das nächste Level', 'Floskel'),
       ('Haftung für Links', 'pauschaler Haftungsausschluss'), ('jederzeit an eine', 'absolute Übergabezusage'), ('abmahnsicher', 'Rechtssicherheit nicht zusagen')]
RUND = {'blog/warum-ist-eine-website-wichtig'}  # dort geht es um Auffindbarkeit der Website, nicht um Erreichbarkeit

for rel, t in pages.items():
    if rel in ('404', 'danke', 'karte/index'): continue
    demo = rel.startswith('beispiel/')
    robots = re.search(r'name="robots" content="([^"]*)"', t); noindex = bool(robots and 'noindex' in robots.group(1))
    # Pflichtlinks auf jeder Seite, auch Beispiel- und Kartenseiten
    for target in ('/impressum', '/datenschutz'):
        if f'href="{target}"' not in t and f'href="{target}#' not in t: err(f'{rel}: kein Link auf {target}')
    if demo: continue
    # Überschriften
    hs = [(int(m.group(1)), text_of(m.group(2))) for m in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', main_of(t), re.S)]
    h1 = [h for l, h in hs if l == 1]
    if len(h1) != 1: err(f'{rel}: {len(h1)} H1')
    else:
        h = h1[0]
        raw = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', main_of(t), re.S).group(1)))  # wie der Browser: Tags ohne Leerzeichen
        if re.search(r'[a-zäöüß][.!?][A-ZÄÖÜ][a-zäöüß]', raw): err(f'{rel}: H1 ohne Leerzeichen zwischen Sätzen: {raw[:60]}')
        if len(h) > 90: err(f'{rel}: H1 {len(h)} Zeichen (über 90)')
        elif len(h) > 70 and not rel.startswith('blog/'): note(f'{rel}: H1 {len(h)} Zeichen (über 70)')
    prev = 0
    for l, h in hs:
        if prev and l > prev + 1: err(f'{rel}: Überschriftenebene übersprungen (H{prev} → H{l}: {h[:40]})')
        prev = l
    if not noindex:
        ti = text_of(re.search(r'<title>(.*?)</title>', t, re.S).group(1))
        if len(ti) > 70: err(f'{rel}: Title {len(ti)} Zeichen')
        elif len(ti) > 65: note(f'{rel}: Title {len(ti)} Zeichen')
    # interne Links
    seen = collections.defaultdict(set)
    for m in re.finditer(r'<a ([^>]*)href="(/[^"]*)"([^>]*)>(.*?)</a>', t, re.S):
        attrs, href, txt = m.group(1) + m.group(3), m.group(2), text_of(m.group(4))
        if '?' in href.split('#')[0] and 'nofollow' not in attrs: err(f'{rel}: interner Link mit Parameter ohne rel="nofollow": {href}')
        if len(txt) > 90: note(f'{rel}: sehr langer Linktext ({len(txt)}): {txt[:40]}…')
        if txt: seen[txt.lower()].add(href.split('#')[0])
    for k, v in seen.items():
        if len(v) > 1 and k not in ('mehr erfahren',): note(f'{rel}: gleicher Linktext „{k[:30]}“ mit {len(v)} Zielen')
    # Zierbilder: lieber CSS als <img alt="">
    deco = len(re.findall(r'<img[^>]*alt=""', t))
    if deco: note(f'{rel}: {deco} Zierbild(er) mit leerem alt (besser als CSS-Hintergrund)')
    # Formulare mit Unternehmer-Bestätigung
    for m in re.finditer(r'<form[^>]*data-lead="(Kontaktformular|Rückruf|Website-Check|Bewerbung)"[^>]*>(.*?)</form>', t, re.S):
        if not re.search(r'name="unternehmer"[^>]*required|required[^>]*name="unternehmer"', m.group(2)): err(f'{rel}: Formular „{m.group(1)}“ ohne Pflicht-Bestätigung „Unternehmer“')
    # Wortwahl
    if rel not in LEGAL and not noindex or rel in ('index',):
        body = text_of(main_of(t))
        for p, why in BAD:
            if re.search(re.escape(p), body, re.I): err(f'{rel}: „{p}“ ({why})')
        if re.search(r'rund um die Uhr', body, re.I) and rel not in RUND: err(f'{rel}: „rund um die Uhr“ (Verfügbarkeitszusage)')
        if re.search(r'(?<!Ist das alles )DSGVO-konform(?!\?)', body): err(f'{rel}: „DSGVO-konform“ als Zusage (besser: nach den Grundsätzen der DSGVO)')

# 4 Einwilligung nur über consent.js lesen -----------------------------------------------------------------------------
for js in glob.glob(ROOT + '/static/assets/*.js'):
    if os.path.basename(js) == 'consent.js': continue
    if re.search(r"localStorage\.getItem\(\s*['\"]mx-consent", open(js, encoding='utf-8').read()):
        err(f'{os.path.basename(js)} liest mx-consent direkt; Gültigkeit nur über window.mxConsent prüfen')

# 5 Ausgabe -----------------------------------------------------------------------------------------------------------
for n in sorted(set(notes)): print('HINWEIS', n)
for e in errors: print('FEHLER ', e)
print(f'{len(pages)} Seiten geprüft: {len(errors)} Fehler, {len(set(notes))} Hinweise')
sys.exit(1 if errors else 0)
