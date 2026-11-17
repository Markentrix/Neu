# -*- coding: utf-8 -*-
"""Seiten 11 bis 19: Farbe, Schrift, Layout, Erkennungszeichen, Bausteine, Bild."""
from ci_base import *
from ci_pages_a import img, L_HELL, L_DUNKEL, B_HELL, LINIE_P, LINIE_H, recolor


def lum(h):
    h = h.lstrip('#'); r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def cr(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + .05) / (y + .05)


def de(v):
    return ('%.1f' % v).replace('.', ',')


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def p11():
    sw = lambda c, name, txt: card('<div class="sw" style="background:%s"></div><div style="font:800 13px Archivo;margin:8px 0 3px">%s</div><div class="small">%s</div>' % (c, name, txt), '')
    sws = '<div class="g g5" style="gap:9px">' + sw(SALZ, 'Salz', 'Papierton. Grund und Weißraum.') + sw(TIEFSEE, 'Tiefsee', 'Tintenton. Text und dunkle Flächen.') + sw(PFAU, 'Pfauenblau', 'Markenfarbe. Links, Linien, Farbflächen.') + sw(REIF, 'Reif', 'Flächenfarbe. Abschnitte, Rahmen.') + sw(KUPFER, 'Kupfer', 'Handlungsfarbe. Hauptknopf, ein Wort.') + '</div>'
    rows = [('Salz', SALZ, '244 · 246 · 247', 'wird nicht gedruckt, ist das Papier', '', 'Grund'), ('Tiefsee', TIEFSEE, '12 · 33 · 40', '83 · 55 · 41 · 78', '97 · 52 · 30 · 79', 'Text, dunkle Fläche'),
            ('Pfauenblau', PFAU, '4 · 82 · 104', '83 · 39 · 26 · 45', '96 · 30 · 11 · 44', 'Markenfarbe'), ('Reif', REIF, '224 · 230 · 233', '11 · 5 · 5 · 0 <sup>1</sup>', '8 · 4 · 4 · 0 <sup>1</sup>', 'Fläche, Rahmen'),
            ('Kupfer', KUPFER, '198 · 116 · 50', '10 · 56 · 80 · 15', '5 · 52 · 88 · 13', 'Handlung')]
    def r1(n, h, rgb, c, u, r):
        if not u: cm = '<td colspan="2" style="font-weight:400">%s</td>' % c
        else: cm = '<td style="font-weight:400">%s</td><td style="font-weight:400">%s</td>' % (c, u)
        return '<tr><td>%s</td><td class="mono" style="font-weight:400">%s</td><td style="font-weight:400">%s</td>%s<td style="font-weight:400">%s</td></tr>' % (n, h, rgb, cm, r)
    t1 = '<div class="card"><table class="tb"><tr><th>Ton</th><th>Hex</th><th>RGB</th><th>CMYK gestrichen</th><th>CMYK ungestrichen</th><th>Rolle</th></tr>' + ''.join(r1(*r) for r in rows) + '</table></div>'
    st = [(KUPFER_D, 'Kupfer dunkel', '#964F08', '150 · 79 · 8', '7 · 65 · 100 · 33', 'Kupfer als kleiner Text auf Hell'), (KUPFER_H, 'Kupfer hell', '#F1A268', '241 · 162 · 104', '2 · 37 · 60 · 0', 'Kupfer auf Tiefsee und Pfauenblau'),
          (PFAU_H, 'Pfauenblau hell', '#62B2D0', '98 · 178 · 208', '58 · 6 · 8 · 1', 'Pfauenblau auf Tiefsee'), (NEBEL, 'Nebel', '#E1F0F6', '225 · 240 · 246', '11 · 1 · 2 · 0', 'Zarte Hinweisfläche, selten'),
          (NEBEN, 'Nebentext', '#465A62', '70 · 90 · 98', 'Tiefsee in 70 %', 'Bildunterschriften, Hinweise auf Hell'), (WEISS, 'Weiß', '#FFFFFF', '255 · 255 · 255', '0 · 0 · 0 · 0', 'Karten, Knopftext auf Pfauenblau')]
    t2 = '<div class="card"><table class="tb"><tr><th>Stufe</th><th>Hex</th><th>RGB</th><th>CMYK ungestrichen</th><th>Einsatz</th></tr>' + ''.join(
        '<tr><td><span style="display:inline-block;width:10px;height:10px;background:%s;border:1px solid rgba(12,33,40,.2);margin-right:7px;vertical-align:-1px"></span>%s</td><td class="mono" style="font-weight:400">%s</td><td style="font-weight:400">%s</td><td style="font-weight:400">%s</td><td style="font-weight:400">%s</td></tr>' % (c, n, h, rgb, cm, e) for c, n, h, rgb, cm, e in st) + '</table></div>'
    foot = '<p class="small" style="margin:7px 0 10px">Die Stufen sind keine zusätzlichen Farben, sondern hellere und dunklere Fassungen der Töne für bestimmte Untergründe. Eine einzige Ausnahme gibt es: <b>Fehlerrot #B3261E</b>, nur für Fehlermeldungen in Formularen, immer mit Symbol, nie als Gestaltungsfarbe.<br><sup>1</sup> Richtwert, im Andruck zu bestätigen (siehe Hinweis auf Seite 13).</p>'
    her = '<div class="note"><b>Zur Herkunft der Werte:</b> Tiefsee, Pfauenblau, Kupfer und ihre Stufen haben CMYK-Werte, die mit den deutschen Offset-Standardprofilen PSO Coated v3 und PSO Uncoated v3 berechnet wurden. <b>Salz und Reif sind neu in Version 3.1.</b> Salz ist das Papier und wird nicht gedruckt. Für Reif sind die CMYK-Werte Richtwerte und noch nicht über die Profile berechnet. Tiefsee wird auf ungestrichenem Papier etwas weniger tief, wie jedes Schwarz.</div>'
    return page(11, 'Design', 'Farbwelt', k('Farbwelt'), 'Fünf Töne, alle nach Dingen benannt, die man anfassen kann. Salz und Tiefsee tragen, Pfauenblau gibt Farbe, Reif gibt Fläche, Kupfer führt zur Handlung.',
                sws + '<h2 style="margin:20px 0 8px">Farbwerte der Palette</h2>' + t1 + '<h2 style="margin:18px 0 8px">Stufen derselben Töne</h2>' + t2 + foot + her)


