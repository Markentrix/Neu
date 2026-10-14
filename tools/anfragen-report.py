#!/usr/bin/env python3
"""Monatsauswertung der Anfragen aus anfragen.log (JSON je Zeile, geschrieben von api/anfrage.php).

Aufruf auf dem Server:  python3 tools/anfragen-report.py /pfad/zu/anfragen.log [--monate 6]
Zählt ohne Cookies und ohne Einwilligungsbanner, weil nur das Serverprotokoll gelesen wird.
"""
import argparse, collections, json, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log', help='Pfad zur anfragen.log')
    ap.add_argument('--monate', type=int, default=6, help='Anzahl der letzten Monate (Standard 6)')
    a = ap.parse_args()
    rows = []
    with open(a.log, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except ValueError: continue
    if not rows:
        print('Keine Einträge.'); return
    by_month = collections.defaultdict(list)
    for r in rows: by_month[(r.get('t') or '')[:7]].append(r)
    months = sorted(m for m in by_month if m)[-a.monate:]
    for m in months:
        rs = by_month[m]
        print(f'\n== {m}: {len(rs)} Anfragen, {sum(1 for r in rs if r.get("sent"))} per Mail zugestellt')
        for key, title in (('quelle', 'Herkunft'), ('bedarf', 'Bedarf'), ('thema', 'Leistung'), ('seite', 'Seite')):
            c = collections.Counter((r.get(key) or '').strip() or '(leer)' for r in rs)
            if len(c) == 1 and '(leer)' in c: continue
            print(f'  {title}:')
            for k, n in c.most_common(8): print(f'    {n:4d}  {k}')
    print(f'\nGesamt im Protokoll: {len(rows)} Anfragen seit {min((r.get("t") or "") for r in rows)[:10]}')

if __name__ == '__main__':
    main()
