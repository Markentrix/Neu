"""DNS-Assistent beim Livegang: zeigt, wohin eine Kunden-Domain heute zeigt, was zu ändern ist, und liefert den Text für den Kunden."""
import ipaddress
import json
import logging

from . import config, einstellungen

log = logging.getLogger("domaincheck")

# Bekannte Anbieter an ihren Adressen (Präfixe) und Nameservern (Teilstrings). Nur zur Anzeige, nie für Entscheidungen.
ANBIETER_IP = [("Squarespace", ("198.185.159.", "198.49.23.", "198.185.159.1")), ("Wix", ("185.230.63.", "23.236.62.147")), ("Shopify", ("23.227.38.",)),
               ("GitHub Pages", ("185.199.108.", "185.199.109.", "185.199.110.", "185.199.111.")), ("Netlify", ("75.2.60.5", "99.83.190.102")), ("Jimdo", ("178.248.", "91.184.")),
               ("IONOS Webhosting", ("217.160.", "82.165.", "212.227.", "87.106.")), ("STRATO", ("81.169.", "85.214."))]
ANBIETER_NS = [("IONOS", ("ui-dns.", "1und1.", "ionos.")), ("Squarespace", ("squarespacedns", "squarespace")), ("GoDaddy", ("domaincontrol.com",)), ("Cloudflare", ("cloudflare.com",)),
               ("STRATO", ("strato.",)), ("Hetzner", ("hetzner.com", "your-server.de", "hetzner.de")), ("Google Domains", ("googledomains",)), ("Wix", ("wixdns",)), ("Namecheap", ("registrar-servers",)),
               ("Telekom", ("t-ipnet", "telekom.")), ("All-Inkl", ("kasserver.",))]


def _test_daten() -> dict | None:
    if not config.DNS_TEST_DATEI:
        return None
    try:
        return json.load(open(config.DNS_TEST_DATEI))
    except (OSError, ValueError):
        return {}


def abfragen(name: str, typ: str) -> list[str] | None:
    """Antworten für A, AAAA, CNAME, NS; [] wenn es keine gibt; None, wenn die Abfrage nicht möglich war."""
    t = _test_daten()
    if t is not None:
        return t.get(f"{name}|{typ}", [])
    try:
        import dns.exception
        import dns.resolver
    except ImportError:
        return None
    r = dns.resolver.Resolver(configure=True)
    r.nameservers = ["1.1.1.1", "8.8.8.8"]     # öffentliche Resolver statt eines möglicherweise veralteten lokalen Caches
    r.lifetime = 6
    try:
        return sorted(str(x).rstrip(".") for x in r.resolve(name, typ))
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return []
    except dns.exception.DNSException:
        return None


def anbieter_ip(ip: str) -> str | None:
    for name, praefixe in ANBIETER_IP:
        if any(ip.startswith(p) for p in praefixe):
            return name
    return None


def anbieter_ns(ns: list[str]) -> str | None:
    for n in ns:
        for name, teile in ANBIETER_NS:
            if any(t in n.lower() for t in teile):
                return name
    return None


def server_adressen(cur) -> tuple[list[str], list[str]]:
    """Öffentliche Adressen des Servers: Einstellung > Umgebung > vom Server-Dienst ermittelt."""
    e = einstellungen.lesen(cur, "server") or {}
    v4 = [x.strip() for x in (e.get("ipv4") or "").split(",") if x.strip()] or list(config.SERVER_IPV4)
    v6 = [x.strip() for x in (e.get("ipv6") or "").split(",") if x.strip()] or list(config.SERVER_IPV6)
    if not v4:
        try:
            d = json.loads((config.QUEUE_DIR / "serverip.json").read_text())
            v4 = [d["v4"]] if d.get("v4") else []
            v6 = v6 or ([d["v6"]] if d.get("v6") else [])
        except (OSError, ValueError, KeyError):
            pass
    gueltig = []
    for x in v4:
        try:
            ipaddress.IPv4Address(x)
            gueltig.append(x)
        except ValueError:
            pass
    v6g = []
    for x in v6:
        try:
            ipaddress.IPv6Address(x)
            v6g.append(x)
        except ValueError:
            pass
    return gueltig, v6g


