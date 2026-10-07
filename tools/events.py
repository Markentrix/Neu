#!/usr/bin/env python3
"""Rendert events.json -> Event-Karten + Schema.org-Event-JSON-LD in index.html (zwischen den Markern).
Aufruf: python3 tools/events.py   (wird von tools/build.sh automatisch ausgeführt)
Umgebungsvariablen: EVENTS_FILE (Standard events.json), EVENTS_TODAY (YYYY-MM-DD, nur zum Testen)."""
import json, os, re, sys, html
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
BERLIN = ZoneInfo('Europe/Berlin')
today = date.fromisoformat(os.environ['EVENTS_TODAY']) if os.environ.get('EVENTS_TODAY') else datetime.now(BERLIN).date()
data = json.load(open(os.path.join(root, os.environ.get('EVENTS_FILE', 'events.json')), encoding='utf8'))
MONS = {'de': ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'], 'en': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']}
WDS = {'de': ['Mo','Di','Mi','Do','Fr','Sa','So'], 'en': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']}
PAGES = [('index.html', 'de'), ('en/index.html', 'en')]
esc = lambda s: html.escape(str(s), quote=True)

def parse(ev):
    for k in ('title', 'date'):
        if not ev.get(k): sys.exit(f'events.json: Feld "{k}" fehlt in {ev}')
    d = date.fromisoformat(ev['date'])
    start = ev.get('start', '20:00'); end = ev.get('end', '01:00')
    s = datetime.combine(d, datetime.strptime(start, '%H:%M').time(), BERLIN)
    e = datetime.combine(d, datetime.strptime(end, '%H:%M').time(), BERLIN)
    if e <= s: e += timedelta(days=1)
    return d, start, end, s, e

upcoming = sorted((parse(e) + (e,) for e in data), key=lambda t: t[3])
upcoming = [t for t in upcoming if t[0] >= today]

def render(lang):
    MON, WD = MONS[lang], WDS[lang]
    en = lang == 'en'
    pre = '../' if en else ''
    g = lambda ev, k: ev.get(k + '_en') or ev.get(k) if en else ev.get(k)
    cards, ld = [], []
    for d, start, end, s_, e_, ev in upcoming:
        title = g(ev, 'title'); desc_t = g(ev, 'description'); tag_t = g(ev, 'tag')
        link = f'<a class="ev-link" href="{esc(ev["url"])}" target="_blank" rel="noopener">{"Learn more" if en else "Mehr Infos"}</a>' if ev.get('url') else ''
        tag = f'<p class="ev-tag">{esc(tag_t)}</p>' if tag_t else ''
        alt = (ev.get('image_alt_en') or ev.get('image_alt') or title) if en else ev.get('image_alt', title)
        img = f'<img class="ev-img" src="{pre}{esc(ev["image"])}" alt="{esc(alt)}" width="640" height="360" loading="lazy" decoding="async">' if ev.get('image') else ''
        desc = f'<p>{esc(desc_t)}</p>' if desc_t else ''
        datestr = f'{WD[d.weekday()]}, {MON[d.month-1]} {d.day}, {d.year}' if en else f'{WD[d.weekday()]}, {d.day}. {MON[d.month-1]} {d.year}'
        times = f'{esc(start)}–{esc(end)}' + ('' if en else ' Uhr')
        cards.append(f'''      <li class="event" data-date="{d.isoformat()}">
        <div class="ev-date" aria-hidden="true"><b>{d.day}</b><span>{MON[d.month-1]}</span><small>{WD[d.weekday()]}</small></div>
        <div class="ev-body">
          {tag}
          <h3>{esc(title)}</h3>
          <p class="ev-meta"><time datetime="{d.isoformat()}">{datestr}</time> · {times}</p>
          {desc}{link}
        </div>
        {img}
      </li>''')
        o = {
            '@type': 'Event', 'name': title,
            'startDate': s_.isoformat(timespec='minutes'), 'endDate': e_.isoformat(timespec='minutes'),
            'eventStatus': 'https://schema.org/EventScheduled',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'location': {'@type': 'Place', 'name': 'Bar Zeitreise', 'address': {'@type': 'PostalAddress', 'streetAddress': 'Hehlentorstraße 16', 'postalCode': '29221', 'addressLocality': 'Celle', 'addressRegion': 'Niedersachsen', 'addressCountry': 'DE'}},
            'organizer': {'@id': 'https://bar-zeitreise.de/#bar'},
            'url': 'https://bar-zeitreise.de/' + ('en/' if en else '') + '#events',
            'inLanguage': 'en' if en else 'de-DE',
            'typicalAgeRange': '18-',
        }
        if ev.get('free') is True:
            o['isAccessibleForFree'] = True
            o['offers'] = {'@type': 'Offer', 'price': 0, 'priceCurrency': 'EUR', 'availability': 'https://schema.org/InStock', 'url': 'https://bar-zeitreise.de/' + ('en/' if en else '') + '#events'}
        elif ev.get('price') is not None:
            o['offers'] = {'@type': 'Offer', 'price': ev['price'], 'priceCurrency': 'EUR', 'availability': 'https://schema.org/InStock', 'url': 'https://bar-zeitreise.de/' + ('en/' if en else '') + '#events'}
        if desc_t: o['description'] = desc_t
        o['image'] = ['https://bar-zeitreise.de/' + ev['image'].lstrip('/')] if ev.get('image') else ['https://bar-zeitreise.de/img/og-bar-zeitreise-celle.jpg']
        ld.append(o)
    p = os.path.join(root, PAGE_FILE[lang])
    h = open(p, encoding='utf8').read()
    h = re.sub(r'<!--events-->.*?<!--/events-->', lambda m: '<!--events-->\n' + '\n'.join(cards) + ('\n' if cards else '') + '<!--/events-->', h, flags=re.S)
    block = '<!--ld-events--><script type="application/ld+json" id="ld-events">' + json.dumps({'@context': 'https://schema.org', '@graph': ld}, ensure_ascii=False) + '</script><!--/ld-events-->' if ld else '<!--ld-events--><!--/ld-events-->'
    h = re.sub(r'<!--ld-events-->.*?<!--/ld-events-->', lambda m: block, h, flags=re.S)
    h = re.sub(r'<p class="events-empty" id="eventsEmpty"[^>]*>', '<p class="events-empty" id="eventsEmpty"' + (' hidden>' if cards else '>'), h)
    open(p, 'w', encoding='utf8').write(h)
    print(f'events[{lang}]: {len(cards)} kommende Events gerendert')

PAGE_FILE = {'de': 'index.html', 'en': 'en/index.html'}
for _, lang in PAGES:
    render(lang)
