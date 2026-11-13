#!/usr/bin/env python3
"""Eigene Illustrationen im Strichstil der CI 3.0. Schreibt src/partials/ill-*.html. Das zugehörige CSS steht im Abschnitt 36 von static/assets/mx.css (Konstante CSS unten als Quelle)."""
import sys
import os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'partials') + os.sep

def up(cx, cy, w, sw=3.2):
    """Aufwärtslinie aus aufwaertslinie.svg (Pfade unverändert), mittig auf (cx, cy), Breite w."""
    s = w / 220.0
    tx = cx - 114 * s; ty = cy - 47 * s
    return ('<g transform="translate(%.1f %.1f) scale(%.4f)" fill="none" stroke="#045268" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M4.0016 83.9982C80 82.0015 150.0016 62.0015 221.9993 12.0013"/><path d="M193.9995 10.0005H223.9996V40.0006"/></g>') % (tx, ty, s, sw / s)

def wrap(name, body):
    return ('<svg class="ill mi mi--%s" viewBox="0 0 360 240" aria-hidden="true" focusable="false">\n'
            '  <rect class="s" width="360" height="240" rx="20"/>\n%s\n</svg>\n') % (name, body)

def bars(x, y, w, cls='bt'):
    return '<path class="%s" d="M%s %sH%s"/>' % (cls, x, y, x + w)

SC = {}

SC['web'] = '''  <circle class="h" cx="170" cy="124" r="104"/>
  <rect class="w" x="40" y="36" width="230" height="156" rx="12"/>
  <path class="l" d="M40 62H270"/>
  <circle class="t" cx="54" cy="49" r="3"/><circle class="t" cx="65" cy="49" r="3"/><circle class="t" cx="76" cy="49" r="3"/>
  <path class="bt" d="M58 86H160"/><path class="bt" d="M58 101H130"/><path class="k" d="M58 113H108"/>
  <path class="bm" d="M58 130H150"/><path class="bm" d="M58 141H128"/>
  <rect class="p" x="58" y="154" width="58" height="22" rx="4"/>
  <rect class="n" x="170" y="76" width="84" height="76" rx="8"/>
  <circle class="w" cx="196" cy="98" r="8"/>
  <path class="p" d="M174 150L204 120 222 138 234 128 252 150Z"/>
  <rect class="w" x="226" y="98" width="88" height="126" rx="15"/>
  <path class="l" d="M258 110H282"/>
  <path class="bt" d="M242 130H298"/><path class="bm" d="M242 142H284"/>
  <rect class="n" x="242" y="154" width="56" height="32" rx="6"/>
  <rect class="p" x="242" y="196" width="56" height="16" rx="4"/>'''

SC['seo'] = '''  <circle class="h" cx="176" cy="122" r="102"/>
  <rect class="p" x="38" y="38" width="204" height="50" rx="10"/>
  <circle class="w" cx="62" cy="63" r="11"/><path class="l" d="M56 67L62 58 68 67"/>
  <path class="pt" d="M84 54H210"/><path class="k" d="M84 65H128"/><path class="pm" d="M84 77H190"/>
  <rect class="w" x="38" y="100" width="204" height="42" rx="10"/>
  <path class="bt" d="M58 116H178"/><path class="bm" d="M58 129H150"/>
  <rect class="w" x="38" y="154" width="204" height="42" rx="10"/>
  <path class="bt" d="M58 170H160"/><path class="bm" d="M58 183H134"/>
  <circle class="n" cx="252" cy="146" r="38"/>
  <path class="hl2" d="M228 130A26 26 0 0 1 244 118"/>
  <path class="hd" d="M280 174L310 206"/>
  ''' + up(252, 148, 52, 3.0)

