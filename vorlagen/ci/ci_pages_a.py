# -*- coding: utf-8 -*-
"""Seiten 1 bis 10: Titel, Einstieg, Marke, Logo."""
from ci_base import *


def recolor(name, mapping):
    s = svg(name)
    for a, b in mapping.items():
        s = s.replace(a, b)
    return 'data:image/svg+xml;base64,' + base64.b64encode(s.encode()).decode()


def img(uri, h=None, w=None, style=''):
    st = ('height:%spx;' % h if h else '') + ('width:%spx;' % w if w else '')
    return '<img src="%s" style="display:block;%s%s">' % (uri, st, style)


L_HELL = svg_uri('markentrix-logo-farbe-hell.svg')
L_DUNKEL = svg_uri('markentrix-logo-farbe-dunkel.svg')
L_TIEF = svg_uri('markentrix-logo-tiefsee.svg')
L_SCHWARZ = recolor('markentrix-logo-tiefsee.svg', {'#0C2128': '#000000'})
L_WEISS = svg_uri('markentrix-logo-weiss.svg')
B_HELL = svg_uri('markentrix-bildmarke-farbe-hell.svg')
B_TIEF = svg_uri('markentrix-bildmarke-tiefsee.svg')
B_WEISS = svg_uri('markentrix-bildmarke-weiss.svg')
B_DUNKEL = svg_uri('markentrix-bildmarke-farbe-dunkel.svg')
LINIE_P = svg_uri('aufwaertslinie.svg')
LINIE_H = svg_uri('aufwaertslinie-hell.svg')


def p01():
    return ('<section class="pg"><div class="hd"><span>01 — Markenhandbuch 2026</span><i></i><span>Version 3.1</span></div>'
            '<div style="margin-top:182px">' + img(L_HELL, w=560) + '</div>'
            '<div style="margin-top:78px"><div style="font:800 32px Archivo;letter-spacing:-.02em">Markenhandbuch</div>'
            '<div style="font-size:14px;color:%s;margin-top:6px">Corporate Identity · Version 3.1 · November 2026</div></div>' % NEBEN +
            '<div style="margin-top:56px;font:800 21px/1.12 Archivo;letter-spacing:-.015em">Mehr Anfragen.<br>' + k('Weniger Aufwand.') + '</div>'
            '<div style="font-size:12.5px;color:%s;margin-top:7px">Websites, Werbung und Automatisierung für lokale Betriebe.</div>' % NEBEN +
            '<div style="position:absolute;right:60px;bottom:118px">' + img(LINIE_P, w=290) + '</div>'
            '<div class="ft"><span>Markentrix · Markenhandbuch 2026 · Version 3.1</span><span>01 · TITEL</span></div></section>')


TOC = [('03', 'Positionierung', 'Marke'), ('04', 'Charakter & Tonalität', 'Marke'), ('05', 'Sprache & Schreibweisen', 'Marke'), ('06', 'Logo-Aufbau', 'Logo'),
       ('07', 'Logo-Varianten', 'Logo'), ('08', 'Schutzraum & Größen', 'Logo'), ('09', 'Platzierung & Hintergründe', 'Logo'), ('10', 'Fehlanwendungen', 'Logo'),
       ('11', 'Farbwelt', 'Design'), ('12', 'Farbe anwenden', 'Design'), ('13', 'Farbe im Druck', 'Design'), ('14', 'Typografie', 'Design'), ('15', 'Schriftgrößen', 'Design'),
       ('16', 'Layout & Abstände', 'Design'), ('17', 'Erkennungszeichen', 'Design'), ('18', 'Bausteine & Icons', 'Design'), ('19', 'Bildsprache', 'Bild'),
       ('20', 'KI-Bilder: Grundlagen', 'Bild'), ('21', 'KI-Bilder: Vorlagen', 'Bild'), ('22', 'Website & Oberflächen', 'Anwendung'), ('23', 'Social Media & Anzeigen', 'Anwendung'),
       ('24', 'Druck & Ausstattung', 'Anwendung'), ('25', 'Botschaften & Vorstellung', 'Kommunikation'), ('26', 'Dateien & Umstellung', 'Praxis'), ('27', 'Kurzreferenz', 'Kurzreferenz')]