def contrast_table():
    fgs = [('Tiefsee', TIEFSEE), ('Nebentext', NEBEN), ('Pfauenblau', PFAU), ('Kupfer dunkel', KUPFER_D), ('Kupfer', KUPFER), ('Weiß', WEISS), ('Salz', SALZ), ('Pfauenblau hell', PFAU_H), ('Kupfer hell', KUPFER_H)]
    bgs = [('Salz', SALZ), ('Weiß', WEISS), ('Reif', REIF), ('Tiefsee', TIEFSEE), ('Pfauenblau', PFAU), ('Kupfer', KUPFER)]
    dark_fg = {'Tiefsee', 'Nebentext', 'Pfauenblau', 'Kupfer dunkel'}
    light_fg = {'Weiß', 'Salz', 'Pfauenblau hell', 'Kupfer hell'}
    rows = ''
    for fn, fc in fgs:
        cells = ''
        for bn, bc in bgs:
            v = cr(fc, bc); s = de(v)
            light_bg = bn in ('Salz', 'Weiß', 'Reif'); dark_bg = bn in ('Tiefsee', 'Pfauenblau')
            if fn in dark_fg:
                if light_bg: cells += '<td>%s <span class="%s"></span></td>' % (s, 'ok' if v >= 4.5 else 'no')
                elif bn == 'Kupfer': cells += '<td>%s <span class="%s"></span></td>' % (s, 'ok' if (v >= 4.5 and fn == 'Tiefsee') else 'no') if fn == 'Tiefsee' else '<td>entfällt</td>'
                elif fn in ('Tiefsee', 'Pfauenblau') and bn != fn: cells += '<td>%s <span class="no"></span></td>' % s
                else: cells += '<td>entfällt</td>'
            elif fn == 'Kupfer':
                if bn == 'Kupfer': cells += '<td>entfällt</td>'
                else: cells += '<td>%s <span class="%s"></span></td>' % (s, 'ok' if v >= 3 else 'no')
            elif fn in light_fg:
                if light_bg or (bn == 'Kupfer' and fn in ('Pfauenblau hell', 'Kupfer hell')): cells += '<td>entfällt</td>'
                elif bn == 'Kupfer': cells += '<td>%s <span class="no"></span></td>' % s
                elif fn in ('Pfauenblau hell', 'Kupfer hell') and bn == 'Pfauenblau': cells += '<td>%s</td>' % s
                else: cells += '<td>%s <span class="%s"></span></td>' % (s, 'ok' if v >= 4.5 else 'no')
        use = {'Tiefsee': 'Text auf allen hellen Tönen und auf Kupfer', 'Nebentext': 'Nebentext auf Hell', 'Pfauenblau': 'Text, Links, Flächen auf Hell', 'Kupfer dunkel': 'Kupfer als Text auf Hell',
               'Kupfer': 'Wort, Fläche, Schrift ab 24 px', 'Weiß': 'Text auf Pfauenblau und Tiefsee', 'Salz': 'Text auf Tiefsee und Pfauenblau', 'Pfauenblau hell': 'Akzenttext auf Tiefsee', 'Kupfer hell': 'Akzent auf Tiefsee und Pfauenblau'}[fn]
        rows += '<tr><td>%s</td>%s<td style="font-weight:400">%s</td></tr>' % (fn, cells, use)
    return '<div class="card"><table class="tb" style="font-size:10px"><tr><th>Farbe</th>' + ''.join('<th>Auf %s</th>' % b[0] for b in bgs) + '<th>Zulässig als</th></tr>' + rows + '</table></div>'


def p12():
    anteile = [('65 %', 'Salz und Weiß', '#FFFFFF'), ('20 %', 'Tiefsee, Text eingerechnet', TIEFSEE), ('9 %', 'Reif', REIF), ('5 %', 'Pfauenblau', PFAU), ('1 %', 'Kupfer', KUPFER)]
    bar = '<div style="display:flex;height:28px;border:1px solid %s;border-radius:3px;overflow:hidden;margin:6px 0 10px">%s</div>' % (LINIE, ''.join('<div style="width:%s;background:%s"></div>' % (a[0].replace(' %', '%'), a[2]) for a in anteile))
    an = card('<h2>Anteile je Fläche</h2>' + bar + '<table class="kv">' + ''.join('<tr><td style="width:44px">%s</td><td style="font-weight:400">%s</td></tr>' % (a[0], a[1]) for a in anteile) + '</table><p class="small" style="margin-top:7px">Richtwerte, gemessen an der Startseite ohne Fotos. Auf Folien und Grafiken liegt Kupfer bei 1 bis 3 %.</p>')
    auf = card('<h2>Aufgaben</h2>' + lst(['<b>Tiefsee</b> trägt Text, Überschriften und dunkle Abschnitte. Höchstens jeder dritte Abschnitt ist dunkel, der Abschluss darf es sein.', '<b>Pfauenblau</b> ist die Markenfarbe: Links, Linien, Diagramme und die Farbfläche für Angebote.',
                                          '<b>Kupfer</b> ist die Handlungsfarbe: der Hauptknopf und ein Schlüsselwort je Überschrift. Nie mehr als ein Hauptknopf je Bildschirm.', '<b>Reif</b> hebt ruhige Abschnitte ab und ist die Farbe aller Rahmen und Trennlinien.', '<b>Salz und Weiß</b> wechseln als Grund. Karten sind weiß.']))
    ct = contrast_table()
    kn = card('<h2>Knöpfe</h2><div style="margin:6px 0 8px"><span class="btn">Termin buchen</span></div><p>Hauptknopf in Kupfer mit Tiefsee-Schrift (4,7:1). Der Knopf in der Kopfzeile ist Tiefsee mit weißer Schrift.</p>')
    ak = card('<h2>Akzent in Überschriften</h2><div style="font:800 17px/1.1 Archivo;letter-spacing:-.02em;margin:6px 0 6px">Websites, die<br>' + k('Anfragen') + ' bringen.</div><p>Der Text bleibt Tiefsee. Den Akzent setzt ein Wort in Kupfer. Kein Strich, kein Verlauf.</p>')
    dk = card('<h2 style="color:#fff">Auf dunkler Fläche</h2><p style="margin-top:6px;color:#fff">Text in Weiß, <span style="color:%s">Pfauenblau hell</span> und <span style="color:%s">Kupfer hell</span> für Akzente.</p><p style="margin-top:8px;color:#C3CED2">Dunkle Flächen setzen Akzente: Angebot, Beweis, Abschluss.</p>' % (PFAU_H, KUPFER_H), 'dk')
    return page(12, 'Design', 'Farbe anwenden', 'Farbe ' + k('anwenden'), 'Die Menge entscheidet über die Wirkung. Markentrix ist hell: Farbe ist Signal und führt den Blick zur Handlung.',
                '<div class="g g2" style="align-items:stretch">' + an + auf + '</div><h2 style="margin:18px 0 8px">Geprüfte Kontraste</h2>' + ct +
                '<p class="small" style="margin:6px 0 11px">Für Kupfer gilt die Grenze 3:1, weil es als Wort nur in großer Schrift (ab 24 px) und als Fläche vorkommt. Text <b>auf</b> Kupfer ist immer Tiefsee (4,7:1), nie Weiß (3,5:1).</p>' +
                '<div class="g g3">' + kn + ak + dk + '</div>')


