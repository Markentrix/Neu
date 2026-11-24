# -*- coding: utf-8 -*-
"""Gezeichnete Bildelemente der Website als SVG: Schadenskizze (Fahrzeug von oben), Prüfstempel, Messskala.

Alles wird rechnerisch erzeugt, ohne Bilddateien, und passt sich per currentColor und CSS-Variablen an
Hell- und Dunkelmodus an.
"""
import math


def _catmull(points, closed=True):
    """Glatte Kurve durch Punkte als SVG-Pfad (Catmull-Rom nach kubischem Bezier)."""
    n = len(points)
    d = [f"M{points[0][0]:.1f},{points[0][1]:.1f}"]
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = points[(i - 1) % n] if (closed or i > 0) else points[i]
        p1 = points[i]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else points[(i + 1) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    if closed:
        d.append("Z")
    return "".join(d)


def _mirror(half, cy):
    """Obere Hälfte (x, Abstand von der Mittellinie) -> geschlossene Kontur um die Mittellinie cy."""
    top = [(x, cy - w) for x, w in half]
    bottom = [(x, cy + w) for x, w in reversed(half)]
    return top + bottom


def car_plan(width=960, height=430, label=""):
    """Schadenskizze: Pkw von oben, Front nach rechts, mit Maßlinie, Schadenszone und Nummernmarken."""
    cy = height / 2 - 6
    # Kontur der oberen Hälfte (x, halbe Breite), Heck links
    body_half = [(122, 0), (124, 62), (138, 108), (176, 134), (262, 146), (400, 150), (520, 150),
                 (640, 144), (730, 130), (800, 108), (838, 72), (850, 30), (852, 0)]
    # Der Mittelpunkt (122,0) und (852,0) doppeln sich beim Spiegeln, daher ohne die Endpunkte spiegeln
    body_pts = [(x, cy - w) for x, w in body_half[:-1]] + [(852, cy)] + [(x, cy + w) for x, w in reversed(body_half[1:-1])] + [(122, cy)]
    # Besser: erst oben von hinten nach vorn, dann unten von vorn nach hinten
    top = [(x, cy - w) for x, w in body_half[1:-1]]
    bot = [(x, cy + w) for x, w in reversed(body_half[1:-1])]
    outline = [(122, cy)] + top + [(852, cy)] + bot
    body = _catmull(outline)

    cab_half = [(300, 0), (306, 60), (340, 96), (440, 106), (540, 104), (606, 90), (628, 58), (632, 0)]
    cab_top = [(x, cy - w) for x, w in cab_half[1:-1]]
    cab_bot = [(x, cy + w) for x, w in reversed(cab_half[1:-1])]
    cabin = _catmull([(300, cy)] + cab_top + [(632, cy)] + cab_bot)

    roof_half = [(372, 0), (376, 46), (420, 74), (500, 76), (560, 70), (578, 44), (580, 0)]
    r_top = [(x, cy - w) for x, w in roof_half[1:-1]]
    r_bot = [(x, cy + w) for x, w in reversed(roof_half[1:-1])]
    roof = _catmull([(372, cy)] + r_top + [(580, cy)] + r_bot)

    def wheel(x, y):
        return f'<rect x="{x - 42}" y="{y - 19}" width="84" height="38" rx="9"/>'
    wheels = "".join(wheel(x, y) for x in (268, 676) for y in (cy - 150, cy + 150))
    # Türfugen, Motorhaube, Kofferraum
    lines = []
    for x in (432, 520):
        lines.append(f'M{x},{cy - 142}L{x},{cy - 100}M{x},{cy + 142}L{x},{cy + 100}')
    lines.append(f'M640,{cy - 120}Q650,{cy} 640,{cy + 120}')                      # Wasserkasten
    lines.append(f'M300,{cy - 112}Q290,{cy} 300,{cy + 112}')                      # Heckscheibe zur Klappe
    lines.append(f'M742,{cy - 70}Q760,{cy} 742,{cy + 70}')                        # Haubenkante
    # Scheinwerfer, Rückleuchten, Spiegel
    lights = (f'<path d="M814,{cy - 96}L842,{cy - 56}L812,{cy - 60}Z"/><path d="M814,{cy + 96}L842,{cy + 56}L812,{cy + 60}Z"/>'
              f'<path d="M132,{cy - 98}L128,{cy - 56}L152,{cy - 70}Z"/><path d="M132,{cy + 98}L128,{cy + 56}L152,{cy + 70}Z"/>')
    mirrors = f'<path d="M606,{cy - 148}L626,{cy - 168}L636,{cy - 160}L618,{cy - 144}Z"/><path d="M606,{cy + 148}L626,{cy + 168}L636,{cy + 160}L618,{cy + 144}Z"/>'

    # Schadenszone vorn rechts: schraffiertes Feld mit Randlinie
    dz = (f'M700,{cy + 132}C760,{cy + 134} 826,{cy + 104} 842,{cy + 60}L846,{cy + 14}L792,{cy + 22}L740,{cy + 70}Z')
    hatch = []
    for i in range(0, 15):
        x = 708 + i * 10
        hatch.append(f'M{x},{cy + 148}L{x + 52},{cy + 30}')
    # Maßlinie unten: Länge
    y_dim = height - 34
    dim = (f'M122,{y_dim}L852,{y_dim}M122,{y_dim - 9}L122,{y_dim + 9}M852,{y_dim - 9}L852,{y_dim + 9}'
           f'M122,{y_dim}L138,{y_dim - 5}M122,{y_dim}L138,{y_dim + 5}M852,{y_dim}L836,{y_dim - 5}M852,{y_dim}L836,{y_dim + 5}')
    # Mittellinie
    axis = f'M70,{cy}L912,{cy}'

    def marker(n, x, y, tx, ty):
        return (f'<path class="leader" d="M{x},{y}L{tx},{ty}"/><circle class="mk" cx="{tx}" cy="{ty}" r="15"/>'
                f'<text class="mk-n" x="{tx}" y="{ty + 6}" text-anchor="middle">{n}</text><circle class="dot" cx="{x}" cy="{y}" r="4"/>')
    marks = marker(1, 832, cy + 34, 900, cy + 80) + marker(2, 728, cy + 144, 770, cy + 192) + marker(3, 142, cy - 30, 84, cy - 96)

    aria = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    return f'''<svg class="plan" viewBox="0 0 {width} {height}" {aria} fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">
  <path class="axis" d="{axis}"/>
  <g class="wheels">{wheels}</g>
  <path class="body" d="{body}" pathLength="1"/>
  <path class="cabin" d="{cabin}" pathLength="1"/>
  <path class="roof" d="{roof}" pathLength="1"/>
  <path class="fine" d="{''.join(lines)}"/>
  <g class="fine">{lights}{mirrors}</g>
  <g class="damage"><path class="dz" d="{dz}"/><path class="hatch" d="{''.join(hatch)}" clip-path="url(#dzclip)"/></g>
  <clipPath id="dzclip"><path d="{dz}"/></clipPath>
  <path class="dim" d="{dim}"/>
  <text class="dim-t" x="{(122 + 852) / 2}" y="{y_dim - 10}" text-anchor="middle">4 620 mm</text>
  {marks}
</svg>'''


def stamp(size=220, top="UNABHÄNGIGER SACHVERSTÄNDIGER", bottom="CELLE · SEIT ÜBER 30 JAHREN", centre="PS", sub="KFZ"):
    """Runder Prüfstempel mit Text auf dem Kreis."""
    font = 'font-family="Barlow Condensed, Arial Narrow, sans-serif" font-weight="700" font-size="14.5" letter-spacing="1.6"'
    return f'''<svg class="stamp" viewBox="0 0 220 220" width="{size}" height="{size}" aria-hidden="true" fill="none" stroke="currentColor">
  <defs>
    <path id="st-top" d="M34,110 A76,76 0 0 1 186,110"/>
    <path id="st-bot" d="M24,110 A86,86 0 0 0 196,110"/>
  </defs>
  <circle cx="110" cy="110" r="105" stroke-width="4.5"/>
  <circle cx="110" cy="110" r="97" stroke-width="1.5"/>
  <circle cx="110" cy="110" r="64" stroke-width="1.5"/>
  <text {font} fill="currentColor" stroke="none"><textPath href="#st-top" startOffset="50%" text-anchor="middle">{top}</textPath></text>
  <text {font} fill="currentColor" stroke="none"><textPath href="#st-bot" startOffset="50%" text-anchor="middle">{bottom}</textPath></text>
  <text x="110" y="124" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif" font-weight="800" font-style="italic" font-size="52" fill="currentColor" stroke="none">{centre}</text>
  <text x="110" y="146" text-anchor="middle" font-family="Barlow Condensed, Arial Narrow, sans-serif" font-weight="700" font-size="13" letter-spacing="3" fill="currentColor" stroke="none">{sub}</text>
  <path d="M96,86h28" stroke-width="2.5"/>
  <path d="M16,110h6M198,110h6" stroke-width="3"/>
</svg>'''


def ruler(width=600, height=22, step=10, major=5):
    """Messskala mit langen und kurzen Strichen."""
    parts = []
    for i in range(0, width // step + 1):
        x = i * step
        h = height if i % major == 0 else height * 0.55
        parts.append(f"M{x},0L{x},{h}")
    return f'<svg class="ruler" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><path d="{"".join(parts)}"/></svg>'