def p02():
    def col(items):
        return '<table class="kv w">' + ''.join('<tr><td style="color:%s">%s</td><td style="font-weight:600">%s</td><td style="text-align:right;color:%s;font-weight:400">%s</td></tr>' % (PFAU, a, b, NEBEN, c) for a, b, c in items) + '</table>'
    toc = card('<div class="g g2" style="gap:30px;align-items:start">' + col(TOC[:14]) + col(TOC[14:]) + '</div>')
    a = card('<h2>So lesen Sie das Handbuch</h2><p style="margin-bottom:8px"><b>C</b> ist die Höhe des Großbuchstabens „M“ der Wortmarke. Alle Maße am Logo beziehen sich darauf und gelten deshalb in jeder Größe.</p>'
             '<p style="margin-bottom:8px"><span class="tag">OFFEN</span> kennzeichnet einen Punkt, der noch einen Nachweis braucht. Offene Punkte werden nie geschätzt.</p>'
             '<p>Kontrastangaben wie 7,9:1 folgen dem Standard WCAG 2.2. Ab 4,5:1 ist Text gut lesbar, ab 3:1 große Schrift und grafische Elemente.</p>')
    b = card('<h2>Die Marke in einem Absatz</h2><p>Markentrix sieht nicht aus wie eine Digitalagentur, sondern wie ein Betrieb von nebenan: klares helles Papier, ein Tintenton, ein tiefes Pfauenblau und ein warmer Akzent in Kupfer, der zur Handlung führt. '
             'Kräftige Überschriften wie auf einem Ladenschild, ruhiger Text, viel freie Fläche. Alles ist aus Dingen abgeleitet, die man anfassen kann.</p>')
    c = card('<h2>Was sich gegenüber Version 3.0 ändert</h2><div class="g g3" style="gap:16px">'
             '<p><b>Neuer Grund.</b> Salz und Reif lösen Kreide und Leinen ab. Die Seite ist kühl und klar statt cremig. Der Rest der Palette bleibt.</p>'
             '<p><b>Kupfer führt.</b> Kupfer ist jetzt die Handlungsfarbe: Hauptknopf und ein Schlüsselwort je Überschrift. Der Kupferstrich unter Wörtern entfällt.</p>'
             '<p><b>Farbe im Wechsel.</b> Helle Flächen wechseln mit Pfauenblau und Tiefsee. Angebot, Beweis und Abschluss stehen auf Farbe.</p></div>'
             '<p style="margin-top:9px" class="small"><b>Seit Version 2:</b> Der Cyan-Violett-Verlauf, Violett und Magenta sowie Space Grotesk und Inter sind entfallen. Archivo und Source Sans 3 bleiben.</p>')
    body = toc + '<div class="g g2 mt2">' + a + b + '</div><div class="mt2">' + c + '</div>'
    return page(2, 'Einstieg', 'Inhalt & Geltung', 'Inhalt &amp; ' + k('Geltung'),
                'Dieses Handbuch ist die verbindliche Grundlage für jeden Markentrix-Auftritt: Website, Social Media, Druck, Angebote und KI-generierte Bilder. Bei Widerspruch zu älteren Dateien gilt dieses Handbuch.', body)


def p03():
    c = lambda lbl, txt, cls='': card('<div class="lbl">%s</div>%s' % (lbl, txt), cls)
    row1 = grid('g2', c('Positionierung', '<p style="font-size:13px;line-height:1.45">Markentrix baut für lokale Betriebe Websites, Werbung und Automatisierung als ein System, das Anfragen bringt und Aufwand spart.</p>'),
                c('Kernversprechen', '<p style="font-size:13px;line-height:1.45">Wir sorgen dafür, dass ein Betrieb gefunden wird, dass aus Besuchern Anfragen werden und dass Routine nicht mehr an der Inhaberin oder dem Inhaber hängt.</p>'))
    row2 = grid('g2', c('Kurzfassung', '<p style="font-size:13px;line-height:1.45">Websites, Werbung und Automatisierung für lokale Betriebe.</p>'),
                c('Claim', '<div style="font:800 19px/1.12 Archivo;letter-spacing:-.015em">Mehr Anfragen. ' + k('Weniger Aufwand.') + '</div>'))
    row3 = grid('g3', c('Für wen', '<p>Lokale, inhabergeführte Betriebe und Vereine jeder Branche. Entscheider ist meist die Inhaberin oder der Inhaber selbst.</p>'),
                c('Was Sie brauchen', '<p>Mehr Anfragen ohne eigenen Zeitaufwand, einen festen Ansprechpartner, klare Preise und verständliche Sprache ohne Fachbegriffe.</p>'),
                c('Woran man uns misst', '<p>An Anfragen, Terminen und eingesparter Zeit. Reichweite und Likes sind Mittel, kein Ergebnis.</p>'))
    br = card('<div class="g g5" style="gap:14px"><div><b>Handwerk</b><div class="small">Elektro, Sanitär, Bau, Tischlerei</div></div><div><b>Kfz und Autopflege</b><div class="small">Werkstatt, Aufbereitung</div></div>'
              '<div><b>Handel</b><div class="small">Hofladen, Fleischerei, Fachgeschäft</div></div><div><b>Land und Garten</b><div class="small">Gartenservice, Lohnunternehmer</div></div>'
              '<div><b>Pferd und Verein</b><div class="small">Ponyclub, Reitverein</div></div></div>'
              '<p class="small" style="margin-top:10px">Die Liste ist offen. Markentrix bietet für jede Branche die passende Website. Deshalb gehört kein Element der Marke einer einzelnen Branche: keine Werkzeug-Symbole, keine Naturfarben, keine Technik-Optik.</p>')
    ist = card('<h2>Was Markentrix ist</h2>' + lst(['Ein fester Ansprechpartner statt eines Agentur-Apparats', 'Ein System statt einzelner Maßnahmen', 'Festpreis und klarer Umfang', 'Aus Celle, für Betriebe in der Region und darüber hinaus']))
    nicht = card('<h2>Was Markentrix nicht ist</h2>' + lst(['Eine reine Posting-Agentur', 'Ein Baukasten zum Selbermachen', 'Ein Technik-Start-up mit Fachsprache', 'Ein Anbieter für Konzerne'], 'x'))
    body = '<div class="g" style="gap:11px">' + row1 + row2 + row3 + '</div><h2 class="mt" style="margin-top:20px">Branchen, für die wir bauen</h2>' + br + '<div class="g g2 mt2">' + ist + nicht + '</div>'
    return page(3, 'Marke', 'Positionierung', 'Positionierung &amp; ' + k('Markenkern'), 'Was uns antreibt. Wofür wir stehen. Was wir bewirken.', body)


