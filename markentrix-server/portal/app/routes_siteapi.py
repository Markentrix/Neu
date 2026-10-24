"""Website-API für fertig gebaute Kunden-Websites (Vertrag „mk-api v1“).

Eine Kunden-Website (z. B. elbdetail.de) ruft unter ihrer eigenen Domain /api/anfrage, /api/slots, /api/verfuegbarkeit und /api/e auf.
Caddy leitet genau diese Pfade an das Portal weiter (als /siteapi/api/…, Host-Kopfzeile bleibt erhalten). Das Portal erkennt den Kunden an der Domain.
Die Website braucht dafür kein eigenes Backend und keinen eigenen Admin: Anfragen, Termine, Sperrtage und Statistik liegen im Kundenportal.

Der Vertrag ist bewusst stabil: Pfade, Felder und Antworten ändern sich nicht. Neue Felder kommen nur dazu."""
import hashlib
import json
import re
import secrets
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, quote, urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from . import config, push
from . import sitedienste as sd
from .db import tx
from .routes_sitedienste import _empfaenger, _termin_mails
from .security import EMAIL_RE, client_ip, rate_limit

router = APIRouter(prefix="/siteapi/api", include_in_schema=False)
TZ = sd.TZ
TITEL = {"kontakt": "Anfrage", "termin": "Terminanfrage", "gutschein": "Gutscheinbestellung", "firma": "Firmenanfrage", "widerruf": "Widerruf", "warteliste": "Wartelisten-Anfrage"}
PRAEFIX = {"kontakt": "K", "termin": "T", "gutschein": "G", "firma": "F", "widerruf": "W", "warteliste": "L"}
LABELS = {"name": "Name", "telefon": "Telefon", "email": "E-Mail", "nachricht": "Nachricht", "paket": "Paket", "klasse": "Fahrzeugklasse", "fahrzeug": "Fahrzeug",
          "zustand": "Zustand", "extras": "Extras", "abholung": "Abholung", "datum": "Wunschtag", "datum2": "Ersatztag", "uhrzeit": "Uhrzeit", "zeitfenster": "Zeitfenster",
          "kanal": "Rückmeldung per", "personen": "Personen", "gutscheincode": "Gutscheincode", "bewertung_ok": "Bewertung gewünscht", "quelle": "Gefunden über", "winterschutz": "Winterschutz",
          "art": "Art", "wunschbetrag": "Betrag", "betrag": "Betrag", "fuer": "Für", "von": "Von", "widmung": "Widmung", "zustellung": "Zustellung", "vorgang": "Vorgangsnummer",
          "leistung": "Leistung", "mitarbeiter": "Mitarbeiter", "haarlaenge": "Haarlänge", "haarzustand": "Haarzustand", "letzte_behandlung": "Letzte Behandlung", "wunschzeit": "Wunschzeit", "terminart": "Terminart", "kennzeichen": "Kennzeichen", "marke": "Marke", "modell": "Modell", "baujahr": "Baujahr", "fahrzeugtyp": "Fahrzeugtyp", "anliegen": "Anliegen", "firma": "Firma", "anzahl": "Anzahl Fahrzeuge", "intervall": "Intervall", "leistungen": "Leistungen", "agb": "AGB akzeptiert", "vorzeitig": "Vorzeitiger Leistungsbeginn"}
SCHLUESSEL = re.compile(r"^[a-z][a-z0-9_]{0,30}$")
TELEFON = re.compile(r"^[0-9+()/ \-.]{5,40}$")
BOT = re.compile(r"bot|crawl|spider|slurp|preview|headless|curl|wget|python|monitor|uptime|lighthouse|facebookexternal", re.I)
DOMAIN = re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$")


class Ungueltig(Exception):
    def __init__(self, fehler: dict):
        self.fehler = fehler


def _json(daten, status: int = 200, kopf: dict | None = None) -> JSONResponse:
    return JSONResponse(daten, status_code=status, headers={"Cache-Control": "no-store", **(kopf or {})})


def _host(request: Request) -> str:
    h = (request.headers.get("host") or "").split(":")[0].lower().strip(".")
    return h[4:] if h.startswith("www.") else h