SC['local'] = '''  <circle class="h" cx="180" cy="124" r="102"/>
  <rect class="w" x="36" y="50" width="290" height="152" rx="14"/>
  <path class="rd" d="M44 124H318M132 56V196M238 56V196"/>
  <rect class="n" x="48" y="62" width="70" height="48" rx="6"/><rect class="n" x="146" y="62" width="78" height="48" rx="6"/><rect class="n" x="252" y="62" width="62" height="48" rx="6"/>
  <rect class="n" x="48" y="138" width="70" height="52" rx="6"/><rect class="n" x="252" y="138" width="62" height="52" rx="6"/>
  <rect class="w" x="148" y="156" width="76" height="38" rx="3"/>
  <path class="p" d="M142 156L152 138H220L230 156Z"/>
  <path class="pl" d="M162 138L160 156M178 138L178 156M194 138L196 156M210 138L212 156"/>
  <rect class="n" x="176" y="168" width="20" height="26" rx="3"/>
  <path class="w" d="M186 130C186 130 162 108 162 88A24 24 0 1 1 210 88C210 108 186 130 186 130Z"/>
  <path class="p" d="M186 130C186 130 162 108 162 88A24 24 0 1 1 210 88C210 108 186 130 186 130Z"/>
  <circle class="w" cx="186" cy="88" r="9"/>
  <rect class="w" x="226" y="76" width="82" height="36" rx="8"/>
  <path class="bt" d="M238 88H284"/><path class="k" d="M238 99H264"/>'''

SC['ki'] = '''  <circle class="h" cx="180" cy="124" r="102"/>
  <path class="w" d="M52 46H170A16 16 0 0 1 186 62V90A16 16 0 0 1 170 106H78L50 128 54 106H52A16 16 0 0 1 36 90V62A16 16 0 0 1 52 46Z"/>
  <path class="bt" d="M54 68H152"/><path class="bm" d="M54 83H120"/>
  <rect class="w" x="236" y="38" width="92" height="66" rx="10"/>
  <path class="l" d="M236 58H328"/><path class="l" d="M258 32V44M306 32V44"/>
  <circle class="n" cx="282" cy="82" r="13"/><path class="lp" d="M275 82L280 87 290 76"/>
  <path class="p" d="M166 122H312A16 16 0 0 1 328 138V166A16 16 0 0 1 312 182H300L312 206 276 182H166A16 16 0 0 1 150 166V138A16 16 0 0 1 166 122Z"/>
  <path class="pt" d="M168 142H290"/><path class="k" d="M168 154H214"/><path class="pm" d="M168 168H262"/>'''

SC['brand'] = '''  <circle class="h" cx="170" cy="124" r="100"/>
  <rect class="w" x="40" y="42" width="142" height="154" rx="14"/>
  <text class="aa" x="58" y="122">Aa</text>
  <path class="k" d="M58 134H116"/>
  <path class="bm" d="M58 152H156"/><path class="bm" d="M58 166H132"/>
  <circle class="t" cx="236" cy="62" r="23"/>
  <circle class="p" cx="284" cy="86" r="23"/>
  <circle class="n" cx="236" cy="110" r="23"/>
  <circle class="h2" cx="284" cy="134" r="23"/>
  <rect class="w" x="208" y="162" width="114" height="58" rx="8"/>
  <circle class="p" cx="228" cy="182" r="7"/>
  <path class="bt" d="M246 179H302"/><path class="bm" d="M246 192H284"/>'''

SC['care'] = '''  <circle class="h" cx="180" cy="122" r="102"/>
  <rect class="w" x="52" y="46" width="160" height="116" rx="12"/>
  <path class="l" d="M52 68H212"/>
  <circle class="t" cx="66" cy="57" r="3"/><circle class="t" cx="77" cy="57" r="3"/><circle class="t" cx="88" cy="57" r="3"/>
  <path class="bt" d="M70 90H160"/><path class="bm" d="M70 104H146"/><path class="bm" d="M70 116H156"/>
  <rect class="n" x="70" y="128" width="56" height="20" rx="4"/>
  <path class="p" d="M262 88L304 102V140C304 170 284 188 262 198 240 188 220 170 220 140V102Z"/>
  <path class="pl" d="M244 142L258 156 282 126"/>
  <path class="k" d="M236 214H288"/>
  <circle class="n" cx="84" cy="184" r="28"/>
  <path class="l" d="M70 180A15 15 0 0 1 96 174"/><path class="l" d="M97 165V175H87"/>
  <path class="l" d="M98 188A15 15 0 0 1 72 194"/><path class="l" d="M71 203V193H81"/>'''