def p04():
    wirkt = card('<h2>Markentrix wirkt</h2><div class="g g2" style="gap:6px 16px">' + lst(['verlässlich', 'persönlich', 'hochwertig', 'bodenständig', 'klar']) + lst(['professionell', 'präzise', 'unternehmerisch', 'ruhig', 'zugewandt']) + '</div>')
    nicht = card('<h2>Markentrix wirkt nicht</h2><div class="g g2" style="gap:6px 16px">' + lst(['verspielt', 'billig', 'austauschbar', 'wie eine Vorlage'], 'x') + lst(['wie Krypto oder Gaming', 'neonlastig', 'technikverliebt', 'wie ein KI-Klischee'], 'x') + '</div>')
    ton = card('<div class="lbl">Tonalität</div><div class="g g3" style="gap:18px"><div><b style="font:700 12.5px Archivo">Direkt statt laut.</b><p>Wir sprechen klar und auf den Punkt, ohne zu übertreiben.</p></div>'
               '<div><b style="font:700 12.5px Archivo">Fachlich statt allgemein.</b><p>Wir kommunizieren kompetent, mit Substanz und konkretem Mehrwert.</p></div>'
               '<div><b style="font:700 12.5px Archivo">Nutzen statt Show.</b><p>Wir zeigen, was es bringt: echte Ergebnisse, keine leeren Versprechen.</p></div></div>')
    rows = [('Überschrift', 'Websites, die Anfragen bringen.', 'Ihr innovativer Partner für ganzheitliche Digitallösungen.'),
            ('Leistung erklären', 'Jede Anfrage landet in Ihrem Portal. Sie sehen sofort, wer geschrieben hat.', 'Unsere KI-gestützte Lösung optimiert nahtlos Ihre Customer Journey.'),
            ('Knopf', 'Erstgespräch buchen', 'Jetzt durchstarten!'), ('Ergebnis nennen', 'Live in 5 bis 15 Werktagen.', 'Blitzschnell online, garantiert die beste Lösung.'),
            ('Absage oder Grenze', 'Das können wir nicht zusagen. Was wir zusagen können: …', 'Leider ist das aktuell nicht möglich.')]
    tb = '<div class="card"><table class="tb"><tr><th style="width:22%">Anlass</th><th style="width:38%">So schreiben wir</th><th>So nicht</th></tr>' + ''.join('<tr><td>%s</td><td style="font-weight:400">%s</td><td style="font-weight:400">%s</td></tr>' % r for r in rows) + '</table></div>'
    b3 = grid('g3', card('<h2>Vier Prüffragen vor dem Senden</h2>' + lst(['Versteht es eine Inhaberin beim ersten Lesen?', 'Steht der Nutzen im ersten Satz?', 'Ist jede Aussage belegbar?', 'Lässt sich ein Wort streichen?'])),
              card('<h2>Satzbau</h2>' + lst(['Kurze Hauptsätze, aktive Verben', 'Ein Gedanke je Satz', 'Fachbegriffe erklären oder weglassen', 'Zahlen statt Adjektive'])),
              card('<h2>Haltung</h2>' + lst(['Auf Augenhöhe, nie belehrend', 'Zusagen, die wir halten können', 'Grenzen offen benennen', 'Kein Verkaufsdruck'])))
    body = '<div class="g g2">' + wirkt + nicht + '</div><div class="mt2">' + ton + '</div><h2 style="margin:20px 0 8px">So klingt das konkret</h2>' + tb + '<div class="mt2">' + b3 + '</div>'
    return page(4, 'Marke', 'Charakter & Tonalität', 'Markencharakter &amp; ' + k('Tonalität'), 'Markentrix wirkt klar, bodenständig und hochwertig. Direkt, fachlich und selbstbewusst: nicht laut, sondern präzise und nutzenorientiert.', body)