def _lade(request: Request) -> dict:
    """Kunde und Einstellungen anhand der Domain. Seiten fremder Domains dürfen nicht schreiben (Herkunftsprüfung)."""
    host = _host(request)
    if not DOMAIN.match(host):
        raise HTTPException(404, "Unbekannte Website.")
    origin = request.headers.get("origin")
    if origin and request.method != "GET":
        oh = (urlparse(origin).hostname or "").lower()
        if oh not in (host, "www." + host):
            raise HTTPException(403, "Herkunft nicht erlaubt.")
    with tx("system") as cur:
        cur.execute("""SELECT w.kunden_id FROM websites w JOIN kunden k ON k.id=w.kunden_id
                       WHERE w.domain=%s AND w.art='live' AND w.status IN ('live','pausiert') AND k.status<>'beendet'""", (host,))
        w = cur.fetchone()
        if not w:
            raise HTTPException(404, "Unbekannte Website.")
        z = sd.zeile(cur, w["kunden_id"])
        if z.get("verzug_pause") and request.method != "GET":
            raise HTTPException(503, "Dieser Dienst ist vorübergehend nicht verfügbar. Bitte rufen Sie uns direkt an.")
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (w["kunden_id"],))
        z["_firma"] = cur.fetchone()["firma"]
    z["_domain"] = host
    return z


def _paypal_me(z: dict) -> str:
    """PayPal.Me-Link des Betriebs aus dem Portal (nur wenn PayPal dort eingeschaltet ist), damit Websites ihn nicht selbst im Code tragen müssen."""
    link = (z.get("pp_me_link") or "").strip().rstrip("/")
    return link if z.get("pp_aktiv") and link.startswith("https://") else ""


def _geschlossen(z: dict) -> list:
    """Ruhetage im JavaScript-Format (0 = Sonntag)."""
    return [d for d in range(7) if (7 if d == 0 else d) not in z["kal_wochentage"]]


def _zeiten(z: dict) -> list:
    fest = sd.zeiten_liste(z)
    if fest:
        return fest
    zs, t = [], datetime(2000, 1, 1, *map(int, z["kal_von"].split(":")))
    schluss = datetime(2000, 1, 1, *map(int, z["kal_bis"].split(":")))
    while t + timedelta(minutes=z["kal_dauer"]) <= schluss and len(zs) < 48:
        zs.append(t.strftime("%H:%M"))
        t += timedelta(minutes=z["kal_dauer"])
    return zs or ["09:00"]


@router.get("/health")
def gesund():
    return _json({"ok": True})


EGAL = {"", "egal", "beliebig", "any", "keine", "0"}


def _personen(v) -> int:
    try:
        return max(1, min(5, int(str(v).strip() or 1)))
    except ValueError:
        return 1