def mini_old(filt):
    """Verkleinerte Beispielseite für die Sehschwäche-Simulation."""
    return ('<div style="filter:%s;background:%s;border:1px solid %s;border-radius:6px;padding:7px;overflow:hidden;height:96px"><div style="display:flex;justify-content:space-between;align-items:center">%s<span style="background:%s;color:#fff;font:600 4px Source Sans 3;padding:2px 5px;border-radius:2px">Termin buchen</span></div>'
            '<div style="display:flex;gap:6px;margin-top:5px"><div style="flex:1.2"><div style="font:800 11px/1.05 Archivo;letter-spacing:-.02em">Websites, die<br><span style="color:%s">Anfragen</span> bringen.</div><div style="margin-top:5px;background:%s;color:%s;font:700 4.4px Source Sans 3;padding:3px 6px;border-radius:2px;display:inline-block">Website-Check starten</div></div>'
            '<div style="flex:1;background:%s;border-radius:4px;padding:5px;color:#fff"><div style="font:800 6.5px/1.1 Archivo">Zwei Angebote.</div><div style="margin-top:4px;background:%s;color:%s;font:700 4px Source Sans 3;padding:2px 4px;border-radius:2px;display:inline-block">Angebot sichern</div></div></div>'
            '<div style="display:flex;gap:4px;margin-top:5px"><div style="flex:1;background:%s;color:#fff;border-radius:3px;padding:4px;font:800 5.5px Archivo">Weniger <span style="color:%s">Aufwand.</span></div><div style="flex:1;background:%s;border-radius:3px"></div></div></div>') % (
        filt, SALZ, LINIE, img(L_HELL, w=46), TIEFSEE, KUPFER, KUPFER, TIEFSEE, PFAU, KUPFER, TIEFSEE, TIEFSEE, KUPFER_H, REIF)


def mini(filt):
    """Verkleinerte Beispielseite: in dreifacher Größe gebaut und herunterskaliert, damit Chromium keine Mindestschriftgröße erzwingt."""
    inner = ('<div style="width:450px;height:318px;background:%s;border:3px solid %s;border-radius:18px;padding:21px;overflow:hidden;transform:scale(.3333);transform-origin:0 0;position:absolute;left:0;top:0">'
             '<div style="display:flex;justify-content:space-between;align-items:center">%s<span style="background:%s;color:#fff;font:600 14px Source Sans 3;padding:6px 14px;border-radius:5px">Termin buchen</span></div>'
             '<div style="display:flex;gap:18px;margin-top:16px"><div style="flex:1.2"><div style="font:800 34px/1.05 Archivo;letter-spacing:-.02em">Websites, die <span style="color:%s">Anfragen</span> bringen.</div>'
             '<div style="margin-top:14px;background:%s;color:%s;font:700 13px Source Sans 3;padding:8px 14px;border-radius:5px;display:inline-block">Website-Check starten</div></div>'
             '<div style="flex:1;background:%s;border-radius:10px;padding:14px;color:#fff;height:108px"><div style="font:800 19px/1.1 Archivo">Zwei Angebote.</div><div style="margin-top:12px;background:%s;color:%s;font:700 12px Source Sans 3;padding:6px 12px;border-radius:5px;display:inline-block">Angebot sichern</div></div></div>'
             '<div style="display:flex;gap:12px;margin-top:16px"><div style="flex:1;background:%s;color:#fff;border-radius:9px;padding:12px;font:800 17px Archivo">Weniger <span style="color:%s">Aufwand.</span></div><div style="flex:1;background:%s;border-radius:9px"></div></div></div>') % (
        SALZ, LINIE, img(L_HELL, w=140), TIEFSEE, KUPFER, KUPFER, TIEFSEE, PFAU, KUPFER, TIEFSEE, TIEFSEE, KUPFER_H, REIF)
    return '<div style="position:relative;width:150px;height:106px;overflow:hidden;filter:%s;border-radius:6px">%s</div>' % (filt, inner)