def p05():
    fest = card('<h2>Feste Schreibweisen</h2>' + kv([('Markenname', 'Markentrix. Großes M, ein Wort, nie in Versalien, nie getrennt, nie „markentrix“.'), ('Anrede', 'Sie, in allen Kanälen. Du nur auf ausdrücklichen Wunsch des Gegenübers.'),
                                                       ('Wir oder ich', '„Wir“ für die Agentur, „ich“ wenn Christian Wien persönlich spricht.'), ('Preise', '599 € · 1.099 € · 29,99 € im Monat. Tausenderpunkt, Leerzeichen vor €, immer mit Hinweis netto oder brutto.'),
                                                       ('Datum', '13.11.2026 oder 13. November 2026.'), ('Telefon', '0176 20370429, international +49 176 20370429.'), ('Zeiträume', '5 bis 15 Werktage im Fließtext, 5–15 nur in Tabellen.'),
                                                       ('Anführungszeichen', '„deutsch“, nie "gerade".')]))
    wort = card('<h2>Wortwahl</h2><div class="lbl n">Bevorzugt</div><p style="margin-bottom:9px">Anfrage, Termin, Betrieb, Kunde, Festpreis, Ansprechpartner, live, sichtbar, gefunden werden, Aufwand sparen, System.</p>'
                '<div class="lbl n">Nicht verwenden</div><p style="margin-bottom:9px">„Ihr Partner für“, maßgeschneidert, innovativ, ganzheitlich, nahtlos, „auf das nächste Level“, revolutionär, Game-Changer, unbelegte Superlative wie „die beste“ oder „Nr. 1“.</p>'
                '<div class="lbl n">Englisch</div><p>Nur, wo es der übliche Begriff ist: Website, Landingpage, SEO, Newsletter. Sonst deutsch: Anfrage statt Lead, Auswertung statt Reporting, Erstgespräch statt Kick-off.</p>')
    r2 = grid('g3', card('<h2>Überschriften</h2>' + lst(['Höchstens zwei Zeilen', 'Aussage, keine Frage ohne Antwort', 'Punkt am Ende erlaubt', 'Keine Versalien, kein Ausrufezeichen'])),
              card('<h2>Knöpfe und Links</h2>' + lst(['Verb plus Gegenstand: „Termin buchen“', 'Höchstens vier Wörter', 'Linktext sagt, wohin er führt', 'Nie „Hier klicken“ oder „Mehr“'])),
              card('<h2>Zahlen und Belege</h2>' + lst(['Kennzahlen nur mit Quelle und Zeitraum', 'Kundenstimmen nur mit Freigabe', 'Keine erfundenen Referenzen', 'Fehlt ein Beleg, fehlt die Zahl'])))
    r3 = grid('g2', card('<h2>Branchenneutral schreiben</h2><p>Allgemeine Texte sprechen von „Betrieb“ und „Kunden“, nicht von „Baustelle“ oder „Aufträgen“. Branchenseiten dürfen und sollen die Sprache der jeweiligen Branche sprechen.</p>'),
              card('<h2>KI in Texten</h2><p>KI ist Werkzeug, nie Verkaufsargument für sich. Immer zuerst sagen, was der Betrieb davon hat: „Der Assistent nimmt Anrufe an und trägt Termine ein.“</p>'))
    r4 = card('<h2>Emojis und Satzzeichen</h2><p>In Social-Media-Texten höchstens ein Emoji je Beitrag, nie in Überschriften, Angeboten und auf der Website. Ein Ausrufezeichen je Text ist die Obergrenze.</p>')
    body = '<div class="g g2" style="align-items:start">' + fest + wort + '</div><div class="mt2">' + r2 + '</div><div class="g g2 mt2">' + r3.replace('class="g g2 "', '') + '</div><div class="mt2">' + r4 + '</div>'
    body = '<div class="g g2" style="align-items:stretch">' + fest + wort + '</div><div class="mt2">' + r2 + '</div><div class="mt2">' + r3 + '</div><div class="mt2">' + r4 + '</div>'
    return page(5, 'Marke', 'Sprache & Schreibweisen', 'Sprache &amp; ' + k('Schreibweisen'), 'Einheitliche Schreibweisen wirken so stark wie ein einheitliches Logo. Diese Regeln gelten für Website, Angebote, E-Mails, Anzeigen und Social Media.', body)


def p06():
    # Konstruktionsbild: Logo mit Maßklammern (Maße in C = Höhe des M der Wortmarke)
    mass = ('<div style="position:relative;height:178px">'
            '<div style="position:absolute;left:116px;top:56px">' + img(L_HELL, w=438) + '</div>'
            '<div style="position:absolute;left:116px;top:20px;width:70px;border-top:1px solid %s;height:6px;border-left:1px solid %s;border-right:1px solid %s"></div>' % (KUPFER_D, KUPFER_D, KUPFER_D) +
            '<div style="position:absolute;left:116px;top:2px;font:700 9px \'Source Sans 3\';color:%s">Bildmarke 1,94 C</div>' % KUPFER_D +
            '<div style="position:absolute;left:215px;top:20px;width:340px;border-top:1px solid %s;height:6px;border-left:1px solid %s;border-right:1px solid %s"></div>' % (KUPFER_D, KUPFER_D, KUPFER_D) +
            '<div style="position:absolute;left:330px;top:2px;font:700 9px \'Source Sans 3\';color:%s">Wortmarke 7,57 C</div>' % KUPFER_D +
            '<div style="position:absolute;left:116px;top:134px;width:22px;border-bottom:1px solid %s;height:6px;border-left:1px solid %s;border-right:1px solid %s"></div>' % (KUPFER_D, KUPFER_D, KUPFER_D) +
            '<div style="position:absolute;left:70px;top:148px;font:700 9px \'Source Sans 3\';color:%s">Abstand 0,62 C</div>' % KUPFER_D +
            '<div style="position:absolute;left:92px;top:56px;height:56px;border-top:1px solid %s;border-bottom:1px solid %s;border-left:1px solid %s;width:6px"></div>' % (KUPFER_D, KUPFER_D, KUPFER_D) +
            '<div style="position:absolute;left:44px;top:80px;font:700 9px \'Source Sans 3\';color:%s">1,66 C</div>' % KUPFER_D +
            '<div style="position:absolute;left:566px;top:70px;height:34px;border-top:1px solid %s;border-bottom:1px solid %s;border-right:1px solid %s;width:6px"></div>' % (KUPFER_D, KUPFER_D, KUPFER_D) +
            '<div style="position:absolute;left:578px;top:82px;font:700 9px \'Source Sans 3\';color:%s">C</div></div>' % KUPFER_D)
    top = card(mass)
    cap = '<p class="small" style="margin:8px 0 14px">C ist die Höhe des „M“ der Wortmarke. Gestrichelt: Grundlinie und Versalhöhe. Die Rundungen der Bildmarke stehen 0,03 C unter der Grundlinie, damit beide optisch auf einer Linie stehen.</p>'
    bm = card('<div class="g" style="grid-template-columns:150px 1fr;gap:18px"><div><h2>Bildmarke</h2>' + img(B_HELL, w=110, style='margin-top:20px;opacity:.9') + '</div>' +
              kv([('Aufbau', 'Striche mit runden Enden und runden Ecken, entlang der gezeigten Mittellinie'), ('Seitenverhältnis', '522 : 447 (Breite : Höhe)'), ('Strich des M', '18,3 % der Markenhöhe'),
                  ('Strich des Pfeils', '12,1 % der Markenhöhe, also zwei Drittel des M-Strichs'), ('Farben', 'Linker Abstrich, linke Schräge und rechter Abstrich in Tiefsee. Der Aufstrich und der Pfeil in Pfauenblau.'),
                  ('Lage', 'Die Aufwärtslinie liegt über den Tiefsee-Strichen'), ('Bedeutung', 'M für Markentrix. Aus dem M wächst eine Linie nach oben: mehr Anfragen.')]) + '</div>')
    wm = card('<div class="g" style="grid-template-columns:180px 1fr;gap:18px"><div><h2>Wortmarke</h2><div style="font:800 36px Archivo;letter-spacing:-.02em;margin-top:12px">Markentrix</div></div>' +
              kv([('Schrift', 'Archivo ExtraBold (800), Laufweite −2 %'), ('Schreibweise', 'Großes M, danach klein'), ('Farbe', 'Tiefsee, auf dunklem Grund Weiß'), ('Dateien', 'In Kurven umgewandelt, keine Schrift nötig')]) + '</div>')
    herk = '<div class="note mt2"><b>Zur Herkunft:</b> Die Bildmarke wurde aus der bisherigen Bilddatei vermessen und stimmt in der Form zu 99,5 % mit ihr überein. Sie liegt jetzt als Vektor vor und sieht in jeder Größe gleich aus. Das Logo wird nie getippt, nachgezeichnet oder von einer KI erzeugt, sondern immer aus den Dateien auf Seite 26 eingesetzt.</div>'
    return page(6, 'Logo', 'Logo-Aufbau', 'Logo: Aufbau &amp; ' + k('Konstruktion'), 'Die Form des Logos bleibt, wie sie war: ein M mit Pfeil. Neu sind die Farben und die Schrift der Wortmarke. Der Verlauf entfällt.',
                top + cap + bm + '<div class="mt2">' + wm + '</div>' + herk)


