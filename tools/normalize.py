# -*- coding: utf-8 -*-
"""catalog_raw.json (extract.py) -> src/catalog.json: Produkte, Kategorien, Fahrzeug-Zuordnung.
Aufruf: python3 tools/normalize.py <crawl_dir>"""
import re, sys, json, unicodedata, urllib.parse, collections
d = sys.argv[1]
raw = json.load(open(f"{d}/catalog_raw.json"))
pages = collections.OrderedDict()
for b in raw: pages.setdefault(b["url"], []).append(b)

def fold(s):
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")

FIX = {"Varaibel": "Variabel", "Livign": "Living", "Wohnmpbil": "Wohnmobil", "Anhägernkupplung": "Anhängerkupplung", "Anhägerkupplung": "Anhängerkupplung"}
def clean(t):
    for a, b in FIX.items(): t = t.replace(a, b)
    return " ".join(t.replace("­", "").split())

MONT = re.compile(r"^(Professionelle )?(Montage|Einbau)", re.I)
EXTRA_PRICE = 0.2  # Optionen < 20 % des Hauptpreises = Zubehör, zählen nicht für "ab"-Preis

def category(name, url):
    n = name.lower(); u = urllib.parse.unquote(url).lower()
    if "/ersatzteile" in u: return "ersatzteile"
    if n.startswith("rasterplatte"): return "rasterplatten"
    if n.startswith("rahmenverl"): return "rahmenverlaengerung"
    if re.match(r"(universal |13-poliger |\d+-poliger )?elektro(kabel)?satz|elektrokabelsatz|13-poliger|universal elektrosatz", n): return "elektrosaetze"
    if "elektrokabelsatz" in u and not n.startswith(("anhängerkupplung", "rahmenverl")): return "elektrosaetze"
    if "fahrzeugspezifische" in u or n.startswith(("anhängerkupplung", "ahk")): return "anhaengerkupplung"
    if re.search(r"motorradträger|alu-plattform|fahrradträger|e-bike-fahrrad|bike max|leuchtenträger", n): return "hecktraeger"
    if re.search(r"motorradanhänger|alu-star", n): return "motorradanhaenger"
    if re.search(r"luftf|e-suspension|dunlop", n): return "luftfederung"
    if "kompressor" in n: return "luftfederung"
    if re.search(r"hydraulik|autolift|alu-matic|thule|flat-jack|hubstütz", n): return "stuetzensysteme"
    if re.search(r"dometic|klima", n): return "klimaanlagen"
    if "robot trolley" in n: return "rangierhilfe"
    if re.search(r"trittstufe|freistufe", n): return "trittstufen"
    if re.search(r"garagenhalterung|standschiene|auffahr", n): return "garagenhalterung"
    if re.search(r"gaswarner|3gas|thermomatte|matratze|multianker|bike lift|markise", n): return "zubehoer"
    if "bike-max" in u or "bike lift" in n: return "zubehoer"
    m = re.search(r"/(luftfederung|hecktr|stuetzen|st%c3%bctzen)", url.lower())
    return "zubehoer"

# ---- Fahrzeug-Zuordnung ----
BASES = {
 "fiat-ducato": ("Fiat Ducato", "sevel"), "citroen-jumper": ("Citroën Jumper", "sevel"), "peugeot-boxer": ("Peugeot Boxer", "sevel"),
 "mercedes-sprinter": ("Mercedes-Benz Sprinter", "sprinter"), "ford-transit": ("Ford Transit", "transit"),
 "renault-master": ("Renault Master / Opel Movano / Nissan Interstar", "master"), "iveco-daily": ("Iveco Daily", "daily"),
 "vw-crafter": ("VW Crafter / LT / MAN TGE", "crafter")}
SERIES = {
 "sevel": [("zfa280", "ZFA 280/290 · bis 1994"), ("z230", "Typ 230 · 1994–2002"), ("z244", "Typ 244 · 2002–2006"), ("z250", "Typ 250 / X290 · ab 2006")],
 "sprinter": [("t1n", "T1N (W901–W905) · 1995–2006"), ("ncv3", "NCV3 (W906) · 2006–2018"), ("vs30", "VS30 (W907/W910) · ab 2018")],
 "transit": [("t-alt", "FT150 / bis 2000 · 1986–2000"), ("t-v185", "V184/V185 · 2000–2012"), ("t-v362", "Custom V362 · ab 2012"), ("t-v363", "V363 · ab 2014")],
 "master": [("x70", "X70 · 1998–2010"), ("x62", "X62 · ab 2010")],
 "daily": [("d-alt", "Daily bis 2006"), ("d-neu", "Daily ab 2006")],
 "crafter": [("c-all", "Crafter / LT / MAN TGE")]}