def _auswahl(cur, z: dict, leistung, mitarbeiter: str, personen=1):
    """Wunsch-Leistung(en) und -Mitarbeiter (Kurznamen der Website) -> (Leistung|None, Mitarbeiter-ID|None, Mitarbeitername).
    Mehrere Leistungen (Liste oder durch Komma getrennt) werden zu einer zusammengefasst: Dauer und Preis addiert."""
    mid, mname = None, ""
    if isinstance(leistung, list):
        wuensche = [str(x).strip().lower() for x in leistung if str(x).strip()]
    else:
        wuensche = [(leistung or "").strip().lower()] if (leistung or "").strip() else []
    mitarbeiter = (mitarbeiter or "").strip().lower()
    zeilen = []
    for w in wuensche:
        cur.execute("SELECT * FROM website_leistungen WHERE kunden_id=%s AND aktiv AND (schluessel=%s OR lower(name)=%s)", (z["kunden_id"], w, w))
        lz = cur.fetchone()
        if not lz and "," in w:
            for teil in [t.strip() for t in w.split(",") if t.strip()][:5]:
                cur.execute("SELECT * FROM website_leistungen WHERE kunden_id=%s AND aktiv AND (schluessel=%s OR lower(name)=%s)", (z["kunden_id"], teil, teil))
                x = cur.fetchone()
                if x:
                    zeilen.append(x)
                else:
                    raise Ungueltig({"leistung": "Bitte nur Leistungen aus der Liste wählen."})
            continue
        if not lz:
            cur.execute("SELECT count(*) AS n FROM website_leistungen WHERE kunden_id=%s AND aktiv", (z["kunden_id"],))
            if cur.fetchone()["n"]:
                raise Ungueltig({"leistung": "Bitte eine Leistung wählen."})
        else:
            zeilen.append(lz)
    ids = []
    zeilen = [x for x in zeilen if not (x["id"] in ids or ids.append(x["id"]))][:5]
    lz = sd.leistungen_kombinieren(zeilen)
    if lz:
        lz = {**lz, "_einzeln": zeilen}
        n = _personen(personen)
        if n > 1:                                      # mehrere Personen nacheinander beim selben Mitarbeiter: Dauer, Preis und Anzahlung mal Anzahl
            p = sd.preis_zahl(lz.get("preis"))
            lz = {**lz, "dauer_min": lz["dauer_min"] * n, "preis": f"{p * n:.2f} €" if p else lz.get("preis"),
                  "anzahlung_wert": (float(lz["anzahlung_wert"]) * n if lz.get("anzahlung_art") == "betrag" and lz.get("anzahlung_wert") is not None else lz.get("anzahlung_wert"))}
    if mitarbeiter not in EGAL:
        cur.execute("SELECT id, name FROM website_mitarbeiter WHERE kunden_id=%s AND aktiv AND (schluessel=%s OR lower(name)=%s)", (z["kunden_id"], mitarbeiter, mitarbeiter))
        m = cur.fetchone()
        if not m:
            raise Ungueltig({"mitarbeiter": "Bitte eine Person wählen."})
        mid, mname = m["id"], m["name"]
    return lz, mid, mname


def _pflichtfelder(lz: dict | None, felder: dict, einzeln: list[dict]) -> dict:
    """Pflichtangaben der gewählten Leistung(en). Rückgabe: {Feldname: Fehlertext}."""
    fehler = {}
    for l in einzeln:
        for f in (l.get("felder") or []):
            if f.get("pflicht") and not felder.get(f["key"]):
                fehler[f["key"]] = f"Bitte „{f['label']}“ angeben."
    return fehler