def p07():
    def v(bg, logo, cap, border=True):
        st = 'background:%s;%s' % (bg, 'border:1px solid %s;' % LINIE if border else '')
        return '<div><div style="%sborder-radius:9px;height:76px;display:flex;align-items:center;justify-content:center">%s</div><div class="cap" style="margin-top:6px">%s</div></div>' % (st, img(logo, w=150), cap)
    vs = ('<div class="g g3" style="gap:12px 11px">' + v(SALZ, L_HELL, '<b>1 · Farbe auf Hell.</b> Standard für alles.') + v(TIEFSEE, L_DUNKEL, '<b>2 · Farbe auf Dunkel.</b> Nur auf Tiefsee.', False) +
          v(SALZ, L_TIEF, '<b>3 · Tiefsee einfarbig.</b> Wenn nur eine Farbe geht.') + v(WEISS, L_SCHWARZ, '<b>4 · Schwarz einfarbig.</b> Stempel, Schwarz-Weiß-Druck.') +
          v(PFAU, L_WEISS, '<b>5 · Weiß einfarbig.</b> Auf Pfauenblau, Fotos, Textil.', False) +
          '<div><div style="border:1px solid %s;background:%s;border-radius:9px;height:76px;display:flex;align-items:center;justify-content:center;gap:22px">%s%s</div><div class="cap" style="margin-top:6px"><b>6 · Bildmarke.</b> In Farbe, Tiefsee oder Weiß.</div></div>' % (LINIE, SALZ, img(B_HELL, h=34), img(B_TIEF, h=34)) + '</div>')
    prof = card('<h2>Profilbild und App-Icon</h2><div style="display:flex;gap:14px;margin:6px 0 10px">'
                '<div style="width:78px;height:78px;border-radius:50%%;background:%s;border:1px solid %s;display:flex;align-items:center;justify-content:center">%s</div>' % (SALZ, LINIE, img(B_HELL, w=44)) +
                '<div style="width:78px;height:78px;border-radius:16px;background:%s;border:1px solid %s;display:flex;align-items:center;justify-content:center">%s</div>' % (SALZ, LINIE, img(B_HELL, w=44)) +
                '<div style="width:78px;height:78px;border-radius:16px;background:%s;display:flex;align-items:center;justify-content:center">%s</div></div>' % (TIEFSEE, img(B_DUNKEL, w=44)) +
                '<p>Die Bildmarke nimmt 56 % der Kantenlänge ein und steht mittig. So bleibt sie auch im runden Zuschnitt vollständig sichtbar. Standard ist die helle Fassung auf Salz.</p>')
    reih = card('<h2>Verbindliche Reihenfolge</h2>' + ol(['<b>Hell ist Standard</b> für alle Medien.', '<b>Dunkel ist die Ausnahme,</b> nur auf bewusst dunklen Flächen.', '<b>Einfarbig</b> nur aus technischem Grund: Stick, Folie, Stempel.', '<b>Bildmarke allein</b> nur, wo der Name daneben steht oder der Platz nicht reicht.'], 'n z'))
    tab = [('Website, Präsentation, Angebot, Brief', '1 · Farbe auf Hell', 'SVG'), ('Social-Media-Grafik, Canva', '1 · Farbe auf Hell', 'PNG mit transparentem Grund'), ('Profilbild, Favicon', 'Profilbild hell', 'PNG 1024 px, Favicon aus SVG'),
           ('Druckerei', '1 oder 3, je nach Verfahren', 'SVG oder PDF, nie PNG'), ('Fahrzeug, Schild, Kleidung, Stick', '3 · Tiefsee oder 5 · Weiß', 'SVG'), ('Foto oder Video als Hintergrund', '5 · Weiß oder 3 · Tiefsee', 'PNG oder SVG')]
    t = '<div class="card"><table class="tb"><tr><th style="width:38%">Einsatz</th><th style="width:30%">Variante</th><th>Dateiformat</th></tr>' + ''.join('<tr><td>%s</td><td style="font-weight:400">%s</td><td style="font-weight:400">%s</td></tr>' % r for r in tab) + '</table></div>'
    return page(7, 'Logo', 'Logo-Varianten', 'Logo-' + k('Varianten'), 'Alle Varianten sind dieselbe Marke in anderer Einfärbung. Form und Proportionen bleiben immer gleich.',
                vs + '<div class="g g2 mt2">' + prof + reih + '</div><h2 style="margin:18px 0 8px">Welche Variante wofür</h2>' + t)