SC['relaunch'] = '''  <circle class="h" cx="180" cy="122" r="102"/>
  <rect class="o" x="28" y="64" width="108" height="126" rx="10"/>
  <path class="bm" d="M42 84H112"/>
  <rect class="w" x="42" y="98" width="42" height="30" rx="3"/><rect class="w" x="90" y="108" width="30" height="22" rx="3"/>
  <path class="bm" d="M42 146H118"/><path class="bm" d="M42 158H92"/><path class="bm" d="M42 170H108"/>
  <path class="l4" d="M146 126H194M182 112L196 126 182 140"/>
  <rect class="w" x="206" y="40" width="126" height="154" rx="12"/>
  <path class="l" d="M206 62H332"/>
  <circle class="t" cx="220" cy="51" r="3"/><circle class="t" cx="231" cy="51" r="3"/><circle class="t" cx="242" cy="51" r="3"/>
  <path class="bt" d="M222 84H304"/><path class="bt" d="M222 98H272"/><path class="k" d="M222 109H260"/>
  <path class="bm" d="M222 124H300"/>
  <rect class="p" x="222" y="138" width="46" height="18" rx="4"/>
  <rect class="n" x="222" y="166" width="28" height="18" rx="4"/><rect class="n" x="256" y="166" width="28" height="18" rx="4"/><rect class="n" x="290" y="166" width="28" height="18" rx="4"/>'''

SC['system'] = '''  <circle class="h" cx="180" cy="124" r="106"/>
  <path class="l" d="M160 96L108 142M200 96L252 142M122 176H238"/>
  <circle class="p" cx="180" cy="66" r="36"/>
  <rect class="pl" x="161" y="53" width="38" height="28" rx="4"/><path class="pl" d="M161 62H199"/>
  <circle class="w" cx="84" cy="174" r="36"/>
  <path class="pin" d="M84 192C84 192 69 178 69 168A15 15 0 1 1 99 168C99 178 84 192 84 192Z"/>
  <circle class="w" cx="84" cy="168" r="5"/>
  <circle class="n" cx="276" cy="174" r="36"/>
  <path class="w" d="M258 160H294A6 6 0 0 1 300 166V180A6 6 0 0 1 294 186H278L268 196 268 186H258A6 6 0 0 1 252 180V166A6 6 0 0 1 258 160Z"/>
  <circle class="t" cx="134" cy="119" r="4.5"/><circle class="t" cx="226" cy="119" r="4.5"/><circle class="t" cx="180" cy="176" r="4.5"/>
  <path class="k" d="M150 224H210"/>
  ''' + up(300, 52, 64, 3.0)

SC['handwerk'] = '''  <circle class="h" cx="190" cy="124" r="102"/>
  <rect class="w" x="46" y="34" width="100" height="168" rx="16"/>
  <path class="l" d="M82 48H110"/>
  <rect class="n" x="60" y="68" width="72" height="42" rx="6"/>
  <path class="bt" d="M70 82H112"/><path class="bm" d="M70 91H104"/><path class="k" d="M70 101H92"/>
  <rect class="w" x="60" y="118" width="72" height="30" rx="6"/>
  <path class="bm" d="M70 130H112"/><path class="bm" d="M70 139H98"/>
  <rect class="p" x="60" y="160" width="72" height="26" rx="5"/><path class="pt" d="M80 173H112"/>
  <g transform="rotate(34 244 134)">
    <rect class="n" x="238" y="82" width="12" height="108" rx="5"/>
    <circle class="n" cx="244" cy="74" r="20"/><circle class="h2" cx="244" cy="74" r="8"/>
  </g>
  <g transform="rotate(-34 244 134)">
    <rect class="w" x="238" y="76" width="12" height="118" rx="5"/>
    <rect class="p" x="214" y="52" width="60" height="28" rx="5"/>
  </g>'''

SC['praxis'] = '''  <circle class="h" cx="184" cy="124" r="102"/>
  <rect class="w" x="84" y="44" width="132" height="158" rx="12"/>
  <rect class="p" x="125" y="34" width="50" height="22" rx="6"/>
  <circle class="n" cx="150" cy="96" r="22"/>
  <path class="lp6" d="M150 85V107M139 96H161"/>
  <path class="bt" d="M104 140H194"/><path class="k" d="M104 150H134"/><path class="bm" d="M104 164H172"/><path class="bm" d="M104 176H150"/>
  <rect class="w" x="226" y="100" width="102" height="86" rx="10"/>
  <path class="l" d="M226 122H328"/><path class="l" d="M248 94V106M306 94V106"/>
  <circle class="t" cx="244" cy="138" r="3"/><circle class="t" cx="266" cy="138" r="3"/><circle class="t" cx="288" cy="138" r="3"/><circle class="t" cx="310" cy="138" r="3"/>
  <circle class="t" cx="244" cy="158" r="3"/><circle class="p" cx="266" cy="158" r="10"/><circle class="t" cx="288" cy="158" r="3"/><circle class="t" cx="310" cy="158" r="3"/>
  <path class="pl" d="M261 158L265 162 272 154"/>
  <path class="p" d="M30 206H62L58 228H34Z"/>
  <path class="n" d="M46 206C26 198 26 170 46 160 66 170 66 198 46 206Z"/><path class="l" d="M46 206V176"/>'''