def p13():
    svgdefs = ('<svg width="0" height="0" style="position:absolute"><defs>'
               '<filter id="prot" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.152286 1.052583 -0.204868 0 0  0.114503 0.786281 0.099216 0 0  -0.003882 -0.048116 1.051998 0 0  0 0 0 1 0"/></filter>'
               '<filter id="deut" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.367322 0.860646 -0.227968 0 0  0.280085 0.672501 0.047413 0 0  -0.011820 0.042940 0.968881 0 0  0 0 0 1 0"/></filter>'
               '<filter id="gray" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0.2126 0.7152 0.0722 0 0  0 0 0 1 0"/></filter></defs></svg>')
    druck = card('<h2>So wird gedruckt</h2>' + lst(['<b>Papier:</b> weiß und ungestrichen. Der Salzton entsteht dann von selbst und wird nicht gedruckt.', '<b>Fließtext:</b> in reinem Schwarz (0 · 0 · 0 · 100), damit kleine Schrift scharf bleibt. Tiefsee erst ab 14 pt und für Flächen.',
                                                   '<b>Pfauenblau und Kupfer:</b> im Vierfarbdruck nach den Werten auf Seite 11.', '<b>Einfarbiger Druck:</b> Logo und Text in Tiefsee oder Schwarz.', '<b>Veredelung:</b> Kupfer kann auf Visitenkarten und Mappen als Heißfolie in Kupfer matt geprägt werden. Das ist dann echtes Metall und der einzige erlaubte Effekt.']))
    kup = card('<h2>Regeln für Kupfer</h2>' + lst(['<b>Handlung und Schlüsselwort.</b> Kupfer steht für den Hauptknopf, ein Wort je Überschrift und Abzeichen. Höchstens ein Hauptknopf je Bildschirm.', '<b>Nie als große Fläche.</b> Kupfer ist Knopf, Wort oder Abzeichen.',
                                             '<b>Text auf Kupfer ist Tiefsee.</b>', '<b>Kupfer als Schrift</b> nur ab 24 px. Kleiner immer Kupfer dunkel.', '<b>Auf Reif und Salz</b> reicht Kupfer für große Schrift, kleiner steht Kupfer dunkel.', '<b>Auf Tiefsee und Pfauenblau</b> steht Kupfer hell.']))
    sim = card('<div class="g g4" style="gap:10px"><div>%s<b style="font-size:10px">Normales Sehen</b></div><div>%s<b style="font-size:10px">Rot-Schwäche</b></div><div>%s<b style="font-size:10px">Grün-Schwäche</b></div><div>%s<b style="font-size:10px">Schwarz-Weiß-Drucker</b></div></div>' % (mini('none'), mini('url(#prot)'), mini('url(#deut)'), mini('url(#gray)')) +
               '<p style="margin-top:10px">Etwa jeder zwölfte Mann sieht Rot und Grün schwächer. Pfauenblau und Kupfer unterscheiden sich nicht nur im Farbton, sondern auch deutlich in der Helligkeit. Deshalb bleiben Knopf, Schlüsselwort und Text in allen vier Ansichten klar getrennt. Die Bilder für Rot- und Grün-Schwäche sind Simulationen.</p>')
    b3 = grid('g3', card('<h2>Nie Farbe allein</h2><p>Eine Information hängt nie nur an der Farbe. Fehler bekommen ein Symbol und Text, Links eine Unterstreichung oder einen Pfeil, Diagramme eine Beschriftung.</p>'),
              card('<h2>Schatten und Linien</h2><p>Schatten sind immer Tiefsee mit 5 bis 16 % Deckkraft, nie schwarz, nie farbig. Rahmen und Trennlinien sind 1 px in Reif.</p>'),
              card('<h2>Was es nicht gibt</h2><p>Verläufe, Neon, Glühen, Transparenz-Effekte, Punktraster und jede weitere Farbe. Die Kundenwebsites haben ihre eigenen Farben, Markentrix nur diese.</p>'))
    off = '<div class="note mt2"><span class="tag">OFFEN</span> Vor der ersten größeren Auflage bestätigt die Druckerei die CMYK-Werte mit einem Andruck auf dem gewählten Papier. Das gilt besonders für Reif. Dabei werden auch die Folienfarben für Fahrzeug und Schild sowie die Kupferfolie festgelegt und hier nachgetragen.</div>'
    return page(13, 'Design', 'Farbe im Druck', 'Farbe im ' + k('Druck') + ' und für alle Augen', 'Die Palette wurde so gebaut, dass sie auf Papier, auf dem Schwarz-Weiß-Drucker und für Menschen mit Farbfehlsicht funktioniert.',
                svgdefs + '<div class="g g2" style="align-items:stretch">' + druck + kup + '</div><h2 style="margin:18px 0 8px">Geprüft für Farbfehlsicht und Graustufen</h2>' + sim + '<div class="mt2">' + b3 + '</div>' + off)


def p14():
    a = card('<div class="lbl n">Überschriften</div><div style="font:800 46px/1 Archivo;letter-spacing:-.025em;margin:4px 0 8px">Archivo</div><div style="font:800 14px/1.35 Archivo">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyzäöüß<br>0123456789 € % &amp; ? !</div><p style="margin-top:8px"><b>ExtraBold 800</b> für H1, H2 und die Wortmarke · <b>Bold 700</b> für H3 und Kartenüberschriften. Laufweite −2,5 %.</p>')
    b = card('<div class="lbl n">Fließtext</div><div style="font:400 46px/1 \'Source Sans 3\';margin:4px 0 8px">Source Sans 3</div><div style="font:400 14px/1.35 \'Source Sans 3\'">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyzäöüß<br>0123456789 € % &amp; ? !</div><p style="margin-top:8px"><b>Regular 400</b> für Fließtext · <b>SemiBold 600</b> für Knöpfe, Labels und Hervorhebungen · <b>Bold 700</b> für Tabellenköpfe.</p>')
    c = card('<h2>Bezug und Lizenz</h2>' + kv([('Lizenz', 'Beide Schriften stehen unter der SIL Open Font License. Kostenlos, auch gewerblich, auch im Druck.'), ('Bezug', 'Google Fonts oder die Schriftdateien im CI-Paket.'),
                                               ('Website', 'Schriften liegen auf dem eigenen Server. Kein Abruf von Google, aus Datenschutzgründen.'), ('Canva', 'Beide Schriften sind dort vorhanden und im Markenkit zu hinterlegen.')], 'w'))
    d = card('<h2>Ersatzschriften</h2>' + kv([('Website', 'Archivo → Arial Black → Arial fett<br>Source Sans 3 → Segoe UI → Systemschrift → Arial'), ('E-Mail, Office', 'Arial für Text und Überschriften, wenn die Markenschriften beim Empfänger fehlen.'),
                                              ('Nie', 'Times, Calibri, Comic Sans, Schreibschriften, Schmuckschriften. Auch nicht mehr: Space Grotesk und Inter.')], 'w'))
    e = card('<h2>Ziffern und Preise</h2><div style="margin:4px 0 6px"><div style="font:800 24px Archivo">1.099 €</div><div style="font:600 12px \'Source Sans 3\'">29,99 € im Monat</div></div><p>Große Preise stehen in Archivo, Nebenpreise und Tabellen in Source Sans 3 mit gleich breiten Ziffern, damit Spalten sauber untereinander stehen.</p>')
    f = card('<h2>Auszeichnung</h2>' + lst(['Hervorheben mit SemiBold, nie mit Farbe allein', 'Kursiv nur für Zitate und Titel', 'Unterstreichung nur für Links', 'Versalien nur für kleine Labels']))
    g_ = card('<h2>Satz</h2>' + lst(['Immer linksbündig, nie Blocksatz', 'Zentriert nur bei Titeln bis zwei Zeilen', '45 bis 75 Zeichen je Zeile', 'Kein einzelnes Wort in der letzten Zeile einer Überschrift']))
    warum = '<div class="note mt2"><b>Warum diese beiden:</b> Archivo ist eine kräftige Grotesk, wie man sie von Schildern und Beschriftungen kennt. Sie wirkt handfest statt technisch. Source Sans 3 ist für lange Texte am Bildschirm entwickelt, offen gezeichnet und auch klein gut lesbar. Zusammen ergeben sie den Abstand zur üblichen Vorlagen-Typografie.</div>'
    return page(14, 'Design', 'Typografie', k('Typografie'), 'Überschriften sind kräftig, kurz und direkt, wie auf einem Ladenschild. Fließtexte sind ruhig und gut lesbar. Zwei Schriften, keine dritte.',
                '<div class="g g2">' + a + b + '</div><div class="g g2 mt2">' + c + d + '</div><div class="g mt2" style="grid-template-columns:1fr 1fr 1fr">' + e + f + g_ + '</div>' + warum)