def p08():
    schutz1 = ('<div class="card" style="height:240px;display:flex;align-items:center;justify-content:center"><div style="position:relative;background:%s;border:1px dashed %s;padding:20px 20px;width:330px">'
               '<div style="background:%s;padding:0">%s</div>' % (REIF, KUPFER_D, SALZ, img(L_HELL, w=290)) +
               '<span style="position:absolute;left:50%;top:3px;font:700 9px Source Sans 3;color:' + KUPFER_D + '">C</span><span style="position:absolute;left:5px;top:50%;font:700 9px Source Sans 3;color:' + KUPFER_D + '">C</span>'
               '<span style="position:absolute;right:5px;top:50%;font:700 9px Source Sans 3;color:' + KUPFER_D + '">C</span><span style="position:absolute;left:50%;bottom:3px;font:700 9px Source Sans 3;color:' + KUPFER_D + '">C</span></div></div>')
    schutz2 = ('<div class="card" style="height:240px;display:flex;align-items:center;justify-content:center"><div style="position:relative;background:%s;border:1px dashed %s;padding:30px">'
               '<div style="background:%s;padding:0">%s</div>' % (REIF, KUPFER_D, SALZ, img(B_HELL, w=100)) +
               '<span style="position:absolute;left:50%;top:6px;font:700 9px Source Sans 3;color:' + KUPFER_D + '">¼ H</span><span style="position:absolute;left:3px;top:50%;font:700 9px Source Sans 3;color:' + KUPFER_D + '">¼ H</span>'
               '<span style="position:absolute;right:3px;top:50%;font:700 9px Source Sans 3;color:' + KUPFER_D + '">¼ H</span><span style="position:absolute;left:50%;bottom:6px;font:700 9px Source Sans 3;color:' + KUPFER_D + '">¼ H</span></div></div>')
    caps = '<div class="g g2" style="margin:8px 0 14px"><p class="cap"><b>Logo:</b> Rundum mindestens C, die Höhe des „M“ der Wortmarke. Das entspricht 60 % der Höhe der Bildmarke.</p><p class="cap"><b>Bildmarke allein:</b> Rundum mindestens ein Viertel ihrer Höhe (¼ H).</p></div>'
    mind = card('<h2>Mindestgrößen</h2><table class="tb"><tr><th></th><th>Digital</th><th>Druck</th></tr><tr><td>Logo, Breite</td><td style="font-weight:400">120 px</td><td style="font-weight:400">30 mm</td></tr>'
                '<tr><td>Bildmarke, Breite</td><td style="font-weight:400">32 px</td><td style="font-weight:400">8 mm</td></tr><tr><td>Favicon</td><td style="font-weight:400">16 px, nur Bildmarke</td><td style="font-weight:400">entfällt</td></tr>'
                '<tr><td>Stick</td><td style="font-weight:400">entfällt</td><td style="font-weight:400">Bildmarke 25 mm hoch, Logo 80 mm breit</td></tr></table>'
                '<p class="small" style="margin-top:8px">Unter der Mindestgröße des Logos immer die Bildmarke verwenden. Die Stick-Maße sind Richtwerte und werden mit dem Hersteller abgestimmt.</p>')
    gr = card('<h2>Größe im Format</h2><table class="tb"><tr><th>Format</th><th>Logo-Breite</th></tr><tr><td>Website, Kopfzeile</td><td style="font-weight:400">150 bis 190 px</td></tr><tr><td>A4, Brief und Angebot</td><td style="font-weight:400">45 bis 55 mm</td></tr>'
              '<tr><td>Visitenkarte 85 × 55 mm</td><td style="font-weight:400">32 mm</td></tr><tr><td>Social Media 1080 px</td><td style="font-weight:400">200 bis 260 px</td></tr><tr><td>Präsentation 16:9</td><td style="font-weight:400">12 bis 15 % der Folienbreite</td></tr></table>'
              '<p class="small" style="margin-top:8px">Das Logo ist Absender, nicht Hauptmotiv. Ausnahme: Titel- und Schlussseiten.</p>')
    vgl = card('<h2>Kleinste Größen im Vergleich</h2><div style="display:flex;align-items:flex-end;gap:36px;margin:8px 0 8px">'
               '<div>%s<div class="cap">190 px · Kopfzeile</div></div><div>%s<div class="cap">120 px · Minimum</div></div><div>%s<div class="cap">32 px</div></div><div>%s<div class="cap">16 px · Favicon</div></div></div>' % (img(L_HELL, w=190), img(L_HELL, w=120), img(B_HELL, w=32), img(B_HELL, w=16)) +
               '<p class="small">Darstellung in Originalgröße bei 100 % Ansicht. Im Ausdruck entspricht 1 px dieser Seite etwa 0,26 mm.</p>')
    return page(8, 'Logo', 'Schutzraum & Größen', 'Schutzraum &amp; ' + k('Mindestgrößen'), 'Der Schutzraum ist die Fläche rund um das Logo, die immer frei bleibt: kein Text, kein Bild, keine Linie, kein Formatrand.',
                '<div class="g g2">' + schutz1 + schutz2 + '</div>' + caps + '<div class="g g2">' + mind + gr + '</div><div class="mt2">' + vgl + '</div>')