def makes_of(t):
    m = []
    if re.search(r"ducato|zfa2|fiat", t): m.append("fiat-ducato")
    if re.search(r"jumper|citro", t): m.append("citroen-jumper")
    if re.search(r"boxer|peugeot", t): m.append("peugeot-boxer")
    if re.search(r"ducato.{0,14}(jumper|boxer)|fiat.{0,6}peugeot.{0,6}citro|sevel", t) or (not m and re.search(r"zfa ?2", t)): m = ["fiat-ducato", "citroen-jumper", "peugeot-boxer"]
    if re.search(r"sprinter", t): m.append("mercedes-sprinter")
    if re.search(r"transit", t): m.append("ford-transit")
    if re.search(r"master|movano|interstar", t): m.append("renault-master")
    if re.search(r"daily|iveco", t): m.append("iveco-daily")
    if re.search(r"crafter|man tge|\btge\b|vw lt", t): m.append("vw-crafter")
    return list(dict.fromkeys(m))

def series_of(group, t):
    t = re.sub(r"\s+", " ", re.sub(r"[-.,/–()]", " ", t))
    s = []
    if group == "sevel":
        if re.search(r"zfa ?280|280 ?/ ?290|\b280\b|1982|bis 1994|1994 bis 1982", t): s.append("zfa280")
        if re.search(r"zfa ?230|typ 230|\b230\b|2001 bis 1994|bj 1994 bis 2001|1994 bis 2001|1996", t): s.append("z230")
        if re.search(r"zfa ?244|typ 244|\b244\b|2006 bis 2001|2001 bis 2006|2002", t): s.append("z244")
        if re.search(r"zfa ?250|x ?250|typ 250|\b250\b|x ?290|ab 0?6 ?2006|2006 bis aktuel|ab bj 2006|ab 2006|02 2011|2011|can bus", t): s.append("z250")
    elif group == "sprinter":
        if re.search(r"t1n|1995|3er|4er|w90[1-5]|bis 2006", t): s.append("t1n")
        if re.search(r"ncv3?|ab bj 2007|ab baujahr 2007|ab 2007|2006|w906|2018 bis", t): s.append("ncv3")
        if re.search(r"vs30|ab baujahr 2018|ab bj 2018|ab 2018|w907|w910|wdb907|500", t): s.append("vs30")
    elif group == "transit":
        if re.search(r"1986|ft150|bis 2000|2000 bis 1986", t): s.append("t-alt")
        if re.search(r"v185|v184|ft350|ab bj 2000|ab baujahr 2000|2000 bis 2012|2000 bis 11 2012|ab 2000|2000 bis", t): s.append("t-v185")
        if re.search(r"v362|custom|ab baujahr 2012|ab bj 2012", t): s.append("t-v362")
        if re.search(r"v363|ab bj 2014|ab baujahr 2014|ab 2014|ab 2021|2021", t): s.append("t-v363")
    elif group == "master":
        if re.search(r"x70|1998|bis 05 2010|bis 2010|bis bj 05 2010|05 10|bis 05 2010", t): s.append("x70")
        if re.search(r"x62|ab bj 0?6 2010|ab 06 2010|ab 2010|ab baujahr 2010|master iii|ab 06 10|06 10", t): s.append("x62")
    elif group == "daily":
        if re.search(r"bis bj 2006|bis 2006|1999|bis baujahr 2006", t): s.append("d-alt")
        if re.search(r"ab bj 2006|ab 2006|ab baujahr 2006", t): s.append("d-neu")
    elif group == "crafter":
        s.append("c-all")
    return s

COACH = ["Bürstner", "Weinsberg", "T.E.C.", "Challenger", "Chausson", "Forster", "Dethleffs", "Giottiline", "Giotti", "Rimor", "Roller Team", "Elnagh", "Frankia",
         "Hobby", "Miller", "Rapido", "Sun Living", "Sun Livign", "Eura Mobil", "Laika", "Hymer", "Blu Camp", "Carthago", "Knaus", "McLouis", "Mobilvetta", "Pilote",
         "Joint", "Karmann", "Eifelland", "Fleurette", "CI", "Cristall", "Dream", "Esterel", "Nexxo", "Adria", "Malibu", "Sunlight", "Benimar", "LMC", "Niesmann", "Pössl", "Globecar"]