@router.get("/leistungen")
def leistungen(request: Request):
    rate_limit("api-leist:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        cur.execute("SELECT * FROM website_leistungen WHERE kunden_id=%s AND aktiv ORDER BY sort, name", (z["kunden_id"],))
        l = [{"key": r["schluessel"], "name": r["name"], "beschreibung": r["beschreibung"] or "", "preis": r["preis"] or "", "dauer": r["dauer_min"],
              "freigabe": bool(z["kal_freigabe"] or r["freigabe"]), "felder": r["felder"] or [], "anzahlung": f"{a:.2f}" if (a := sd.anzahlung_berechnen(r)) else ""} for r in cur.fetchall()]
    return _json({"leistungen": l})


@router.get("/mitarbeiter")
def mitarbeiter(request: Request):
    rate_limit("api-mitarb:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        cur.execute("""SELECT m.id, m.schluessel, m.name, coalesce(array_agg(l.schluessel) FILTER (WHERE l.id IS NOT NULL), '{}') AS leistungen
                       FROM website_mitarbeiter m LEFT JOIN website_mitarbeiter_leistungen x ON x.mitarbeiter_id=m.id LEFT JOIN website_leistungen l ON l.id=x.leistung_id AND l.aktiv
                       WHERE m.kunden_id=%s AND m.aktiv GROUP BY m.id ORDER BY m.sort, m.name""", (z["kunden_id"],))
        return _json({"mitarbeiter": [{"key": r["schluessel"], "name": r["name"], "leistungen": list(r["leistungen"])} for r in cur.fetchall()]})


@router.get("/verfuegbarkeit")
def verfuegbarkeit(request: Request, leistung: str = "", mitarbeiter: str = "", personen: int = 1):  # leistung: ein Schlüssel oder mehrere durch Komma
    rate_limit("api-verf:" + client_ip(request), 120, 60)
    z = _lade(request)
    heute = datetime.now(TZ).date()
    if not z["kal_aktiv"]:
        return _json({"blocked": [], "blockedKeramik": [], "closedWeekdays": _geschlossen(z), "nextFree": None, "selfBooking": False, "slotTimes": _zeiten(z), "paypalMe": _paypal_me(z)})
    try:
        with tx("system") as cur:
            sd.reservierungen_verfallen(cur, z["kunden_id"], z["kal_halte_std"])
            lz, mid, _ = _auswahl(cur, z, leistung, mitarbeiter, personen)
            plan = sd.slotplan(cur, z, leistung=lz, mitarbeiter=mid)
            res = sd.ressourcen(cur, z, (lz or {}).get("id"), mid)
            team = any(r["id"] for r in res)
            offen = set().union(*[set(r["wochentage"]) for r in res]) if res else set()
    except Ungueltig as e:
        return _json({"ok": False, "errors": e.fehler, "message": "Bitte die Auswahl prüfen."}, 422)
    gesperrt = [d.isoformat() for d, s in plan.items() if not any(x[2] for x in s)]
    ab = heute + timedelta(days=z["kal_tage"] + 1)
    gesperrt += [(ab + timedelta(days=i)).isoformat() for i in range(0, 400 - z["kal_tage"])]     # jenseits des Buchungszeitraums gibt es noch keine Termine
    frei = [d.isoformat() for d, s in sorted(plan.items()) if any(x[2] for x in s)]
    alle_zeiten = {x[0] for s in plan.values() for x in s}
    zeiten = sorted(alle_zeiten) if (z.get("kal_wochenplan") and alle_zeiten) else (sorted(set(_zeiten(z)) | alle_zeiten) if team else _zeiten(z))
    geschlossen = [d for d in range(7) if (7 if d == 0 else d) not in offen]
    return _json({"blocked": gesperrt, "blockedKeramik": gesperrt, "closedWeekdays": geschlossen, "nextFree": frei[0] if frei else None,
                  "selfBooking": not (z["kal_freigabe"] or (lz or {}).get("freigabe")), "slotTimes": zeiten, "paypalMe": _paypal_me(z)})


@router.get("/slots")
def slots(request: Request, tag: str = "", leistung: str = "", mitarbeiter: str = "", personen: int = 1):
    rate_limit("api-slots:" + client_ip(request), 120, 60)
    z = _lade(request)
    try:
        d = date.fromisoformat(tag)
    except ValueError:
        return _json({"ok": False, "message": "Ungültiges Datum"}, 400)
    if not z["kal_aktiv"]:
        return _json({"tag": tag, "slots": [{"zeit": t, "frei": False} for t in _zeiten(z)]})
    try:
        with tx("system") as cur:
            sd.reservierungen_verfallen(cur, z["kunden_id"], z["kal_halte_std"])
            lz, mid, _ = _auswahl(cur, z, leistung, mitarbeiter, personen)
            plan = sd.slotplan(cur, z, leistung=lz, mitarbeiter=mid)
    except Ungueltig as e:
        return _json({"ok": False, "errors": e.fehler, "message": "Bitte die Auswahl prüfen."}, 422)
    vorhanden = {x[0]: x[2] for x in plan.get(d, [])}
    zeiten = sorted(vorhanden) if z.get("kal_wochenplan") and vorhanden else sorted(set(_zeiten(z)) | set(vorhanden))
    return _json({"tag": tag, "slots": [{"zeit": t, "frei": bool(vorhanden.get(t, False))} for t in zeiten]})


async def _roh(request: Request) -> bytes:
    return (await request.body())[:30_001]


@router.post("/e")
def ereignis(request: Request, roh: bytes = Depends(_roh)):
    """Anonyme Besucherstatistik: kein Cookie, keine IP-Adresse. Die Besucherkennung ist ein Hash, der sich täglich ändert."""
    try:
        rate_limit("api-e:" + client_ip(request), 120, 60)
        ua = request.headers.get("user-agent", "")
        roh = roh[:4096]
        z = _lade(request)
        if not z["stat_aktiv"] or not ua or BOT.search(ua):
            return Response(status_code=204)
        p = json.loads(roh or b"{}")
        if not isinstance(p, dict) or p.get("t") not in ("pv", "ev"):
            return Response(status_code=204)
        try:
            w = int(p.get("w"))
            geraet = "Mobil" if w < 640 else ("Tablet" if w < 1024 else "Desktop")
        except (TypeError, ValueError):
            geraet = ""
        utm = p.get("utm") if isinstance(p.get("utm"), dict) else {}
        quelle = re.sub(r"[^a-z0-9.\-]", "", str(utm.get("s") or p.get("r") or "").lower())[:100]
        pfad = (urlparse(str(p.get("u") or "/")).path or "/")[:120]
        tag = datetime.now(TZ).date()
        besucher = hashlib.sha256(f"{config.PORTAL_SECRET}|{tag}|{z['kunden_id']}|{client_ip(request)}|{ua}".encode()).hexdigest()[:16]
        with tx("system") as cur:
            cur.execute("INSERT INTO website_stat (kunden_id, tag, art, name, pfad, quelle, geraet, besucher) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (z["kunden_id"], tag, p["t"], str(p.get("n") or "")[:60] or None, pfad, quelle or None, geraet or None, besucher))
            if secrets.randbelow(200) == 0:
                cur.execute("DELETE FROM website_stat WHERE kunden_id=%s AND tag < current_date - 400", (z["kunden_id"],))
    except HTTPException:
        pass
    except Exception:  # noqa: BLE001 - die Statistik darf nie die Seite stören
        pass
    return Response(status_code=204)


# ---------------------------------------------------------------- Anfragen
def _text(v, grenze: int) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v)).strip()[:grenze]


def _daten(request: Request, roh: bytes) -> tuple[dict, bool]:
    if len(roh) > 30_000:
        raise HTTPException(413, "Die Eingabe ist zu lang.")
    ct = (request.headers.get("content-type") or "").lower()
    if ct.startswith("application/x-www-form-urlencoded"):
        q = parse_qs(roh.decode("utf-8", "replace"), keep_blank_values=True)
        return {k: (v if len(v) > 1 else v[0]) for k, v in q.items()}, True
    try:
        d = json.loads(roh or b"{}")
    except ValueError:
        raise HTTPException(400, "Ungültige Anfrage.")
    if not isinstance(d, dict):
        raise HTTPException(400, "Ungültige Anfrage.")
    return d, False


def _pruefen(d: dict, z: dict) -> dict:
    """Prüft die Eingabe allgemein (Pflichtfelder, Formate). Preis- und Paketschlüssel kennt nur die Website selbst und werden nicht geprüft."""
    typ = d.get("typ")
    if typ not in TITEL:
        raise Ungueltig({"typ": "Unbekannte Anfrage."})
    fehler: dict = {}
    felder: dict = {}
    for k, v in list(d.items())[:60]:
        k = str(k)
        if k in ("typ", "website", "hp", "einwilligung") or not SCHLUESSEL.match(k):
            continue
        if isinstance(v, list):
            v = [_text(x, 120) for x in v[:20] if _text(x, 120)]
        elif isinstance(v, (str, int, float)) and not isinstance(v, bool):
            v = _text(v, 2000)
        else:
            continue
        if v not in ("", []):
            felder[k] = v
    name = felder.get("name", "")
    if not 2 <= len(name) <= 120:
        fehler["name"] = "Bitte den Namen angeben."
    tel, mail = felder.get("telefon", ""), felder.get("email", "").lower()
    if mail:
        felder["email"] = mail
    if tel and not TELEFON.match(tel):
        fehler["telefon"] = "Bitte eine gültige Telefonnummer angeben."
    if mail and not EMAIL_RE.match(mail):
        fehler["email"] = "Bitte eine gültige E-Mail-Adresse angeben."
    if typ == "termin" and not tel:
        fehler["telefon"] = "Bitte eine Telefonnummer angeben."
    if typ in ("gutschein", "firma", "widerruf", "warteliste") and not mail:
        fehler["email"] = "Bitte eine E-Mail-Adresse angeben."
    if typ == "kontakt" and not tel and not mail:
        fehler["telefon"] = "Bitte Telefon oder E-Mail angeben."
    if typ != "widerruf" and d.get("einwilligung") not in ("ja", "on", True, "true", "1", 1):
        fehler["einwilligung"] = "Bitte die Datenschutzhinweise bestätigen."
    heute = datetime.now(TZ).date()
    if typ in ("termin", "warteliste"):
        for k in ("datum", "datum2"):
            raw = felder.get(k, "")
            if not raw:
                if k == "datum":
                    fehler[k] = "Bitte einen Tag wählen."
                continue
            try:
                tag = date.fromisoformat(str(raw))
            except ValueError:
                fehler[k] = "Ungültiges Datum."
                continue
            if tag < heute:
                fehler[k] = "Bitte ein Datum ab heute wählen."
            elif tag > heute + timedelta(days=400):
                fehler[k] = "Bitte ein Datum innerhalb der nächsten 12 Monate wählen."
        u = felder.get("uhrzeit", "")
        if u and not sd.ZEIT_RE.match(str(u)):
            fehler["uhrzeit"] = "Bitte eine gültige Uhrzeit wählen."
    if typ == "gutschein":
        roh = felder.get("wunschbetrag") or felder.get("betrag") or ""
        if str(roh).strip():
            v = sd.betrag_lesen(roh)
            if v is None or not 1 <= v <= 10000:
                fehler["wunschbetrag"] = "Bitte einen gültigen Betrag angeben."
    if fehler:
        raise Ungueltig(fehler)
    felder["typ"] = typ
    return felder


def _wert_schoen(v):
    """Aus Kürzeln der Website wird lesbarer Text: „tierhaare, flecken“ → „Tierhaare, Flecken“, „ja“ → „Ja“, „email“ → „E-Mail“."""
    if not isinstance(v, str) or not v or v != v.lower() or any(c.isdigit() or c in "@:/" for c in v):
        return v
    teile = [t.strip() for t in v.split(",")]
    return ", ".join({"email": "E-Mail", "whatsapp": "WhatsApp", "sms": "SMS"}.get(t, t[:1].upper() + t[1:]) for t in teile)


def _zusammenfassung(felder: dict, labels: dict | None = None) -> str:
    zeilen = []
    for k, v in felder.items():
        if k in ("typ", "nachricht") or v in ("", []):
            continue
        if k in ("datum", "datum2"):
            try:
                v = date.fromisoformat(v).strftime("%d.%m.%Y")
            except ValueError:
                pass
        if k in ("wunschbetrag", "betrag"):
            v = v if "€" in str(v) else f"{v} €"
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        v = _wert_schoen(v)
        zeilen.append(f"{(labels or {}).get(k) or LABELS.get(k, k.replace('_', ' ').capitalize())}: {v}")
    if felder.get("nachricht"):
        zeilen.append("\nNachricht:\n" + felder["nachricht"])
    return "\n".join(zeilen)


def _mails(kid, z: dict, typ: str, ref: str, felder: dict, firma: str, buchung: dict | None, labels: dict | None = None):
    titel = TITEL[typ]
    mail = felder.get("email", "")
    text = _zusammenfassung(felder, labels)
    an = [a for a in _empfaenger((z["kal_empfaenger"] or z["mail_empfaenger"]) if buchung else z["mail_empfaenger"]) if EMAIL_RE.match(a)][:5]
    if buchung and buchung["frei"]:
        kopf = f"Neue Terminanfrage ({ref}): {buchung['wann']}.\nDie Uhrzeit ist für {z['kal_halte_std']} Stunden vorgemerkt. Bitte im Kundenportal unter „Website-Dienste“ bestätigen oder ablehnen."
    elif buchung:
        kopf = f"Neue Online-Buchung ({ref}): {buchung['wann']}. Der Termin steht im Portal unter „Heute“."
    else:
        kopf = f"Neue {titel} über die Website ({ref})."
    if buchung and buchung["zeile"].get("anzahlung"):
        kopf += f"\nAnzahlung: {buchung['zeile']['anzahlung'].replace('.', ',')} € (der Besucher hat den Zahlungslink bekommen). Nach Zahlungseingang im Portal „Anzahlung erhalten“ klicken."
    fehler = ""
    for a in an:
        ok, via = sd.kundenmail(kid, a, f"{titel}: {felder.get('name', '')} ({ref})", f"{kopf}\n\n{text}\n\n—\nSie können direkt auf diese E-Mail antworten.", reply_to=mail or None, art="kontakt")
        if not ok:
            fehler = via
    if not an:
        sd.ereignis(kid, "kontakt", False, "Kein Empfänger eingetragen, die Anfrage liegt nur im Portal unter „Anfragen“.")
    elif fehler:
        sd.ereignis(kid, "kontakt", False, "Versand fehlgeschlagen, Anfrage liegt im Portal. " + fehler[:150])
    else:
        sd.ereignis(kid, "kontakt", True, f"{titel} gesendet")
    if mail:
        if buchung and not buchung["frei"]:
            _termin_mails(kid, buchung["zeile"], z, firma, [])          # sofort bestätigt: Einladung mit Absage-Link an den Kunden
            return
        extra = f"\nIhr Wunschtermin {buchung['wann']} ist für Sie vorgemerkt. Wir prüfen ihn und melden uns mit der Bestätigung." if buchung else ""
        if buchung:
            extra += sd.zahlungsabsatz(z, buchung["zeile"].get("anzahlung"))
            extra += f"\nFalls Sie nicht können, sagen Sie bitte hier ab:\n{config.BASE_URL}/site/{z['site_id']}/termin/absagen?t={buchung['zeile']['token']}\n"
        sd.kundenmail(kid, mail, f"Eingangsbestätigung: {titel} ({ref})",
                      f"Guten Tag {felder.get('name', '')},\n\nvielen Dank, Ihre {titel} ist bei uns eingegangen. Ihre Vorgangsnummer: {ref}.{extra}\n\nIhre Angaben:\n{text}\n\nMit freundlichen Grüßen\n{firma}",
                      art="kontakt")


@router.post("/anfrage")
def anfrage(request: Request, bg: BackgroundTasks, roh: bytes = Depends(_roh)):
    rate_limit("api-anfrage:" + client_ip(request), config.SITE_API_LIMIT, 600)
    d, formular = _daten(request, roh)
    z = _lade(request)
    rate_limit("api-anfragesite:" + z["site_id"], 200, 86400)

    def fehlerantwort(status: int, meldung: str, fehler: dict | None = None):
        if formular:
            return PlainTextResponse(meldung, status_code=status)
        return _json({"ok": False, "message": meldung, **({"errors": fehler} if fehler else {})}, status)

    if d.get("website") or d.get("hp"):
        return _json({"ok": True, "ref": "OK", "status": "neu"})             # Lockfeld: so tun als ob, nichts speichern
    kid, firma = z["kunden_id"], z["_firma"]
    try:
        felder = _pruefen(d, z)
        typ = felder["typ"]
        ref = PRAEFIX[typ] + datetime.now(TZ).strftime("%y%m%d") + "-" + secrets.token_hex(2).upper()
        buchung = None
        labels: dict = {}
        kontakt = felder.get("email", "") + (", " + felder["telefon"] if felder.get("telefon") and felder.get("email") else felder.get("telefon", ""))
        with tx("system") as cur:
            cur.execute("INSERT INTO anfragen (kunden_id, name, kontakt, nachricht, quelle) VALUES (%s,%s,%s,%s,'website') RETURNING id",
                        (kid, felder["name"], kontakt, f"{TITEL[typ]} {ref}\n\n{_zusammenfassung(felder, labels)}"[:6000]))
            aid = cur.fetchone()["id"]
            if typ == "warteliste":
                lz, wunsch, _m = _auswahl(cur, z, felder.get("leistung", ""), felder.get("mitarbeiter", ""))
                cur.execute("""INSERT INTO website_warteliste (kunden_id, ref, name, email, telefon, tag, leistung_id, mitarbeiter_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (kid, ref, felder["name"], felder["email"], felder.get("telefon") or None, date.fromisoformat(felder["datum"]), (lz or {}).get("id"), wunsch))
            if typ == "gutschein":
                bt = sd.betrag_lesen(felder.get("wunschbetrag") or felder.get("betrag"))
                cur.execute("""INSERT INTO website_gutscheine (kunden_id, anfrage_id, ref, name, email, telefon, betrag, empfaenger, widmung)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (kid, aid, ref, felder["name"], felder.get("email") or None, felder.get("telefon") or None, bt,
                             str(felder.get("empfaenger") or felder.get("fuer") or "")[:120] or None, str(felder.get("widmung") or "")[:500] or None))
            if typ == "termin" and felder.get("uhrzeit") and z["kal_aktiv"] and felder.get("email"):
                cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (str(kid),))
                sd.reservierungen_verfallen(cur, kid, z["kal_halte_std"])
                lz, wunsch, mname = _auswahl(cur, z, felder.get("leistung", ""), felder.get("mitarbeiter", ""), felder.get("personen", 1))
                if lz:
                    labels = {f["key"]: f["label"] for l in lz["_einzeln"] for f in (l.get("felder") or [])}
                    miss = _pflichtfelder(lz, felder, lz["_einzeln"])
                    if miss:
                        raise Ungueltig(miss)
                tag = date.fromisoformat(felder["datum"])
                treffer = [(u, rid) for t, u, f, rid in sd.slotplan(cur, z, leistung=lz, mitarbeiter=wunsch).get(tag, []) if t == felder["uhrzeit"] and f]
                if not treffer:
                    raise Ungueltig({"uhrzeit": "Diese Uhrzeit ist leider gerade vergeben. Bitte eine andere wählen."})
                start, rid = treffer[0]
                if rid:
                    cur.execute("SELECT name FROM website_mitarbeiter WHERE id=%s", (rid,))
                    mname = cur.fetchone()["name"]
                dauer = (lz or {}).get("dauer_min") or z["kal_dauer"]
                ende = start + timedelta(minutes=dauer)
                if lz:
                    felder["leistung"] = lz["name"]
                if mname:
                    felder["mitarbeiter"] = mname
                frei_gabe = bool(z["kal_freigabe"] or (lz or {}).get("freigabe"))
                anz = sd.anzahlung_berechnen(lz)
                preis_b = sd.preis_zahl((lz or {}).get("preis"))
                titel = " – ".join(x for x in ((lz or {}).get("name"), mname) if x) or "Termin über die Website"
                cur.execute("""INSERT INTO termine (kunden_id, anfrage_id, titel, beginn, ende, kontakt_name, kontakt_info, status, notiz)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                            (kid, aid, titel[:120], start, ende, felder["name"], kontakt, "geplant" if frei_gabe else "bestaetigt", _zusammenfassung(felder, labels)[:1500]))
                tid = cur.fetchone()["id"]
                try:
                    cur.execute("""INSERT INTO website_termine (kunden_id, termin_id, start, ende, name, email, telefon, nachricht, token, status, ref, daten, mitarbeiter_id, leistung_id, puffer_min,
                                                                anzahlung, anzahlung_betrag, preis_betrag)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                   RETURNING id, start, ende, name, email, telefon, nachricht, token, anzahlung, ref""",
                                (kid, tid, start, ende, felder["name"], felder["email"], felder.get("telefon"), felder.get("nachricht"), secrets.token_urlsafe(24),
                                 "reserviert" if frei_gabe else "gebucht", ref, json.dumps(felder, ensure_ascii=False), rid, (lz or {}).get("id"), (lz or {}).get("puffer_min") or 0,
                                 f"{anz:.2f}" if anz else None, anz, preis_b))
                except Exception:
                    raise Ungueltig({"uhrzeit": "Diese Uhrzeit wurde gerade vergeben. Bitte eine andere wählen."})
                g = cur.fetchone()
                g["leistung_name"], g["mitarbeiter_name"] = (lz or {}).get("name", ""), mname
                buchung = {"zeile": g, "wann": start.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr"), "frei": frei_gabe}
            ids = push.kunde(cur, kid)
    except Ungueltig as e:
        return fehlerantwort(422, "Bitte die markierten Angaben prüfen.", e.fehler)
    push.senden(ids, f"Neue {TITEL[typ]} über die Website", f"{felder['name']}" + (f": {buchung['wann']}" if buchung else ""), "/app#" + ("heute" if buchung else "anfragen"), "anfrage")
    bg.add_task(_mails, kid, z, typ, ref, felder, firma, buchung, labels)
    if formular:
        return Response(status_code=303, headers={"Location": f"/danke.html?typ={quote(typ)}&ref={quote(ref)}"})
    return _json({"ok": True, "ref": ref, "status": "neu"})