def p09():
    def mini(content, cap):
        return '<div><div style="background:%s;border:1px solid %s;border-radius:9px;height:152px;position:relative;overflow:hidden">%s</div><div class="cap"><b>%s</b></div></div>' % (SALZ, LINIE, content, cap)
    m1 = mini('<div style="position:absolute;left:12px;top:12px">%s</div><div style="position:absolute;left:12px;top:44px;width:120px;height:5px;background:%s"></div><div style="position:absolute;left:12px;top:56px;width:96px;height:3px;background:%s"></div>' % (img(L_HELL, w=58), '#C9D1D5', LINIE), 'Dokumente, Website: oben links.')
    m2 = mini('<div style="position:absolute;left:14px;top:14px;width:100px;height:10px;background:#B8C2C7"></div><div style="position:absolute;left:14px;top:30px;width:90px;height:10px;background:#B8C2C7"></div><div style="position:absolute;left:14px;bottom:14px">%s</div>' % img(L_HELL, w=58), 'Social-Media-Grafik: unten links.')
    m3 = mini('<div style="position:absolute;left:0;right:0;top:52px;display:flex;justify-content:center">%s</div>' % img(L_HELL, w=104), 'Titel und Schlussseite: mittig.')
    m4 = mini('<div style="position:absolute;left:50%%;top:50%%;margin:-42px 0 0 -42px;width:84px;height:84px;border-radius:50%%;border:1px solid %s;display:flex;align-items:center;justify-content:center">%s</div>' % (LINIE, img(B_HELL, w=48)), 'Profilbild: Bildmarke mittig.')
    reg = card('<h2>Regeln zur Platzierung</h2>' + lst(['<b>Abstand zum Formatrand:</b> mindestens 1,5 C und nie weniger als die Seitenrand des Formats: 64 px bei Social Media, 20 mm auf A4.', '<b>Ein Platz je Medium:</b> Innerhalb einer Serie steht das Logo immer an derselben Stelle.',
                                                '<b>Einmal je Fläche:</b> Das Logo erscheint nie doppelt auf einer Seite oder Grafik.', '<b>Ausrichtung:</b> Die linke Kante der Bildmarke fluchtet mit der linken Textkante.', '<b>Nie rechts unten</b> bei Stories und Reels, dort liegen Bedienelemente der Plattform.']).replace('weniger als die Seitenrand', 'weniger als der Seitenrand'))
    nb = card('<h2>Logo neben anderen Logos</h2>' + lst(['<b>Trennung:</b> Zwischen zwei Logos steht eine feine senkrechte Linie in Reif, mit Abstand C auf beiden Seiten.', '<b>Gleiche optische Höhe:</b> Das Partnerlogo ist so hoch wie die Bildmarke, nie höher.',
                                                       '<b>Reihenfolge:</b> Markentrix steht links, wenn Markentrix Absender ist.', '<b>Kundenlogos</b> nur mit Zustimmung des Kunden und in dessen Originalfarben.']))

    def bgc(bg, cap, logo=L_HELL, ok=True, bd=True):
        mark = '<span class="ok">%s</span>' if ok else '<span class="no">%s</span>'
        return '<div><div style="background:%s;%sborder-radius:9px;height:64px;display:flex;align-items:center;justify-content:center">%s</div><div class="cap" style="margin-top:5px">%s</div></div>' % (bg, 'border:1px solid %s;' % LINIE if bd else '', img(logo, w=118), mark % cap)
    bgs = ('<div class="g g4" style="gap:9px 11px">' + bgc(SALZ, 'Salz') + bgc(WEISS, 'Weiß') + bgc(REIF, 'Reif') + bgc(TIEFSEE, 'Tiefsee, Logo für Dunkel', L_DUNKEL, bd=False) +
           bgc(PFAU, 'Pfauenblau, Logo in Weiß', L_WEISS, bd=False) +
           '<div><div style="background:linear-gradient(135deg,#B3BBC0,#6C7A80);border-radius:9px;height:64px;display:flex;align-items:center;justify-content:center">%s</div><div class="cap" style="margin-top:5px"><span class="ok">Ruhige Fotofläche, Logo einfarbig</span></div></div>' % img(L_WEISS, w=118) +
           bgc(KUPFER, 'Kupfer', L_TIEF, ok=False, bd=False) +
           '<div><div style="background:repeating-linear-gradient(45deg,#4E8A5A 0 14px,#C9504A 14px 28px,#D8A93C 28px 42px);border-radius:9px;height:64px;display:flex;align-items:center;justify-content:center">%s</div><div class="cap" style="margin-top:5px"><span class="no">Unruhiges Motiv</span></div></div>' % img(L_TIEF, w=118) + '</div>')
    faust = '<div class="note mt2"><b>Faustregel:</b> Das Farblogo steht nur auf Salz, Weiß, Reif oder Tiefsee. Auf allem anderen steht die einfarbige Fassung in Weiß oder Tiefsee, je nachdem, was stärker kontrastiert. Reicht der Kontrast nicht, kommt eine Salz-Fläche mit Schutzraum unter das Logo.</div>'
    return page(9, 'Logo', 'Platzierung & Hintergründe', 'Platzierung &amp; ' + k('Hintergründe'), 'Wo das Logo steht und worauf es stehen darf. Ein fester Platz macht jede Fläche sofort als Markentrix erkennbar.',
                '<div class="g g4" style="gap:11px">' + m1 + m2 + m3 + m4 + '</div><div class="g g2 mt2">' + reg + nb + '</div><h2 style="margin:16px 0 8px">Erlaubte Hintergründe</h2>' + bgs + faust)


