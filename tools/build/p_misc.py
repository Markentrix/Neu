# -*- coding: utf-8 -*-
from common import *
import datetime

# ---------------- DANKE ----------------
html = head("Vielen Dank | Burnout Celler-Kartbahn", "Deine Anfrage ist bei uns eingegangen. Du erhältst eine Eingangsbestätigung mit Vorgangsnummer per E-Mail.", noindex=True) + header()
html += f'''
<section class="section"><div class="wrap" style="max-width:760px">
<span class="eyebrow">Eingangsbestätigung</span>
<h1 id="danke-title">Danke für deine Nachricht!</h1>
<div class="card card--accent">
  <p class="muted" style="margin:0">Deine Vorgangsnummer</p>
  <p style="font-family:var(--display);font-size:2rem;font-weight:800;margin:.2rem 0 .6rem;color:#fff" id="ref">–</p>
  <p id="danke-text">Wir melden uns so schnell wie möglich bei dir. Eine Eingangsbestätigung mit dieser Vorgangsnummer ist an deine E-Mail-Adresse unterwegs – bitte schau auch im Spam-Ordner nach.</p>
</div>
<p class="muted" style="margin-top:1.25rem">Bitte nenne die Vorgangsnummer bei Rückfragen. Du erreichst uns unter <a href="{TEL_LINK}">{TEL}</a>, per <a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp</a> oder <a href="mailto:{MAIL}">{MAIL}</a>.</p>
<div class="pill-row"><a class="btn btn--primary" href="index.html">Zur Startseite</a><a class="btn btn--ghost" href="preise.html">Preise ansehen</a><a class="btn btn--ghost" href="faq.html">Häufige Fragen</a></div>
</div></section>
''' + footer() + end()
write("danke.html", html)

# ---------------- 404 ----------------
html = head("Seite nicht gefunden | Burnout Celler-Kartbahn", "Diese Seite gibt es nicht mehr. Hier geht es zurück zur Startseite, zu den Preisen oder zur Online-Buchung der Celler Kartbahn.", noindex=True) + header()
html += f'''
<section class="hero hero--sub">
  <img class="hero__img" src="assets/img/strecke-reifen.webp" width="800" height="533" alt="Reifenstapel an der Kartbahn" >
  <div class="wrap">
    <span class="eyebrow">Fehler 404</span>
    <h1>Auslaufzone – diese Seite gibt es nicht</h1>
    <p class="lead">Die Adresse ist falsch oder die Seite wurde verschoben. Zurück auf die Strecke:</p>
    <div class="hero__actions"><a class="btn btn--primary" href="index.html">Startseite</a><a class="btn btn--light" href="buchen.html">Online buchen</a><a class="btn btn--ghost" href="preise.html">Preise</a><a class="btn btn--ghost" href="kontakt.html">Kontakt</a></div>
  </div>
</section>
''' + footer() + end()
write("404.html", html)

