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
pages = [("index.html","1.0","weekly"),("buchen.html","0.9","weekly"),("gutscheine.html","0.9","monthly"),("preise.html","0.9","monthly"),("kinder.html","0.8","monthly"),("firmen.html","0.8","monthly"),("kartbahn.html","0.7","monthly"),("faq.html","0.7","monthly"),("kontakt.html","0.8","monthly"),("agb.html","0.3","yearly"),("widerruf.html","0.2","yearly"),("impressum.html","0.2","yearly"),("datenschutz.html","0.2","yearly")]
today = datetime.date.today().isoformat()
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f'  <url><loc>/{p}</loc><lastmod>{today}</lastmod><changefreq>{c}</changefreq><priority>{pr}</priority></url>\n' for p,pr,c in pages) + '</urlset>\n'
write("sitemap.xml", sm)
write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /danke.html\nDisallow: /404.html\n")
write("site.webmanifest", '{\n  "name": "Burnout Celler-Kartbahn",\n  "short_name": "Kartbahn Celle",\n  "description": "Indoor-Kartbahn in Celle – online buchen, Preise, Gutscheine",\n  "start_url": "/index.html",\n  "display": "standalone",\n  "background_color": "#0b0b0d",\n  "theme_color": "#e10600",\n  "lang": "de",\n  "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]\n}\n')
write("favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#e10600"/><path d="M8 29 20 9l12 20H8z" fill="#fff"/><path d="M14 29l6-10 6 10z" fill="#e10600"/><rect x="8" y="30" width="24" height="3" fill="#fff"/></svg>\n')