def p10():
    def bad(inner, cap, bg=SALZ, extra=''):
        return ('<div><div style="position:relative;background:%s;border:1px solid %s;border-radius:9px;height:88px;display:flex;align-items:center;justify-content:center;overflow:hidden;%s">'
                '<span style="position:absolute;left:8px;top:8px;width:16px;height:16px;border-radius:50%%;background:%s;color:#fff;font:700 10px/16px Source Sans 3;text-align:center">×</span>%s</div><div class="cap" style="margin-top:5px">%s</div></div>') % (bg, LINIE, extra, FEHLER, inner, cap)
    old_grad = recolor('markentrix-bildmarke-farbe-hell.svg', {'#0C2128': '#2EA8FF', '#045268': '#7A5CF5'})
    g = ('<div class="g g3" style="gap:11px">' + bad(img(L_HELL, w=170, style='transform:scaleX(1.18) scaleY(.82)'), '<b>verzerrt</b> oder gestaucht werden') +
         bad(img(L_HELL, w=170, style='transform:rotate(-9deg)'), '<b>gedreht</b> oder schräg gestellt werden') +
         bad(img(recolor('markentrix-logo-farbe-hell.svg', {'#0C2128': '#8B1538', '#045268': '#D9265D'}), w=170), '<b>umgefärbt</b> werden') +
         bad(img(L_HELL, w=170, style='opacity:.18'), '<b>kontrastarm</b> oder transparent stehen') + bad(img(L_HELL, w=170, style='filter:drop-shadow(3px 5px 4px rgba(0,0,0,.5))'), 'mit <b>Schatten, Glanz oder Kontur</b> versehen werden') +
         bad('<div style="display:flex;align-items:center;gap:8px">%s<span style="font:400 22px Arial">markentrix</span></div>' % img(B_HELL, h=26), 'mit <b>anderer Schrift</b> oder kleinem „m“ gesetzt werden') +
         bad(img(old_grad, h=64), 'in der <b>alten Fassung mit Verlauf</b> erscheinen') +
         bad(img(L_TIEF, w=150), 'auf <b>unruhigem Grund</b> stehen', bg='repeating-linear-gradient(45deg,#4E8A5A 0 14px,#C9504A 14px 28px,#D8A93C 28px 42px)') +
         bad('<div style="display:flex;align-items:center;gap:6px">%s<div style="font:700 8px/1.1 Source Sans 3;margin-left:-14px">Ihre Agentur<br>aus Celle</div></div>' % img(L_HELL, w=150), 'im <b>Schutzraum bedrängt</b> werden') + '</div>')
    nz = card('<h2>Ebenfalls nicht zulässig</h2>' + lst(['Bildmarke und Wortmarke neu anordnen, etwa übereinander oder vertauscht', 'Einen Claim fest an das Logo anhängen', 'Die Farben von M und Aufwärtslinie vertauschen oder den Pfeil in Kupfer setzen',
                                                      'Das Logo als Muster, Wasserzeichen oder Hintergrund kacheln', 'Das Logo in einen Rahmen, Kreis oder ein Feld mit Kontur setzen', 'Pixelige oder unscharfe Dateien verwenden', 'Das Logo tippen, nachzeichnen oder von einer KI erzeugen lassen']))
    bs = card('<h2>Bestand, der zu ersetzen ist</h2><p style="margin-bottom:8px">Diese Fassungen sind im Umlauf und werden durch die Dateien aus diesem Handbuch ersetzt:</p>' +
              lst(['<b>Alle Logos mit Verlauf</b> in Cyan, Blau und Violett', '<b>Website-Kopfzeile:</b> dünner gezeichnete Bildmarke, Wortmarke kleingeschrieben („markentrix“)', '<b>E-Mail-Signatur:</b> Wortmarke in einer Ersatzschrift',
                   '<b>Profilbilder</b> auf Instagram, Facebook, YouTube, TikTok, Google und WhatsApp', '<b>Wortmarke in Space Grotesk</b>']))
    return page(10, 'Logo', 'Fehlanwendungen', 'Das Logo darf ' + k('nicht'), 'Jede dieser Abweichungen schwächt die Wiedererkennung. Im Zweifel gilt: Datei unverändert einsetzen, nur proportional skalieren.',
                g + '<div class="g g2 mt">' + nz + bs + '</div>')