SC['gastro'] = '''  <circle class="h" cx="172" cy="124" r="102"/>
  <path class="l" d="M52 78V104A10 10 0 0 0 72 104V78M62 78V200"/>
  <circle class="w" cx="154" cy="124" r="66"/>
  <circle class="n" cx="154" cy="124" r="44"/>
  <circle class="p" cx="140" cy="116" r="15"/>
  <path class="w" d="M158 140C158 120 176 110 190 112 192 130 178 144 158 140Z"/>
  <path class="l" d="M158 140L176 124"/>
  <path class="k" d="M118 210H190"/>
  <path class="w" d="M240 76C260 84 260 124 240 134Z"/><path class="l" d="M240 134V200"/>
  <rect class="w" x="270" y="82" width="58" height="88" rx="8"/>
  <path class="bt" d="M282 100H316"/><path class="k" d="M282 110H300"/><path class="bm" d="M282 124H316"/><path class="bm" d="M282 136H306"/><circle class="p" cx="292" cy="154" r="6"/>'''

CSS = '''
/* 36 · Eigene Illustrationen im Strichstil (Markenhandbuch 3.0): Tiefsee-Linie, Pfauenblau, genau ein Kupferstrich je Motiv */
.ill.mi .s{fill:#F7F4EE}
.ill.mi .h{fill:#EAE2D3}
.ill.mi .h2{fill:#EAE2D3;stroke:#0C2128;stroke-width:3}
.ill.mi .w,.ill.mi .n,.ill.mi .p,.ill.mi .o,.ill.mi .t{stroke:#0C2128;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}
.ill.mi .w{fill:#FFFFFF}
.ill.mi .n{fill:#E1F0F6}
.ill.mi .p{fill:#045268}
.ill.mi .o{fill:#EAE2D3;stroke-dasharray:6 6}
.ill.mi .t{fill:#0C2128;stroke:none}
.ill.mi .l,.ill.mi .l4{fill:none;stroke:#0C2128;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.ill.mi .l4{stroke-width:4}
.ill.mi .lp{fill:none;stroke:#045268;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
.ill.mi .lp6{fill:none;stroke:#045268;stroke-width:7;stroke-linecap:round}
.ill.mi .pl{fill:none;stroke:#FFFFFF;stroke-width:3.5;stroke-linecap:round;stroke-linejoin:round}
.ill.mi .pin{fill:#045268;stroke:#0C2128;stroke-width:3;stroke-linejoin:round}
.ill.mi .bt{fill:none;stroke:#0C2128;stroke-width:6;stroke-linecap:round}
.ill.mi .bm{fill:none;stroke:#4E5C5F;stroke-opacity:.45;stroke-width:4;stroke-linecap:round}
.ill.mi .pt{fill:none;stroke:#FFFFFF;stroke-width:6;stroke-linecap:round}
.ill.mi .pm{fill:none;stroke:#FFFFFF;stroke-opacity:.6;stroke-width:4;stroke-linecap:round}
.ill.mi .k{fill:none;stroke:#C67432;stroke-width:5;stroke-linecap:butt}
.ill.mi .rd{fill:none;stroke:#EAE2D3;stroke-width:10;stroke-linecap:butt}
.ill.mi .hd{fill:none;stroke:#0C2128;stroke-width:10;stroke-linecap:round}
.ill.mi .hl2{fill:none;stroke:#FFFFFF;stroke-width:4;stroke-linecap:round}
.ill.mi .aa{font:800 54px 'Archivo','Arial Black',Arial,sans-serif;fill:#0C2128}
'''

if __name__ == '__main__':
    import json
    for k, v in SC.items():
        open(R + 'ill-%s.html' % k, 'w', encoding='utf-8').write(wrap(k, v.replace(' style="display:none"', '')))
    print('ok', len(SC))