# ---------------- sitemap / robots / manifest ----------------
LLMS = """# Burnout Celler-Kartbahn

> Indoor-Kartbahn in Celle (Niedersachsen) mit ca. 600 m Strecke, Brücke, Tunnel und zweiter Ebene mit Steilkurve in 6 m Höhe. Betreiber: Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle. Familienbetrieb seit 2009, Geschäftsführer Christian Sprunk.

## Kurzfakten
- Adresse: Waldweg 100, 29221 Celle, Deutschland (Koordinaten 52.6088, 10.0614). Vom Bahnhof Celle max. 20 Minuten zu Fuß, Parkplätze am Haus.
- Telefon: 05141 908650 (+49 5141 908650). WhatsApp: +49 152 31394662. E-Mail: team@celler-kartbahn.com.
- Öffnungszeiten: Montag–Freitag ab 15:00 Uhr (niedersächsische Schulferien ab 13:00), Samstag ab 13:00, Sonntag ab 11:00 – jeweils Open End (Schluss je nach Auslastung, unter der Woche z. B. gegen 21 Uhr).
- Karts: Sodi SR5 mit 9 PS (seit 09/2023), 13 Kinderkarts Sodi LR6 (6,5 PS), 2 Doppelsitzer.
- Alter/Größe: Kinderkart ab 8 Jahren und 1,25 m; Rennkart ab 13 Jahren und 1,55 m (mit Erfahrung ab 12); Doppelsitzer-Beifahrer ab 4 Jahren und 1,10 m, Fahrer volljährig.
- Bezahlung vor Ort bar oder EC-Karte. Neukunden: Registrierung inkl. Rennlizenz 2 €, Sturmhaube inkl. Helmleihe 3 € (Paket 4 €).

## Preise (pro Person, 10 Minuten, Stand Oktober 2026)
- Samstag/Sonntag: 1 Fahrt 15,00 € (Kids 8–15: 13,50 €), 3 Fahrten 43 € (36 €), 5 Fahrten 60 € (50 €).
- Freitag: 1 Fahrt 14 € (12 €), 3 Fahrten 34 € (29 €), 5 Fahrten 49 € (41 €).
- Montag–Donnerstag (Spartage): 3 Fahrten zum Preis von 2 = 30 € (27 €), 5 Fahrten zum Preis von 3 = 43 € (36 €).
- Doppelsitzer (2 Personen): 1 Fahrt 18 €, 2 Fahrten 32 €, 3 Fahrten 45 €.
- Kidsparty/Kindergeburtstag (ab 6 Kindern, exklusiv): Paket F1 3 × 10 Min 40 € pro Kind, Paket F2 Grand-Prix-Modus 48 € pro Kind, Pizzapaket 10,50 €.
- Supercup/Rennen (6–17 Personen, exklusiv): Standard 39 €, Professional 49 €, Premium 59 €, Double Premium 59 €, Double Ultra 75 €, Grand Prix 49 €/59 €.
- Bahnmiete: 650 € pro Stunde inkl. 10 Karts, jede weitere halbe Stunde 325 €, jedes weitere Kart 65 €/Std. (max. 16 Karts).
- Schulklassen (ab 20 Personen, Mo–Fr): 20 € (20 Min) oder 25 € (30 Min + Getränk). Kinderkartführerschein 45 € (jeden 1. Samstag im Monat, 10 Uhr).
- RaceCam (Rennvideo per QR-Code): 5 € / 9 € / 12 €. Siegerehrung: Pokalsätze 30 € / 40 €, Medaille 1,90 €.

## Reservierung
- Unter 5 Personen: telefonisch ab 2 Tage vorher. Ab 5 Personen: online unter /buchen.html (kurzfristig innerhalb 3 Tagen telefonisch).
- Gutscheine und Tickets vorab: /gutscheine.html (PayPal oder Bestellung).

## Seiten
- [Startseite](/index.html): Überblick, Öffnungszeiten, News
- [Preise](/preise.html): vollständige Preisliste
- [Online buchen](/buchen.html): Fahrten, Kidsparty, Supercup, Bahnmiete, Schulklasse, Führerschein
- [Gutscheine](/gutscheine.html): Wertgutscheine und Fahrt-Tickets
- [Kinder](/kinder.html): Kindergeburtstag, Kinderkarts, Führerschein, Schulklassen
- [Firmen & Gruppen](/firmen.html): Supercup, Meisterschaftsmodus, Bahnmiete, Buffet, Veranstaltungsraum bis 80 Personen
- [Die Kartbahn](/kartbahn.html): Strecke, Karts, Rennlizenz-App, RaceCam, Bistro, Team, Fahrtipps
- [FAQ](/faq.html): häufige Fragen
- [Kontakt](/kontakt.html): Anfahrt, Formular
- [AGB](/agb.html), [Widerruf](/widerruf.html), [Impressum](/impressum.html), [Datenschutz](/datenschutz.html)
"""
IMAGES = {"index.html":["hero-rennen","zweite-ebene","bistro-theke"],"preise.html":["karts-boxengasse","kids-start"],"kinder.html":["kartflotte","kids-siegerehrung","kids-start"],"firmen.html":["strecke-start","veranstaltungsraum","strecke-boxengasse"],"kartbahn.html":["hero-strecke","kart-sodi-front","karts-boxengasse","bistro-lounge"],"gutscheine.html":["hero-duell","kart-detail"]}
pages = [("index.html","1.0","weekly"),("buchen.html","0.9","weekly"),("gutscheine.html","0.9","monthly"),("preise.html","0.9","monthly"),("kinder.html","0.8","monthly"),("firmen.html","0.8","monthly"),("kartbahn.html","0.7","monthly"),("faq.html","0.7","monthly"),("kontakt.html","0.8","monthly"),("agb.html","0.3","yearly"),("widerruf.html","0.2","yearly"),("impressum.html","0.2","yearly"),("datenschutz.html","0.2","yearly")]
today = datetime.date.today().isoformat()
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "".join(f'  <url><loc>/{p}</loc><lastmod>{today}</lastmod><changefreq>{c}</changefreq><priority>{pr}</priority>' + "".join(f'<image:image><image:loc>/assets/img/{i}.webp</image:loc></image:image>' for i in IMAGES.get(p,[])) + '</url>\n' for p,pr,c in pages) + '</urlset>\n'
write("sitemap.xml", sm)
write("robots.txt", "# Burnout Celler-Kartbahn – Suchmaschinen und KI-Assistenten sind willkommen\n" + "".join(f"User-agent: {b}\n" for b in ["*","Googlebot","Bingbot","Google-Extended","GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-Web","anthropic-ai","PerplexityBot","Perplexity-User","Applebot","Applebot-Extended","DuckDuckBot","CCBot","Amazonbot","meta-externalagent"]) + "Allow: /\nDisallow: /danke.html\nDisallow: /404.html\n\n# Sitemap (vollständige Adresse mit Domain wird vom Hosting ergänzt): /sitemap.xml\n# Kurzfassung für KI-Assistenten: /llms.txt\n")
write("llms.txt", LLMS)
if DEMO: write("robots.txt", "# Demo-Version – nicht für Suchmaschinen\nUser-agent: *\nDisallow: /\n")
write("site.webmanifest", '{\n  "name": "Burnout Celler-Kartbahn",\n  "short_name": "Kartbahn Celle",\n  "description": "Indoor-Kartbahn in Celle – online buchen, Preise, Gutscheine",\n  "start_url": "/index.html",\n  "display": "standalone",\n  "background_color": "#0b0b0d",\n  "theme_color": "#e10600",\n  "lang": "de",\n  "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]\n}\n')
write("favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#0b0b0d"/><text x="20" y="30" text-anchor="middle" font-family="Impact,Arial,sans-serif" font-style="italic" font-weight="900" font-size="30" fill="#e10600">B</text></svg>\n')