def p15():
    rows = [('H1', 'Archivo 800', '37 → 75 px', '28 bis 34 pt', '72 bis 110 px', '1,04 bis 1,1', '−2,5 %'), ('H2', 'Archivo 800', '29 → 48 px', '18 bis 22 pt', '48 bis 64 px', '1,12', '−2 %'), ('H3', 'Archivo 700', '19 → 23 px', '12 bis 14 pt', '36 bis 44 px', '1,25', '−1 %'),
            ('Vorspann', 'Source Sans 3 400', '18 → 20 px', '12,5 pt', '38 bis 46 px', '1,45', '0'), ('Fließtext', 'Source Sans 3 400', '17 → 19 px', '10 bis 11 pt', 'mindestens 34 px', '1,5', '0'), ('Kleintext', 'Source Sans 3 400', '15 px', '8,5 pt', 'mindestens 28 px', '1,4', '0'),
            ('Label', 'Source Sans 3 700, Versalien', '13 px', '8 pt', '24 bis 28 px', '1,3', '+9 %'), ('Knopf', 'Source Sans 3 600', '16 bis 17 px', 'entfällt', '34 bis 40 px', '1', '0')]
    t = '<div class="card"><table class="tb"><tr><th>Stufe</th><th>Schrift</th><th>Website<br>Handy → Desktop</th><th>Druck A4</th><th>Social Media<br>1080 px breit</th><th>Zeilenhöhe</th><th>Laufweite</th></tr>' + ''.join('<tr><td>%s</td>%s</tr>' % (r[0], ''.join('<td style="font-weight:400">%s</td>' % c for c in r[1:])) for r in rows) + '</table></div>'
    cap = '<p class="small" style="margin:6px 0 12px">Source Sans 3 läuft etwas kleiner als andere Schriften. Fließtext auf der Website ist deshalb nie kleiner als 17 px. Zwischen Handy und Desktop wachsen die Größen stufenlos mit der Bildschirmbreite.</p>'
    h = card('<div class="lbl n">Hierarchie im Überblick</div><div style="font:800 25px/1.05 Archivo;letter-spacing:-.025em">H1 · Archivo<br>ExtraBold</div><div style="font:800 17px Archivo;margin:7px 0 2px;letter-spacing:-.02em">H2 · Archivo ExtraBold</div><div style="font:700 13.5px Archivo;margin-bottom:6px">H3 · Archivo Bold</div>'
             '<div style="font:400 13.5px \'Source Sans 3\'">Vorspann · Source Sans 3 Regular</div><div style="font:400 12px \'Source Sans 3\'">Fließtext · Source Sans 3 Regular</div><div style="font:400 10px \'Source Sans 3\';color:%s">Kleintext · Source Sans 3 Regular in Nebentext</div><div style="font:700 8.5px \'Source Sans 3\';letter-spacing:.09em;margin-top:5px">LABEL · SOURCE SANS 3 BOLD</div>' % NEBEN)
    bsp = card('<div class="lbl n">Anwendungsbeispiel</div><div style="font:800 25px/1.05 Archivo;letter-spacing:-.025em;margin-bottom:6px">Ein Ansprechpartner.<br>' + k('Kein Apparat.') + '</div><p style="font-size:12.5px;margin-bottom:6px">Sie sprechen mit dem, der Ihre Website baut.</p><p style="margin-bottom:9px">Vom Erstgespräch bis zur laufenden Pflege haben Sie einen festen Ansprechpartner. Jede Anfrage landet an einem Ort, und Sie erfahren es sofort.</p><span class="btn">Erstgespräch buchen</span>')
    u = grid('g3', card('<h2>Überschriften</h2>' + lst(['Höchstens zwei Zeilen in jeder Breite', 'Immer Tiefsee, auf Dunkel Weiß', 'Akzent: ein Wort in Kupfer', 'Nie in Versalien, nie ganz farbig'])),
             card('<h2>Fließtext</h2>' + lst(['Auf Hell in Tiefsee, auf Dunkel in Weiß', 'Website nie kleiner als 17 px', 'Eingabefelder mindestens 16 px', 'Absatzabstand: halbe Zeilenhöhe'])),
             card('<h2>Labels</h2>' + lst(['Höchstens vier Wörter', 'Nebentext oder Pfauenblau', 'Sparsam: nicht über jeder Überschrift', 'Nie als Ersatz für eine Überschrift'])))
    return page(15, 'Design', 'Schriftgrößen', 'Schriftgrößen &amp; ' + k('Hierarchie'), 'Höchstens fünf Größen je Fläche. Die Überschrift ist mindestens dreimal so groß wie der Fließtext.', t + cap + '<div class="g g2">' + h + bsp + '</div><div class="mt2">' + u + '</div>')


