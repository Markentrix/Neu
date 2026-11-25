# -*- coding: utf-8 -*-
"""Gezeichnete Bildelemente der Website als SVG: das Fahrzeug von der Seite mit Schadenszone und Bremsspur
und eine Messskala. Alles wird im Code erzeugt, ohne Bilddateien. Farben kommen aus CSS-Variablen
(Klassen `v-*`), damit Hell- und Dunkelmodus funktionieren.
"""

import math

VIEW_W, VIEW_H = 1200, 450

# Ankerpunkte der Beschriftungen (x, y im Koordinatensystem der Zeichnung):
# Linie läuft vom Anker am Fahrzeug zum Rand der Beschriftung. 'top' = Beschriftung oben, 'bottom' = unten.
ANCHORS = {
    "leasingruecknahme": {"x": 262, "from": 310, "to": 100, "side": "top"},
    "wertgutachten": {"x": 590, "from": 147, "to": 100, "side": "top"},
    "haftpflicht": {"x": 962, "from": 231, "to": 100, "side": "top", "damage": True},
    "unfallanalytisch": {"x": 170, "from": 364, "to": 398, "side": "bottom"},
    "beweissicherung": {"x": 598, "from": 336, "to": 398, "side": "bottom"},
    "restwert": {"x": 960, "from": 338, "to": 398, "side": "bottom", "damage": True},
}

BODY = ("M266,334 L262,298 C262,278 266,268 282,264 L352,247 C382,238 412,208 452,172 "
        "C472,154 492,147 522,147 L668,147 C700,147 724,158 748,180 L808,232 L880,242 L902,234 "
        "L916,250 L942,256 L930,272 L958,286 L938,302 L960,318 L938,336 "
        "L921,336 A68,68 0 1 0 799,336 L481,336 A68,68 0 1 0 359,336 L266,334 Z")
GHOST_FRONT = "M880,242 L968,252 C1000,256 1016,268 1022,290 L1028,322 C1029,332 1022,336 1012,336 L938,336"


def _wheel(cx, cy=306):
    spokes = "".join(
        f'<line x1="{cx}" y1="{cy}" x2="{cx + 35 * math.cos(a):.1f}" y2="{cy + 35 * math.sin(a):.1f}"/>'
        for a in [i * 2 * math.pi / 10 - math.pi / 2 for i in range(10)])
    return (f'<circle class="v-tyre" cx="{cx}" cy="{cy}" r="54"/>'
            f'<circle class="v-rim" cx="{cx}" cy="{cy}" r="36"/>'
            f'<g class="v-spoke">{spokes}</g>'
            f'<circle class="v-disc" cx="{cx}" cy="{cy}" r="15"/>'
            f'<circle class="v-hub" cx="{cx}" cy="{cy}" r="5"/>')


def car_side(label=""):
    """Pkw von der Seite, Front rechts: Bremsspur links, verformte Front mit roter Schadenszone und rotem Kreis."""
    leaders = []
    for a in ANCHORS.values():
        cls = "v-lead v-lead--dmg" if a.get("damage") else "v-lead"
        leaders.append(f'<line class="{cls}" x1="{a["x"]}" y1="{a["from"]}" x2="{a["x"]}" y2="{a["to"]}"/>'
                       f'<circle class="v-dot{" v-dot--dmg" if a.get("damage") else ""}" cx="{a["x"]}" cy="{a["from"]}" r="5"/>')
    return f'''<svg class="vehicle-svg" viewBox="0 0 {VIEW_W} {VIEW_H}" role="img" aria-label="{label}" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" class="v-hatch"/></pattern>
    <clipPath id="body-clip"><path d="{BODY}"/></clipPath>
  </defs>
  <line class="v-ground" x1="30" y1="360" x2="1170" y2="360"/>
  <rect class="v-skid" x="40" y="360" width="150" height="6"/>
  <rect class="v-skid" x="204" y="360" width="90" height="6"/>
  <rect class="v-skid" x="308" y="360" width="30" height="6"/>
  <g class="v-ghost"><path d="{GHOST_FRONT}"/></g>
  <path class="v-body" d="{BODY}"/>
  <g clip-path="url(#body-clip)"><rect class="v-hatch-area" x="876" y="226" width="120" height="120" fill="url(#hatch)"/></g>
  <g class="v-detail">
    <path class="v-glass" d="M396,228 L462,178 C474,167 486,162 500,162 L584,162 L584,228 Z"/>
    <path class="v-glass" d="M606,228 L606,162 L672,162 C688,162 700,168 712,178 L772,228 Z"/>
    <path d="M352,247 L806,232" class="v-belt"/>
    <path d="M470,232 C474,270 474,306 470,336"/><path d="M598,228 L598,336"/><path d="M742,236 C746,270 746,306 742,336"/>
    <rect class="v-handle" x="540" y="244" width="30" height="6" rx="3"/><rect class="v-handle" x="690" y="244" width="30" height="6" rx="3"/>
    <path class="v-glass" d="M782,222 L806,228 L800,238 L778,232 Z"/>
    <path class="v-lamp" d="M264,282 L286,277 L286,300 L264,303 Z"/>
    <path class="v-lamp" d="M912,254 L934,252 L930,268 L908,268 Z"/>
  </g>
  {_wheel(420)}{_wheel(860)}
  <path class="v-ring" d="M884,262 C898,222 986,216 1010,268 C1028,314 986,350 936,348 C890,346 868,312 876,276 C880,258 894,244 916,236"/>
  {"".join(leaders)}
</svg>'''


def ruler(height=440, major=50):
    """Senkrechte Messskala (Zentimeter-Raster) am Rand eines Fotos."""
    ticks = []
    y = 0
    while y <= height:
        long = (y // 10) % (major // 10) == 0
        ticks.append(f'<line x1="{0}" y1="{y}" x2="{22 if long else 12}" y2="{y}"/>')
        y += 10
    return (f'<svg class="ruler" viewBox="0 0 24 {height}" width="24" height="{height}" aria-hidden="true" focusable="false" '
            f'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">{"".join(ticks)}</svg>')