def _host(name: str, v4: list[str], v6: list[str]) -> dict:
    a, aaaa, cname = abfragen(name, "A"), abfragen(name, "AAAA"), abfragen(name, "CNAME")
    h = {"name": name, "a": a or [], "aaaa": aaaa or [], "cname": cname or [], "status": "unbekannt", "zeigt_auf": None, "aaaa_stoert": False}
    if a is None:
        return h
    if not a:
        h["status"] = "fehlt"
        return h
    fremd = [x for x in a if x not in v4]
    h["status"] = "ok" if v4 and not fremd else "falsch"
    if h["status"] == "falsch":
        h["zeigt_auf"] = next((anbieter_ip(x) for x in a if anbieter_ip(x)), None) or ("eine andere Adresse: " + a[0])
    if aaaa:
        h["aaaa_stoert"] = not v6 or any(x.lower() not in [y.lower() for y in v6] for x in aaaa)
    return h


def pruefen(domain: str, v4: list[str], v6: list[str]) -> dict:
    domain = domain.strip().lower().rstrip(".")
    ns = abfragen(domain, "NS")
    apex, www = _host(domain, v4, v6), _host("www." + domain, v4, v6)
    anb = anbieter_ns(ns or [])
    probleme, schritte = [], []
    ip = v4[0] if v4 else "<Server-IP>"
    if not v4:
        probleme.append("Die öffentliche Adresse des Servers ist noch nicht bekannt. Sie wird vom Server stündlich ermittelt oder unter Einstellungen → Server eingetragen.")
    for h, label in ((apex, domain), (www, "www." + domain)):
        if h["status"] == "unbekannt":
            probleme.append(f"{label}: die DNS-Abfrage war nicht möglich (später erneut versuchen).")
        elif h["status"] == "fehlt":
            probleme.append(f"{label} hat keinen A-Eintrag.")
        elif h["status"] == "falsch":
            probleme.append(f"{label} zeigt noch auf {h['zeigt_auf']} und nicht auf diesen Server.")
        if h["aaaa_stoert"]:
            probleme.append(f"{label} hat einen AAAA-Eintrag (IPv6) {h['aaaa'][0]}, der nicht zu diesem Server gehört. Besucher und das Zertifikat landen dort.")
    if anb and probleme:
        schritte.append(f"Die DNS-Einträge dieser Domain werden bei {anb} verwaltet. Änderungen müssen dort erfolgen (nicht beim Registrar, falls das ein anderer ist).")
    if apex["status"] != "ok":
        schritte.append(f"A-Eintrag für {domain} (Host „@“ oder leer) auf {ip} setzen. Alle anderen A-Einträge für diesen Namen löschen.")
    if www["status"] != "ok":
        schritte.append(f"A-Eintrag für www.{domain} (Host „www“) auf {ip} setzen, oder einen CNAME von www auf {domain}. Vorhandene andere Einträge für www löschen.")
    if apex["aaaa_stoert"] or www["aaaa_stoert"]:
        schritte.append("AAAA-Einträge für @ und www löschen" + (f" oder auf {v6[0]} setzen." if v6 else "."))
    if probleme:
        schritte.append("Danach prüfen, dass beim Anbieter keine Weiterleitung oder Parkseite für die Domain aktiv ist, und etwas warten (die TTL der alten Einträge bestimmt, wie lange; oft 1 bis 4 Stunden).")
    ok = apex["status"] == "ok" and www["status"] == "ok" and not apex["aaaa_stoert"] and not www["aaaa_stoert"]
    text = ""
    if not ok and v4:
        text = (f"Guten Tag,\n\nfür die Umstellung Ihrer Website bitte in der Verwaltung Ihrer Domain {domain}" + (f" bei {anb}" if anb else "") + " (Bereich „DNS“) diese Änderungen vornehmen:\n\n"
                + "\n".join(f"{i}. {s}" for i, s in enumerate([x for x in schritte if not x.startswith("Danach")], 1)) +
                "\n\nDie Änderung gilt nach einigen Minuten bis wenigen Stunden. Bitte melden Sie sich, wenn Sie fertig sind, dann prüfen wir alles und schalten die Seite frei.\n\nViele Grüße")
    return {"domain": domain, "geprueft": True, "ok": ok, "nameserver": ns or [], "dns_anbieter": anb, "apex": apex, "www": www,
            "probleme": probleme, "schritte": schritte, "kundentext": text, "server_ipv4": v4, "server_ipv6": v6}