def p16():
    bars = '<div style="display:flex;align-items:flex-end;gap:6px;height:76px;margin:8px 0 3px">' + ''.join('<div style="width:%dpx;height:%dpx;background:%s"></div>' % (w, h, PFAU) for w, h in [(5, 5), (8, 8), (12, 12), (16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (84, 76)]) + '</div><div class="small">4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128 px</div>'
    ab = card('<h2>Abstandsskala</h2><p>Alle Abstände sind Vielfache von 4 px. Andere Werte gibt es nicht.</p>' + bars + kv([('Innerhalb eines Elements', '4 bis 12 px'), ('Innenabstand Karte', '24 px, auf dem Handy 16 px'), ('Zwischen Karten', '16 bis 24 px'), ('Zwischen Abschnitten', '56 px auf dem Handy, bis 128 px am Desktop')], 'w'))
    cols = '<div style="display:flex;gap:4px;margin-top:10px">' + ''.join('<div style="flex:1;height:38px;background:%s"></div>' % REIF for _ in range(12)) + '</div>'
    ra = card('<h2>Raster</h2><table class="tb"><tr><th>Medium</th><th>Raster</th></tr><tr><td>Website</td><td style="font-weight:400">12 Spalten, Inhaltsbreite höchstens 1180 px, Textspalte höchstens 800 px, Seitenrand 16 bis 32 px</td></tr><tr><td>A4</td><td style="font-weight:400">6 Spalten, Rand 20 mm, links bei Briefen 25 mm</td></tr>'
              '<tr><td>Social Media</td><td style="font-weight:400">Rand 64 px bei 1080 px Breite, Inhalte auf 4 Spalten</td></tr><tr><td>Präsentation 16:9</td><td style="font-weight:400">12 Spalten, Rand 5 % der Breite</td></tr></table>' + cols)
    rad = card('<h2>Eckenradien</h2><div style="display:flex;gap:14px;margin:6px 0 10px">' + ''.join('<div><div style="width:68px;height:38px;border:2px solid %s;border-radius:%dpx"></div><div class="cap" style="text-align:center">%d px</div></div>' % (PFAU, r, r) for r in (4, 8, 12)) +
               '</div><p><b>4</b> Knöpfe, Eingabefelder, Abzeichen · <b>8</b> Karten · <b>12</b> große Flächen und Bilder. Die Ecken sind bewusst knapp gerundet. Stark gerundete oder runde Formen gehören nicht zur Marke, außer im Logo selbst.</p>')
    sh = card('<h2>Rahmen und Schatten</h2><div style="display:flex;gap:12px;margin:6px 0 10px">' + ''.join('<div style="width:62px;height:42px;background:#fff;border-radius:8px;%s"></div>' % s for s in ('border:1px solid %s' % LINIE, 'border:1px solid %s;box-shadow:0 1px 3px rgba(12,33,40,.08)' % LINIE, 'box-shadow:0 6px 16px rgba(12,33,40,.12)', 'box-shadow:0 14px 30px rgba(12,33,40,.16)')) +
              '</div><p><b>Rahmen</b> 1 px in Reif ist der Standard für Karten. <b>Schatten klein</b> für Karten auf Weiß, <b>mittel</b> für schwebende Elemente, <b>groß</b> nur für Dialoge und Gerätebilder.</p>')
    r = lambda n, t, d: card('<div style="font:700 11px Source Sans 3;color:%s;margin-bottom:3px">%s</div><h3>%s</h3><p>%s</p>' % (PFAU, n, t, d))
    six = ('<div class="g g3 mt2">' + r('01', 'Hierarchie', 'Eine dominante Botschaft je Fläche. Nebentexte klar zurücknehmen.') + r('02', 'Freie Fläche', 'Rund 60 % der Fläche bleiben frei. Ruhe ist Teil der Marke.') +
           r('03', 'Farbe im Wechsel', 'Abschnitte wechseln zwischen Weiß und Salz. Pfauenblau und Tiefsee setzen Akzente: Angebot, Beweis, Abschluss.') + r('04', 'Hauptaktion', 'Genau eine Hauptaktion je Abschnitt, als Knopf in Kupfer.') +
           r('05', 'Textbreite', 'Lange Zeilen vermeiden. Inhalte bleiben mit einem Blick erfassbar.') + r('06', 'Kein Schmuck', 'Keine Muster, keine Deko-Zählungen, keine Leisten mit runden Kennzahlen.') + '</div>')
    return page(16, 'Design', 'Layout & Abstände', 'Layout, Raster &amp; ' + k('Abstände'), 'Struktur vor Dekoration. Jede Fläche folgt einer klaren Hierarchie, festen Abständen und bewusst freier Fläche.',
                '<div class="g g2" style="align-items:stretch">' + ab + ra + '</div><div class="g g2 mt2" style="align-items:stretch">' + rad + sh + '</div>' + six)


def p17():
    kw = card('<div class="lbl">1 · Das Kupferwort</div><div style="font:800 25px/1.08 Archivo;letter-spacing:-.025em;margin:4px 0 8px">Websites, die<br>' + k('Anfragen') + ' bringen.</div>' +
              kv([('Was', 'Ein Wort, selten zwei, in Kupfer. Der Rest der Überschrift bleibt Tiefsee.'), ('Wahl', 'Das Wort, auf dem die Aussage liegt: der Nutzen oder die Handlung.'), ('Häufigkeit', 'Ein Kupferwort je Überschrift, nie mehr als zwei je sichtbarer Fläche.'),
                  ('Auf Dunkel', 'Kupfer hell'), ('Nie', 'ganze Sätze, Fließtext, Links oder Wörter unter 24 px (dort Kupfer dunkel). Nie unterstrichen, schräg oder als Markerfläche.')], 'w'))
    li = card('<div class="lbl">2 · Die Aufwärtslinie</div><div style="margin:2px 0 10px">' + img(LINIE_P, w=200) + '</div>' +
              kv([('Was', 'Eine einzelne, nach oben beschleunigende Linie, die im Pfeil des Logos endet'), ('Maße', 'Seitenverhältnis 8 : 3, Strichstärke 2,5 % der Breite, runde Enden'), ('Farbe', 'Pfauenblau, auf Dunkel Pfauenblau hell. Nie Kupfer.'),
                  ('Platz', 'Unten rechts, 20 bis 35 % der Formatbreite'), ('Nie', 'spiegeln, drehen, hinter Text legen, als Diagramm mit Zahlen ausgeben')], 'w'))
    zs = card('<h2>Zusammenspiel</h2>' + kv([('Je Fläche', 'Höchstens ein Kupferwort und ein Hauptknopf in Kupfer'), ('Dominant', 'Nur eines von beiden darf groß sein'), ('In Dokumenten', 'Aufwärtslinie auf Titel und Schlussseite, nicht auf jeder Seite'),
                                              ('Aus der Datei', 'Die Aufwärtslinie wird nie nachgezeichnet, sondern aus „aufwaertslinie.svg“ eingesetzt')], 'w'))
    dk = '<div class="card dk" style="min-height:178px"><div style="font:700 12px Archivo;margin-bottom:6px">Auf dunklem Grund</div><div style="font:800 22px/1.08 Archivo;letter-spacing:-.02em">Mehr Anfragen.<br><span style="color:%s">Weniger Aufwand.</span></div><div style="margin-top:12px">%s</div></div>' % (KUPFER_H, img(LINIE_H, w=160))
    b3 = grid('g3', card('<h2>Warum das Wort</h2><p>Kupfer ist die warme Farbe der Marke und fällt neben Tiefsee und Pfauenblau sofort auf. Ein Wort in Kupfer sagt: Darauf kommt es an. Mehr braucht es nicht, um den Blick zu führen.</p>'),
              card('<h2>Warum die Linie</h2><p>Sie ist der Aufstrich des M, weitergeführt. Sie steht für das Versprechen der Marke: Es geht nach oben, in ruhigen Schritten.</p>'),
              card('<h2>Was entfallen ist</h2><p>Die Wachstumskurve mit drei Leuchtpunkten, der Cyan-Marker aus den früheren Fassungen und seit Version 3.1 der Kupferstrich unter Wörtern.</p>'))
    probe = '<div class="note mt2"><b>Probe aufs Exempel:</b> Decken Sie auf einer beliebigen Markentrix-Fläche das Logo ab. Bleiben Salz oder Weiß, Tiefsee, eine Überschrift in Archivo mit einem Wort in Kupfer und ein Knopf in Kupfer sichtbar, ist die Fläche richtig gestaltet.</div>'
    return page(17, 'Design', 'Erkennungszeichen', 'Die zwei ' + k('Erkennungszeichen'), 'Zwei wiederkehrende Elemente machen Markentrix auch ohne Logo erkennbar: das Wort in Kupfer und die Linie nach oben. Beide stammen aus dem Logo.',
                '<div class="g g2" style="align-items:stretch">' + kw + li + '</div><div class="g g2 mt2" style="align-items:stretch">' + zs + dk + '</div><div class="mt2">' + b3 + '</div>' + probe)


ICONS = {
    'cal': '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    'msg': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    'sea': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'mai': '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'chk': '<path d="M20 6 9 17l-5-5"/>',
    'trd': '<path d="M22 7l-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>'}


def icon(n, size=26):
    return '<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (size, size, TIEFSEE, ICONS[n])


def p18():
    kn = card('<h2>Knöpfe</h2><div style="display:flex;gap:11px;align-items:center;margin:6px 0 10px"><span class="btn">Termin buchen</span><span class="btn s">Anrufen</span><span style="color:%s;font-weight:600;font-size:11.5px">Alle Referenzen →</span></div>' % PFAU +
              kv([('Hauptknopf', 'Kupfer mit Tiefsee-Schrift, einmal je Abschnitt. Auf Pfauenblau und Tiefsee: Kupfer hell.'), ('Kopfzeile', 'Tiefsee mit weißer Schrift'), ('Zweitknopf', 'Weiß mit Rahmen in Tiefsee, Text in Tiefsee'), ('Textlink', 'Pfauenblau, mit Pfeil, ohne Fläche'),
                  ('Maße', 'Höhe mindestens 44 px, Radius 4 px, Innenabstand 16 bis 24 px'), ('Zustände', 'Berühren: heller (#D4823F). Fokus: 3 px Tiefsee mit 3 px Abstand, auf Dunkel Weiß. Gesperrt: 40 % Deckkraft.')], 'w'))
    ka = card('<h2>Karten, Felder, Abzeichen</h2><div style="display:flex;gap:9px;align-items:center;margin:6px 0 10px"><div style="border:1px solid %s;border-radius:4px;padding:9px 11px;font-size:10.5px;color:%s;flex:1;background:#fff">www.ihre-website.de</div>' % (TIEFSEE, NEBEN) +
              '<span style="background:%s;color:%s;font:700 8.5px Source Sans 3;padding:4px 8px;border-radius:3px">Nur bis 30.11.</span><span style="background:%s;color:%s;font:700 8.5px Source Sans 3;padding:4px 8px;border-radius:3px">Ab November</span></div>' % (KUPFER, TIEFSEE, NEBEL, PFAU) +
              kv([('Karte', 'Weiß, Rahmen in Reif, Radius 8 px, Innenabstand 24 px'), ('Eingabefeld', 'Höhe mindestens 44 px, Radius 4 px, Schrift mindestens 16 px, Beschriftung immer sichtbar über dem Feld'),
                  ('Abzeichen', 'Kupfer mit Text in Tiefsee für den einen Hinweis. Tiefsee mit weißem Text auf Pfauenblau. Nebel mit Text in Pfauenblau für alles Weitere.'), ('Meldungen', 'Erfolg in Pfauenblau mit Haken. Fehler in Fehlerrot mit Symbol und Text unter dem Feld.')], 'w'))
    ic = card('<h2>Icons</h2><div style="display:flex;gap:16px;margin:6px 0 10px">' + ''.join(icon(n) for n in ICONS) + '</div>' +
              lst(['<b>Stil:</b> Linien-Icons mit runden Enden, passend zur Bildmarke.', '<b>Strich:</b> 1,75 px bei 24 px Größe, proportional mitwachsend.', '<b>Farbe:</b> Tiefsee oder Pfauenblau, auf Dunkel Weiß. Nie Kupfer.', '<b>Quelle:</b> Empfohlen ist die freie Sammlung Lucide. Sammlungen werden nicht gemischt.', '<b>Nie:</b> gefüllte Icons, Emojis als Icons, 3D- oder Comic-Icons.']))
    bars = '<div style="display:flex;align-items:flex-end;gap:12px;height:76px;border-bottom:1px solid %s;margin:6px 0 10px;padding:0 6px">' % TIEFSEE + ''.join('<div style="width:34px;height:%dpx;background:%s;border-radius:2px 2px 0 0"></div>' % (h, c) for h, c in [(28, PFAU), (36, PFAU), (46, PFAU), (58, PFAU), (72, KUPFER)]) + '</div>'
    dg = card('<h2>Diagramme und Tabellen</h2>' + bars + lst(['<b>Diagramme:</b> Pfauenblau als Grundfarbe, Kupfer für genau einen hervorgehobenen Wert, Nebentext für Achsen.', '<b>Beschriftung:</b> Source Sans 3, Werte direkt am Balken, keine Legende, wenn es ohne geht.',
                                                        '<b>Tabellen:</b> Weiß, nur waagerechte Linien in Reif, Kopfzeile als Label, Zahlen rechtsbündig.', '<b>Nie:</b> 3D-Effekte, Tortendiagramme mit mehr als vier Teilen, Zahlen ohne Quelle.']))
    b3 = grid('g3', card('<h2>Bewegung</h2><p>Kurz und funktional: unter 300 ms, nur Einblenden und Verschieben. Wer Bewegung reduziert haben möchte, bekommt keine.</p>'),
              card('<h2>Bedienbarkeit</h2><p>Tippziele mindestens 44 px. Alles ist per Tastatur erreichbar, der Fokus immer sichtbar. Ziel ist WCAG 2.2 AA.</p>'),
              card('<h2>Technische Werte</h2><p>Alle Farben, Größen, Abstände und Radien liegen als Variablen in der Datei <span class="mono">tokens.css</span> im CI-Paket.</p>'))
    return page(18, 'Design', 'Bausteine & Icons', 'Bausteine &amp; ' + k('Icons'), 'Wiederkehrende Bausteine sehen überall gleich aus: auf der Website, im Portal, in Angeboten und Präsentationen.',
                '<div class="g g2" style="align-items:stretch">' + kn + ka + '</div><div class="g g2 mt2" style="align-items:stretch">' + ic + dg + '</div><div class="mt2">' + b3 + '</div>')


def p19():
    geeignet = card('<h2>Geeignete Motive</h2>' + lst(['Betriebe bei der Arbeit: Werkstatt, Laden, Hof, Stall, Garten, Baustelle', 'Inhaberinnen und Inhaber in ihrem Betrieb', 'Hände, Werkzeug, Ware und Material in der Nahaufnahme', 'Smartphone oder Laptop mit einer Anfrage, einem Termin, einer Website', 'Website-Ansichten auf echten Geräten', 'Vorher-Nachher-Darstellungen']))
    vermeiden = card('<h2>Vermeiden</h2>' + lst(['Stockfoto-Szenen: Händeschütteln, Anzugträger, gestellte Teams', 'KI-Klischees: Roboter, leuchtende Gehirne, Hologramme', 'Neon, Glühen, Lichtreflexe, dunkle Räume', 'Unruhige oder zugestellte Hintergründe', 'Comic-Icons und 3D-Figuren', 'Unnatürliche Menschen, glatte Haut, Dauerlächeln'], 'x'))
    rows = [('Licht', 'Natürliches, weiches Tageslicht von der Seite oder schräg von vorn. Keine harten Schatten, kein Blitz. Mindestens die Hälfte des Bildes ist heller als Mittelgrau.'), ('Farbe', 'Natürlich und leicht warm. Sättigung zurückhaltend. Kein Farbstich, kein Filter, kein Orange-Türkis-Look.'),
            ('Markenfarben im Bild', 'Pfauenblau erscheint als echter Gegenstand: ein Arbeitsshirt, eine Schürze, eine Tür, ein Ordner. Kupfer höchstens einmal und klein, am besten als echtes Material: Kupfer, Leder, warmes Holz. Dunkles ist Blauschwarz statt Schwarz.'),
            ('Umgebung', 'Aufgeräumt und echt, mit natürlichen Materialien: weiße Wände, helles Holz, Leinen, Papier, heller Stein. Keine fremden Logos, keine lesbaren Fremdmarken.'), ('Menschen', 'Echte Betriebe aus der Region, Alter 25 bis 60, echte Arbeitskleidung, natürliche Haut. Konzentriert bei der Arbeit oder freundlich im Gespräch. Der Blick in die Kamera ist die Ausnahme.'),
            ('Aufnahme', 'Augenhöhe, Brennweite 35 bis 50 mm, leichte Unschärfe im Hintergrund. Ein klares Hauptmotiv im Goldenen Schnitt.'), ('Freifläche', 'Mindestens ein Drittel des Bildes ist ruhig und hell, damit Überschrift und Logo Platz haben.'), ('Bearbeitung', 'Nur Helligkeit, Weißabgleich und Zuschnitt. Keine Haut-Retusche, keine Montagen, keine Farbüberlagerung.')]
    look = '<div class="card"><table class="kv w">' + ''.join('<tr><td style="width:128px">%s</td><td style="font-weight:400">%s</td></tr>' % r for r in rows) + '</table></div>'
    b3 = grid('g3', card('<h2>Bildschirme im Bild</h2><p>Displays zeigen helle, schlichte Oberflächen in Weiß mit einem Knopf in Kupfer. Echte Ansichten werden nachträglich eingesetzt, nie abfotografiert.</p>'),
              card('<h2>Formate und Zuschnitt</h2><p>Quer 3:2 und 16:9 für Website und Präsentation. Hoch 4:5 und 9:16 für Social Media. Bilder haben 12 px Eckenradius oder laufen randlos.</p>'),
              card('<h2>Rechte</h2><p>Fotos echter Betriebe und Personen nur mit schriftlicher Zustimmung. Jedes veröffentlichte Projekt nennt den Betrieb und das Aufnahmedatum.</p>'))
    rang = '<div class="note mt2"><b>Rangfolge der Bildquellen:</b> zuerst eigene Fotos echter Kunden und Projekte, dann KI-Bilder nach den Regeln der nächsten zwei Seiten, zuletzt gekaufte Fotos. Gekaufte Fotos sind die Ausnahme und müssen den Look in allen Werten treffen.</div>'
    return page(19, 'Bild', 'Bildsprache', 'Bildsprache &amp; ' + k('Fotografie'), 'Hell, echt und nah am Betrieb. Gezeigt werden Menschen bei ihrer Arbeit und das, was sie herstellen oder anbieten. Technik ist Werkzeug in der Hand, nie das Motiv.',
                '<div class="g g2" style="align-items:stretch">' + geeignet + vermeiden + '</div><h2 style="margin:18px 0 8px">Der Markentrix-Look in festen Werten</h2>' + look + '<div class="mt2">' + b3 + '</div>' + rang)