def coach_of(name, url):
    u = urllib.parse.unquote(url)
    if "fahrzeugspezifische" not in u: return None
    n = re.sub(r"^Anhängerkupplung( Wohnmobil)?\s+", "", clean(name))
    for c in sorted(COACH, key=len, reverse=True):
        if n.lower().startswith(c.lower()):
            c2 = {"Giotti": "Giottiline", "Sun Livign": "Sun Living", "CI": "CI Mizar" if n.lower().startswith("ci mizar") else "CI"}.get(c, c)
            if c == "Nexxo": return ("Bürstner", n)
            return (c2, n[len(c):].strip(" -") or n)
    return ("Weitere Hersteller", n)

def specs_of(body):
    sp = []
    for tag, t in body:
        m = re.match(r"^([A-ZÄÖÜ][\wäöüß\.\- /\(\)]{2,34}?)\s*:\s*(.{1,80})$", t)
        if m and len(sp) < 14: sp.append([m.group(1).strip(), m.group(2).strip()])
    return sp

products = []; used = set(); parts = []
for url, blocks in pages.items():
    up = urllib.parse.unquote(url)
    nb = [b for b in blocks if not MONT.match(b["name"])]
    mont = [b for b in blocks if MONT.match(b["name"])]
    if not nb: continue
    if "/ersatzteile/" in up:
        for b in nb:
            parts.append({"name": clean(b["name"]), "price": b["price"], "img": b["images"][:1], "url": url})
        continue
    p0 = nb[0]; name = clean(p0["name"])
    base = fold(up.rstrip("/").split("/")[-1])[:72] or fold(name)[:72]
    slug = base; k = 2
    while slug in used: slug = f"{base}-{k}"; k += 1
    used.add(slug)
    cat = category(name, url)
    t = name.lower()
    coach = coach_of(name, url)
    makes = [] if coach else makes_of(t)
    groups = list(dict.fromkeys(BASES[m][1] for m in makes))
    series = []
    for g in groups: series += series_of(g, t)
    series = list(dict.fromkeys(series))
    opts = []
    for b in nb[1:]:
        if b["price"] is not None: opts.append({"name": clean(b["name"]), "price": b["price"], "extra": bool(p0["price"] and b["price"] < p0["price"] * EXTRA_PRICE)})
    variants = [{"t": clean(re.sub(r"\s*[\d\.]+,\d{2} €\s*$", "", v["t"])), "p": v["p"]} for v in p0["variants"] if v["p"] is not None]
    prices = [p0["price"]] + [v["p"] for v in variants] + [o["price"] for o in opts if not o["extra"]]
    prices = [x for x in prices if x]
    low = min(prices) if prices else None
    body = [[a, clean(b)] for a, b in p0["body"] if not re.match(r"^(Montagekosten|Montage)$", b)]
    products.append({
        "slug": slug, "name": name, "cat": cat, "src": url, "price": p0["price"], "low": low, "from": bool(low and p0["price"] and (low != max(prices))) or bool(variants and len({v["p"] for v in variants}) > 1),
        "old": p0["old"], "variants": variants, "options": opts,
        "montage": [{"name": clean(m["name"]), "price": m["price"], "variants": [{"t": re.sub(r"\s*[\d\.]+,\d{2} €\s*$", "", clean(v["t"])), "p": v["p"] or m["price"]} for v in m["variants"]]} for m in mont if m["price"]],
        "images": p0["images"][:4] + [i for b in nb[1:3] for i in b["images"][:1] if i not in p0["images"][:4]], "weight": p0["weight"], "delivery": p0["delivery"],
        "docs": p0.get("docs", []), "title": clean(re.sub(r"\s*[-–|]\s*Italia Camper 24\s*$", "", p0["title"])), "meta": clean(p0["meta"]), "body": body[:60], "specs": specs_of(body),
        "makes": makes, "series": series, "coach": list(coach) if coach else None})
cats = collections.Counter(p["cat"] for p in products)
print(len(products), "Produkte;", len(parts), "Ersatzteile"); print(cats)
print("Fahrzeug-markiert:", sum(1 for p in products if p["makes"]), "| Coach:", sum(1 for p in products if p["coach"]))
print("mit Marke aber ohne Baureihe:", sum(1 for p in products if p["makes"] and not p["series"]))
json.dump({"products": products, "parts": parts}, open("/home/user/Neu/src/catalog.json", "w"), ensure_ascii=False, indent=0)
