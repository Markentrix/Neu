# -*- coding: utf-8 -*-
"""Liest die gecrawlten Seiten von italiacamper24.de aus (Preise, Bilder, Texte) -> catalog_raw.json
Aufruf: python3 tools/extract.py <crawl_dir>   (crawl_dir enthält fetch.log + pages/*.html)"""
import re, sys, json, html, urllib.parse
from bs4 import BeautifulSoup
d = sys.argv[1]
log = [l.split() for l in open(f"{d}/fetch.log") if l.strip().endswith(" 200")]
def eur(t):
    m = re.search(r"([\d\.]+,\d{2})", t or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None
def imgid(u):
    m = re.search(r"/image/(i[0-9a-f]+)/version/(\d+)/image\.(\w+)", u or "")
    return f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else None
NOISE = re.compile(r"Versandkostenfrei in folgende|Mehr anzeigen|^Italia Camper 24$|^Tel\.|E-Mail:|Hinweis: Bitte|Das ganze Jahr|für Sie erreichbar|Home Kontakte|Rund um die Uhr|Schillerstr|Wellingholzhausen|Öffnungzeit|^inkl\. MwSt|Cookie|Adobe Acrobat|^\d+(\.\d+)? ?KB$|^Download$|^\d[\d\.]*,\d{2} €$|In den Warenkorb", re.I)
out = []
for f, u, _ in log:
    s = open(f"{d}/pages/{f}.html", encoding="utf-8", errors="ignore").read()
    if "In den Warenkorb" not in s: continue
    soup = BeautifulSoup(s, "lxml")
    title = (soup.title.string or "").strip() if soup.title else ""
    md = soup.find("meta", attrs={"name": "description"})
    import copy
    ca = copy.copy(soup.select_one("#content_area"))
    body = []
    if ca:
        for t in ca.select("script,style,noscript,form,button,select,option,svg"): t.decompose()
        for el in ca.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "dt", "dd"]):
            if el.find_parent("div", class_="j-product"): continue
            if el.find(["h1","h2","h3","h4","p","li"]): continue
            t = " ".join(el.get_text(" ", strip=True).split())
            if len(t) < 3 or NOISE.search(t): continue
            body.append([el.name, t])
        seen = set(); body2 = []
        for k in body:
            if k[1] in seen: continue
            seen.add(k[1]); body2.append(k)
        body = body2[:150]
    for pm in soup.select("div.j-product"):
        pr = pm.select_one("[itemprop=price]")
        price = float(pr["content"]) if pr and pr.get("content") else eur(pr.get_text() if pr else "")
        old = pm.select_one(".cc-shop-old-price-value"); oldp = eur(old.get_text()) if old else None
        if oldp == 0: oldp = None
        # Name: erste Überschrift vor dem Produkt, sonst alt des Hauptbilds
        h = pm.find_previous(["h1", "h2", "h3"])
        mi = pm.select_one("img.cc-shop-product-main-image")
        name = (pm.select_one("[itemprop=name]").get_text(" ", strip=True) if pm.select_one("[itemprop=name]") else None) or (h.get_text(" ", strip=True) if h else None) or (mi.get("alt") if mi else None) or title
        imgs = []
        for a in pm.select("a.cc-shop-product-thumbnail,a.cc-product-superzoom"):
            i = imgid(a.get("data-href") or a.get("href"))
            if i and i not in imgs: imgs.append(i)
        if not imgs and mi:
            i = imgid(mi.get("src"))
            if i: imgs.append(i)
        variants = []
        for o in pm.select("select option"):
            t = " ".join(o.get_text(" ", strip=True).split())
            if t: variants.append({"t": t, "p": eur(t)})
        w = pm.select_one(".j-product-weight"); dl = pm.select_one(".j-product-delivery-time")
        desc = []
        out.append({"url": u, "title": title, "body": body, "meta": md["content"] if md and md.get("content") else "", "name": name, "price": price,
                    "old": oldp, "variants": variants, "images": imgs, "weight": w.get_text(strip=True) if w else "",
                    "delivery": " ".join(dl.get_text().split()) if dl else "", "desc": desc})
json.dump(out, open(f"{d}/catalog_raw.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "Produktblöcke auf", len({o['url'] for o in out}), "Seiten")
