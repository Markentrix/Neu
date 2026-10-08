"""Brand-Layer: Endcard, Hook-Plate und Karten als PNG aus HTML (CI-Farben,
Space Grotesk / Inter aus assets/fonts), gerendert mit Playwright/Chromium.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

CI = {
    "soft_white": "#F8FAFC", "white": "#FFFFFF", "navy": "#0B1020", "black": "#05070B",
    "cyan": "#28C7F7", "blue": "#1E9BFF", "violet": "#8B5CF6", "cool_gray": "#B8C0CC",
    "muted_gray": "#667085", "cyan_text": "#0E8FC4",
}
REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "assets" / "fonts"


def _font_face() -> str:
    def face(fam, weight, file):
        p = FONTS / file
        if not p.exists():
            return ""
        b64 = base64.b64encode(p.read_bytes()).decode()
        return (f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "".join([
        face("Space Grotesk", 700, "space-grotesk-latin-700-normal.woff2"),
        face("Space Grotesk", 600, "space-grotesk-latin-600-normal.woff2"),
        face("Inter", 400, "inter-latin-400-normal.woff2"),
        face("Inter", 500, "inter-latin-500-normal.woff2"),
    ])


def _img_data_uri(path: Optional[str | Path]) -> Optional[str]:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    mime = "image/svg+xml" if p.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def render_html(html: str, out_path: str | Path, width: int, height: int,
                transparent: bool = False) -> Path:
    from playwright.sync_api import sync_playwright
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        kwargs = {}
        exe = "/opt/pw-browsers/chromium"
        if os.path.exists(exe):
            kwargs["executable_path"] = exe
        try:
            browser = pw.chromium.launch(**kwargs)
        except Exception:
            browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(200)
        page.screenshot(path=str(out), omit_background=transparent, full_page=False)
        browser.close()
    return out


def endcard(out_path: str | Path, logo_path: Optional[str | Path] = None,
            headline: str = "Mehr Anfragen. Weniger Aufwand.",
            subline: str = "KI-Automatisierung & Social-Media-Werbung für lokale Unternehmen.",
            cta: str = "Marketing-Check anfragen →", url: str = "markentrix.de",
            ai_note: str = "KI-generiert · Anzeige") -> Path:
    """Endcard 1080x1920, Light-Theme, Safe Area oben 240 px / unten 330 px."""
    logo = _img_data_uri(logo_path)
    logo_html = (f'<img class="logo" src="{logo}" alt="">' if logo
                 else '<div class="logo-missing">Logo fehlt: assets/markentrix-logo-light.svg</div>')
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_face()}
html,body{{margin:0;width:1080px;height:1920px;background:{CI['soft_white']};}}
.wrap{{position:absolute;left:0;right:0;top:240px;bottom:330px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;padding:0 96px;text-align:center;}}
.logo{{width:420px;height:auto;margin-bottom:88px;}}
.logo-missing{{font:500 28px Inter;color:{CI['muted_gray']};border:1px dashed {CI['cool_gray']};padding:24px 32px;margin-bottom:88px;}}
h1{{font:700 92px/1.08 'Space Grotesk';color:{CI['navy']};margin:0 0 36px;letter-spacing:-0.01em;}}
p{{font:400 40px/1.35 Inter;color:{CI['muted_gray']};margin:0 0 96px;max-width:860px;}}
.cta{{font:600 44px 'Space Grotesk';color:#fff;background:linear-gradient(90deg,{CI['cyan']},{CI['blue']});
  border-radius:999px;padding:34px 72px;}}
.url{{font:500 36px Inter;color:{CI['navy']};margin-top:72px;}}
.curve{{position:absolute;left:96px;right:96px;bottom:360px;height:140px;}}
.note{{position:absolute;left:0;right:0;bottom:270px;text-align:center;font:400 26px Inter;color:{CI['muted_gray']};}}
</style></head><body>
<svg class="curve" viewBox="0 0 888 140" preserveAspectRatio="none"><defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{CI['cyan']}"/><stop offset="1" stop-color="{CI['blue']}"/></linearGradient></defs>
<path d="M0 130 C 250 125, 500 95, 888 10" fill="none" stroke="url(#g)" stroke-width="8" stroke-linecap="round"/></svg>
<div class="wrap">{logo_html}<h1>{headline}</h1><p>{subline}</p><div class="cta">{cta}</div><div class="url">{url}</div></div>
<div class="note">{ai_note}</div>
</body></html>"""
    return render_html(html, out_path, 1080, 1920)


def hook_plate(text: str, out_path: str | Path, width: int = 1080) -> Path:
    """Hook-Plate: Space Grotesk Bold, Navy auf hellem Band, max. 2 Zeilen, transparent."""
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_face()}
html,body{{margin:0;width:{width}px;height:{round(width*0.37)}px;background:transparent;}}
.band{{position:absolute;left:{round(width*0.055)}px;right:{round(width*0.055)}px;top:{round(width*0.02)}px;background:rgba(255,255,255,0.96);
  border:1px solid {CI['cool_gray']};border-radius:{round(width*0.026)}px;padding:{round(width*0.037)}px {round(width*0.044)}px;text-align:center;}}
.band div{{font:700 {round(width*0.059)}px/1.15 'Space Grotesk';color:{CI['navy']};}}
</style></head><body><div class="band"><div>{text}</div></div></body></html>"""
    return render_html(html, out_path, width, round(width * 0.37), transparent=True)
