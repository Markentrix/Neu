"""Online-Shop für Kunden-Websites.

 - öffentlich (über die Domain der Website, wie die übrige Website-API): Katalog lesen, Bilder, Gutschein-Einstellung, Bestellung annehmen
 - /api/kunde/shop: der Inhaber pflegt Artikel, Bilder, Farben, Kategorien, Einstellungen und bearbeitet Bestellungen
Das Portal rechnet jede Bestellung mit seinen eigenen Preisen nach. Preise der Website werden nur verglichen, nie übernommen."""
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import fotos, push, shop
from . import sitedienste as sd
from .db import tx
from .routes_siteapi import TELEFON, _lade, _paypal_me
from .routes_sitedienste import _empfaenger
from .security import EMAIL_RE, audit, client_ip, rate_limit, require_inhaber, require_modul

public = APIRouter(prefix="/siteapi/api", include_in_schema=False)
kunde = APIRouter(prefix="/api/kunde/shop")


def _uuid(v: str) -> str:
    try:
        return str(uuid.UUID(str(v)))
    except ValueError:
        raise HTTPException(404, "Nicht gefunden.")


# =============================================================== öffentlich: Katalog
def _nein() -> JSONResponse:
    return JSONResponse({"ok": False}, status_code=404, headers={"Cache-Control": "no-store"})


def _einstellungen(cur, kid) -> dict | None:
    """Einstellungen, aber nur wenn der Shop eingeschaltet und das Modul gebucht ist."""
    cur.execute("SELECT 1 FROM kunden_module WHERE kunden_id=%s AND modul_code='shop' AND aktiv", (kid,))
    if not cur.fetchone():
        return None
    cur.execute("SELECT * FROM shop_einstellungen WHERE kunden_id=%s AND aktiv", (kid,))
    return cur.fetchone()


def _zeit(t) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mit_etag(request: Request, daten: dict) -> Response:
    body = json.dumps(daten, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    etag = '"' + hashlib.sha256(body).hexdigest()[:20] + '"'
    kopf = {"Cache-Control": "public, max-age=300", "ETag": etag}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=kopf)
    return Response(body, media_type="application/json", headers=kopf)


def _farben_liste(cur, kid) -> list:
    cur.execute("SELECT schluessel, name, hex FROM shop_farben WHERE kunden_id=%s ORDER BY sort, name", (kid,))
    return [{"key": r["schluessel"], "name": r["name"], "hex": r["hex"].lower()} for r in cur.fetchall()]


def _kategorien_liste(cur, kid) -> list:
    cur.execute("""SELECT k.schluessel, k.name, k.sort FROM shop_kategorien k
                   WHERE k.kunden_id=%s AND EXISTS (SELECT 1 FROM shop_produkte p WHERE p.kunden_id=k.kunden_id AND p.aktiv AND p.kategorie=k.schluessel)
                   ORDER BY k.sort, k.name""", (kid,))
    return [{"key": r["schluessel"], "name": r["name"], "sort": r["sort"]} for r in cur.fetchall()]


def _produkt_json(r: dict, farben: set, bilder: list, mit_verwandt: bool = False) -> dict:
    d = {"id": r["schluessel"], "name": r["name"], "kategorie": r["kategorie"], "preis": shop.euro(r["preis_cent"]), "kurz": r["kurz"], "lang": r["lang"],
         "material": r["material"], "masse": r["masse"], "gewicht": r["gewicht"], "farben": [f for f in r["farben"] if f in farben], "tags": list(r["tags"]),
         "personalisierbar": r["personalisierbar"], "textlabel": (r["textlabel"] or "Wunschtext") if r["personalisierbar"] else None,
         "textmax": r["textmax"] if r["personalisierbar"] else 0,
         "bilder": [{"url": f"/api/medien/{b['id']}.webp", "w": b["w"], "h": b["h"], "alt": b["alt"]} for b in bilder],
         "sort": r["sort"], "aktiv": True, "geaendert": _zeit(r["geaendert_am"])}
    if mit_verwandt:
        d["verwandt"] = list(r["verwandt"])
    return d


def _bilder_je_produkt(cur, kid, ids: list) -> dict:
    cur.execute("SELECT id, produkt_id, w, h, alt FROM shop_bilder WHERE kunden_id=%s AND produkt_id = ANY(%s::uuid[]) ORDER BY sort, erstellt_am", (kid, [str(i) for i in ids]))
    aus: dict = {}
    for b in cur.fetchall():
        aus.setdefault(str(b["produkt_id"]), []).append(b)
    return aus


@public.get("/produkte")
def katalog(request: Request):
    rate_limit("api-shop:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        e = _einstellungen(cur, z["kunden_id"])
        if not e:
            return _nein()
        cur.execute("SELECT * FROM shop_produkte WHERE kunden_id=%s AND aktiv ORDER BY sort, name", (z["kunden_id"],))
        zeilen = cur.fetchall()
        farben = _farben_liste(cur, z["kunden_id"])
        bilder = _bilder_je_produkt(cur, z["kunden_id"], [r["id"] for r in zeilen])
        kategorien = _kategorien_liste(cur, z["kunden_id"])
    keys = {f["key"] for f in farben}
    stand = max([e["geaendert_am"]] + [r["geaendert_am"] for r in zeilen])
    return _mit_etag(request, {
        "stand": _zeit(stand),
        "versand": {"pauschale": shop.euro(e["versand_pauschale_cent"]), "versandfreiAb": shop.euro(e["versandfrei_ab_cent"]) if e["versandfrei_ab_cent"] is not None else None,
                    "abholung": e["abholung"], "produktionszeit": e["produktionszeit"], "lieferzeit": e["lieferzeit"]},
        "kategorien": kategorien, "farben": farben,
        "produkte": [_produkt_json(r, keys, bilder.get(str(r["id"]), []), True) for r in zeilen]})


@public.get("/produkte/{pid}")
def produkt(pid: str, request: Request):
    rate_limit("api-shop:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        if not _einstellungen(cur, z["kunden_id"]):
            return _nein()
        cur.execute("SELECT * FROM shop_produkte WHERE kunden_id=%s AND aktiv AND schluessel=%s", (z["kunden_id"], pid[:80]))
        r = cur.fetchone()
        if not r:
            return _nein()
        keys = {f["key"] for f in _farben_liste(cur, z["kunden_id"])}
        bilder = _bilder_je_produkt(cur, z["kunden_id"], [r["id"]])
        cur.execute("SELECT schluessel FROM shop_produkte WHERE kunden_id=%s AND aktiv AND schluessel = ANY(%s)", (z["kunden_id"], list(r["verwandt"])))
        aktiv = {x["schluessel"] for x in cur.fetchall()}
    d = _produkt_json(r, keys, bilder.get(str(r["id"]), []))
    d["verwandt"] = [v for v in r["verwandt"] if v in aktiv]
    return _mit_etag(request, d)


@public.get("/farben")
def farben(request: Request):
    rate_limit("api-shop:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        if not _einstellungen(cur, z["kunden_id"]):
            return _nein()
        return _mit_etag(request, {"farben": _farben_liste(cur, z["kunden_id"])})


@public.get("/kategorien")
def kategorien(request: Request):
    rate_limit("api-shop:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        if not _einstellungen(cur, z["kunden_id"]):
            return _nein()
        return _mit_etag(request, {"kategorien": _kategorien_liste(cur, z["kunden_id"])})


@public.get("/gutschein")
def gutschein(request: Request):
    rate_limit("api-shop:" + client_ip(request), 120, 60)
    z = _lade(request)
    with tx("system") as cur:
        e = _einstellungen(cur, z["kunden_id"])
    if not e:
        return _nein()
    if not e["gutschein_aktiv"]:
        return _mit_etag(request, {"aktiv": False})
    return _mit_etag(request, {"aktiv": True, "einloesen": True, "betraege": list(e["gutschein_betraege"]), "min": e["gutschein_min"], "max": e["gutschein_max"],
                               "gueltigkeitMonate": e["gutschein_monate"], "zustellung": list(e["gutschein_zustellung"])})


GUT_UNGUELTIG = "Dieser Gutschein-Code ist ungültig, abgelaufen oder schon aufgebraucht."


def _gutschein_lesen(cur, kid, code: str, sperren: bool = False):
    """Gültiger, bezahlter Gutschein mit Restguthaben oder None. Mit sperren=True wird die Zeile für die Einlösung gesperrt."""
    code = _t(code, 40)
    if len(code) < 3:
        return None
    cur.execute("""SELECT * FROM website_gutscheine WHERE kunden_id=%s AND status='gesendet' AND lower(code)=lower(%s) AND betrag IS NOT NULL
                   AND (gueltig_bis IS NULL OR gueltig_bis >= current_date) AND betrag > eingeloest""" + (" FOR UPDATE" if sperren else ""), (kid, code))
    return cur.fetchone()


def _rest_cent(g: dict) -> int:
    return max(0, round((g["betrag"] - g["eingeloest"]) * 100))


@public.post("/gutschein/pruefen")
async def gutschein_pruefen(request: Request):
    """Prüft einen Gutschein-Code für die Kasse: {code} → {ok:true, gueltig:bool, rest, ablauf}. Stark begrenzt, damit niemand Codes durchprobiert."""
    from .routes_siteapi import _json
    rate_limit("api-gutpruef:" + client_ip(request), 10, 600)
    try:
        d = json.loads((await request.body())[:2000] or b"{}")
    except ValueError:
        d = {}
    z = _lade(request)
    rate_limit("api-gutpruefsite:" + z["site_id"], 300, 86400)
    with tx("system") as cur:
        e = _einstellungen(cur, z["kunden_id"])
        if not e:
            return _nein()
        g = _gutschein_lesen(cur, z["kunden_id"], d.get("code") if isinstance(d, dict) else "") if e["gutschein_aktiv"] else None
    if not g:
        return _json({"ok": True, "gueltig": False, "message": GUT_UNGUELTIG})
    return _json({"ok": True, "gueltig": True, "rest": shop.euro(_rest_cent(g)), "ablauf": g["gueltig_bis"].isoformat() if g["gueltig_bis"] else None})


@public.get("/medien/{datei}")
def medium(datei: str, request: Request):
    rate_limit("api-medien:" + client_ip(request), 600, 60)
    m = re.match(r"^([0-9a-f-]{36})\.webp$", datei)
    if not m:
        raise HTTPException(404, "Nicht gefunden.")
    z = _lade(request)
    with tx("system") as cur:
        if not _einstellungen(cur, z["kunden_id"]):
            raise HTTPException(404, "Nicht gefunden.")
        cur.execute("""SELECT b.daten FROM shop_bilder b JOIN shop_produkte p ON p.id=b.produkt_id
                       WHERE b.id=%s AND b.kunden_id=%s AND p.aktiv""", (m.group(1), z["kunden_id"]))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Nicht gefunden.")
    return Response(bytes(r["daten"]), media_type="image/webp", headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"})


# =============================================================== öffentlich: Bestellung
def _t(v, n: int) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(v if v is not None else "")).strip()[:n]


def _ja(v) -> bool:
    return v in ("ja", "on", True, "true", "1", 1)


def bestellung_annehmen(request: Request, bg: BackgroundTasks, d: dict, z: dict):
    """Wird von /api/anfrage mit typ=bestellung aufgerufen. Gibt die fertige Antwort zurück."""
    from .routes_siteapi import _json   # spät importiert (Kreisbezug)

    def fehler(errors: dict, status: int = 422):
        return _json({"ok": False, "message": "Bitte die markierten Angaben prüfen.", "errors": errors}, status)

    kid, firma = z["kunden_id"], z["_firma"]
    err: dict = {}
    name, mail, tel = _t(d.get("name"), 120), _t(d.get("email"), 200).lower(), _t(d.get("telefon"), 40)
    if not 2 <= len(name) <= 120:
        err["name"] = "Bitte den Namen angeben."
    if not EMAIL_RE.match(mail):
        err["email"] = "Bitte eine gültige E-Mail-Adresse angeben."
    if tel and not TELEFON.match(tel):
        err["telefon"] = "Bitte eine gültige Telefonnummer angeben."
    if not _ja(d.get("einwilligung")):
        err["einwilligung"] = "Bitte die Datenschutzhinweise bestätigen."
    if not _ja(d.get("agb")):
        err["agb"] = "Bitte die AGB bestätigen."
    lieferart, zahlungsart = _t(d.get("lieferart"), 20), _t(d.get("zahlungsart"), 20)
    if lieferart not in ("versand", "abholung"):
        err["lieferart"] = "Bitte Versand oder Abholung wählen."
    if zahlungsart not in ("paypal", "abholung"):
        err["zahlungsart"] = "Bitte eine Zahlungsart wählen."
    if lieferart == "versand" and zahlungsart == "abholung":
        err["zahlungsart"] = "Zahlung bei Abholung gibt es nur bei Abholung."
    adresse = None
    if lieferart == "versand":
        a = d.get("adresse") if isinstance(d.get("adresse"), dict) else {}
        adresse = {"strasse": _t(a.get("strasse"), 120), "plz": _t(a.get("plz"), 10), "ort": _t(a.get("ort"), 80), "land": (_t(a.get("land"), 2) or "DE").upper()}
        if len(adresse["strasse"]) < 3:
            err["strasse"] = "Bitte Straße und Hausnummer angeben."
        if not shop.PLZ.match(adresse["plz"]):
            err["plz"] = "Bitte die Postleitzahl angeben."
        if len(adresse["ort"]) < 2:
            err["ort"] = "Bitte den Ort angeben."
        if not re.match(r"^[A-Z]{2}$", adresse["land"]):
            err["land"] = "Bitte das Land angeben."
    roh = d.get("positionen")
    if not isinstance(roh, list) or not 1 <= len(roh) <= 30:
        err["positionen"] = "Der Warenkorb ist leer oder zu groß."
    if err:
        return fehler(err)
    abweichung = False
    with tx("system") as cur:
        e = _einstellungen(cur, kid)
        if not e:
            return _nein()
        if lieferart == "abholung" and not e["abholung"]:
            return fehler({"lieferart": "Abholung ist nicht möglich."})
        farbname = {f["key"]: f["name"] for f in _farben_liste(cur, kid)}
        pos, zwischen = [], 0
        for i, p in enumerate(roh):
            if not isinstance(p, dict):
                return fehler({"positionen": "Ungültige Position."})
            cur.execute("SELECT * FROM shop_produkte WHERE kunden_id=%s AND aktiv AND schluessel=%s", (kid, _t(p.get("id"), 80)))
            r = cur.fetchone()
            if not r:
                return fehler({"positionen": f"Der Artikel „{_t(p.get('name'), 60) or _t(p.get('id'), 40)}“ ist nicht mehr verfügbar."})
            try:
                menge = int(p.get("menge"))
            except (TypeError, ValueError):
                menge = 0
            if not 1 <= menge <= 99:
                return fehler({"positionen": "Bitte eine Menge zwischen 1 und 99 wählen."})
            farbe = _t(p.get("farbe"), 60)
            moegliche = [f for f in r["farben"] if f in farbname]
            if moegliche and farbe not in moegliche:
                return fehler({"positionen": f"Bitte für „{r['name']}“ eine verfügbare Farbe wählen."})
            if not moegliche:
                farbe = ""
            text = _t(p.get("text"), 300)
            if r["personalisierbar"]:
                if not text:
                    return fehler({"positionen": f"Bitte den {r['textlabel'] or 'Wunschtext'} für „{r['name']}“ angeben."})
                if len(text) > r["textmax"]:
                    return fehler({"positionen": f"Der {r['textlabel'] or 'Wunschtext'} für „{r['name']}“ darf höchstens {r['textmax']} Zeichen lang sein."})
            else:
                text = ""
            if p.get("einzelpreis") not in (None, "") and shop.cent(p.get("einzelpreis")) != r["preis_cent"]:
                abweichung = True
            pos.append({"produkt_schluessel": r["schluessel"], "name": r["name"], "farbe": farbe or None, "farbe_name": farbname.get(farbe), "wunschtext": text or None,
                        "menge": menge, "einzelpreis_cent": r["preis_cent"]})
            zwischen += r["preis_cent"] * menge
        versand = shop.versandkosten(e, zwischen, lieferart)
        summe = zwischen + versand
        gcode = _t(d.get("gutscheincode"), 40)
        gut, abzug = None, 0
        if gcode:
            gut = _gutschein_lesen(cur, kid, gcode, True) if e["gutschein_aktiv"] else None
            if not gut:
                return fehler({"gutscheincode": GUT_UNGUELTIG})
            abzug = min(_rest_cent(gut), summe)
        for feld, wert in (("zwischensumme", zwischen), ("versand", versand), ("summe", summe)):
            if d.get(feld) not in (None, "") and shop.cent(d.get(feld)) != wert:
                abweichung = True
        if abweichung:
            return fehler({"summe": "Die Preise haben sich geändert. Bitte laden Sie die Seite neu und prüfen Sie den Warenkorb."})
        jahr = datetime.now(sd.TZ).year
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("shop:" + str(kid),))
        cur.execute("SELECT coalesce(max(nr),0)+1 AS n FROM shop_bestellungen WHERE kunden_id=%s AND ref LIKE %s", (kid, f"{e['ref_praefix']}-{jahr}-%"))
        nr = cur.fetchone()["n"]
        ref = f"{e['ref_praefix']}-{jahr}-{nr:04d}"
        zuzahlen = summe - abzug
        cur.execute("""INSERT INTO shop_bestellungen (kunden_id, ref, nr, name, email, telefon, lieferart, adresse, zahlungsart, zwischensumme_cent, versand_cent, summe_cent, anmerkung,
                                                      gutschein_id, gutschein_code, gutschein_cent, status, bezahlt_am)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s, CASE WHEN %s THEN 'bezahlt' ELSE 'eingegangen' END, CASE WHEN %s THEN now() END) RETURNING *""",
                    (kid, ref, nr, name, mail, tel or None, lieferart, json.dumps(adresse) if adresse else None, zahlungsart, zwischen, versand, summe, _t(d.get("anmerkung"), 1000) or None,
                     gut["id"] if gut else None, gut["code"] if gut else None, abzug, bool(gut) and zuzahlen == 0, bool(gut) and zuzahlen == 0))
        b = cur.fetchone()
        if gut:
            cur.execute("UPDATE website_gutscheine SET eingeloest = eingeloest + %s WHERE id=%s", (abzug / 100, gut["id"]))
        for p in pos:
            cur.execute("""INSERT INTO shop_positionen (kunden_id, bestellung_id, produkt_schluessel, name, farbe, farbe_name, wunschtext, menge, einzelpreis_cent)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (kid, b["id"], p["produkt_schluessel"], p["name"], p["farbe"], p["farbe_name"], p["wunschtext"], p["menge"], p["einzelpreis_cent"]))
        ids = push.kunde(cur, kid)
    me = _paypal_me(z)
    paypal_url = f"{me}/{zuzahlen / 100:.2f}{z.get('pp_waehrung') or 'EUR'}" if zahlungsart == "paypal" and me and zuzahlen > 0 else ""
    push.senden(ids, "Neue Bestellung über die Website", f"{name}: {shop.eur(zuzahlen)}", "/app#shop", "bestellung")
    bg.add_task(_bestell_mails, kid, z, firma, dict(b), pos, paypal_url)
    antwort = {"ok": True, "ref": ref, "status": "neu"}
    if gut:
        antwort["gutschein"] = {"abgezogen": shop.euro(abzug), "rest": shop.euro(_rest_cent(gut) - abzug), "zuZahlen": shop.euro(zuzahlen)}
    if paypal_url:
        antwort["paypalUrl"] = paypal_url
    return _json(antwort)


def _bestell_mails(kid, z: dict, firma: str, b: dict, pos: list, paypal_url: str):
    uebersicht = shop.bestell_uebersicht(b, pos)
    an = [a for a in _empfaenger(z["mail_empfaenger"]) if EMAIL_RE.match(a)][:5]
    for a in an:
        sd.kundenmail(kid, a, f"Neue Bestellung {b['ref']}: {b['name']}", f"Neue Bestellung über die Website ({b['ref']}).\nKontakt: {b['name']}, {b['email']}"
                      + (f", {b['telefon']}" if b.get("telefon") else "") + f"\nZahlungsart: {'PayPal' if b['zahlungsart'] == 'paypal' else 'bei Abholung'}\n\n{uebersicht}\n\n"
                      "Im Kundenportal unter „Shop“ können Sie die Bestellung bearbeiten.\n\n—\nSie können direkt auf diese E-Mail antworten.", reply_to=b["email"], art="bestellung")
    sd.kundenmail(kid, b["email"], f"Ihre Bestellung {b['ref']}",
                  f"Guten Tag {b['name']},\n\nvielen Dank für Ihre Bestellung. Ihre Bestellnummer: {b['ref']}.\n\n{uebersicht}\n\n{shop.zahlhinweis(b, paypal_url)}\n\n"
                  f"Wir melden uns, sobald es bei Ihrer Bestellung weitergeht.\n\nMit freundlichen Grüßen\n{firma}", art="bestellung")


# =============================================================== Kundenportal
class EinstellungIn(BaseModel):
    aktiv: bool = False
    ref_praefix: str = Field(default="B", pattern=r"^[A-Z0-9]{1,6}$")
    versand_pauschale: float = Field(default=4.9, ge=0, le=1000)
    versandfrei_ab: float | None = Field(default=None, ge=0, le=100000)
    abholung: bool = True
    produktionszeit: str = Field(default="", max_length=200)
    lieferzeit: str = Field(default="", max_length=200)
    gutschein_aktiv: bool = False
    gutschein_betraege: list[int] = Field(default_factory=lambda: [10, 20, 30, 50], max_length=12)
    gutschein_min: int = Field(default=10, ge=1, le=10000)
    gutschein_max: int = Field(default=500, ge=1, le=10000)
    gutschein_monate: int = Field(default=36, ge=1, le=120)
    gutschein_zustellung: list[str] = Field(default_factory=lambda: ["E-Mail (PDF)", "Post (Karte)"], max_length=6)


class NameIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    schluessel: str = Field(default="", max_length=60)
    hex: str = Field(default="#888888", max_length=7)
    sort: int = Field(default=100, ge=0, le=100000)


class ProduktIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    schluessel: str = Field(default="", max_length=60)
    kategorie: str | None = Field(default=None, max_length=60)
    preis: float = Field(ge=0, le=100000)
    kurz: str = Field(default="", max_length=400)
    lang: str = Field(default="", max_length=4000)
    material: str = Field(default="", max_length=120)
    masse: str = Field(default="", max_length=120)
    gewicht: str = Field(default="", max_length=60)
    farben: list[str] = Field(default_factory=list, max_length=40)
    tags: list[str] = Field(default_factory=list, max_length=12)
    verwandt: list[str] = Field(default_factory=list, max_length=12)
    personalisierbar: bool = False
    textlabel: str = Field(default="", max_length=80)
    textmax: int = Field(default=0, ge=0, le=200)
    sort: int = Field(default=100, ge=0, le=100000)
    aktiv: bool = False


class BestellungIn(BaseModel):
    status: str
    sendungsnummer: str = Field(default="", max_length=80)
    abholtermin: str = Field(default="", max_length=120)
    notiz: str = Field(default="", max_length=1000)
    mail: bool = False


class BildIn(BaseModel):
    alt: str = Field(default="", max_length=200)
    sort: int = Field(default=100, ge=0, le=1000)


def _gate(cur, user):
    require_modul(cur, user, "shop")


def _einst_json(e: dict | None) -> dict:
    if not e:
        return {"aktiv": False, "ref_praefix": "B", "versand_pauschale": 4.9, "versandfrei_ab": None, "abholung": True, "produktionszeit": "", "lieferzeit": "",
                "gutschein_aktiv": False, "gutschein_betraege": [10, 20, 30, 50], "gutschein_min": 10, "gutschein_max": 500, "gutschein_monate": 36,
                "gutschein_zustellung": ["E-Mail (PDF)", "Post (Karte)"]}
    return {"aktiv": e["aktiv"], "ref_praefix": e["ref_praefix"], "versand_pauschale": shop.euro(e["versand_pauschale_cent"]),
            "versandfrei_ab": shop.euro(e["versandfrei_ab_cent"]) if e["versandfrei_ab_cent"] is not None else None, "abholung": e["abholung"],
            "produktionszeit": e["produktionszeit"], "lieferzeit": e["lieferzeit"], "gutschein_aktiv": e["gutschein_aktiv"], "gutschein_betraege": list(e["gutschein_betraege"]),
            "gutschein_min": e["gutschein_min"], "gutschein_max": e["gutschein_max"], "gutschein_monate": e["gutschein_monate"], "gutschein_zustellung": list(e["gutschein_zustellung"])}


@kunde.get("")
def uebersicht(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        cur.execute("SELECT * FROM shop_einstellungen WHERE kunden_id=%s", (kid,))
        e = cur.fetchone()
        cur.execute("SELECT * FROM shop_kategorien ORDER BY sort, name")
        kats = [{"id": str(r["id"]), "schluessel": r["schluessel"], "name": r["name"], "sort": r["sort"]} for r in cur.fetchall()]
        cur.execute("SELECT * FROM shop_farben ORDER BY sort, name")
        fs = [{"id": str(r["id"]), "schluessel": r["schluessel"], "name": r["name"], "hex": r["hex"], "sort": r["sort"]} for r in cur.fetchall()]
        cur.execute("SELECT * FROM shop_produkte ORDER BY sort, name")
        prod = cur.fetchall()
        bilder = _bilder_je_produkt(cur, kid, [p["id"] for p in prod])
        cur.execute("SELECT * FROM shop_bestellungen ORDER BY erstellt_am DESC LIMIT 100")
        best = cur.fetchall()
        cur.execute("SELECT * FROM shop_positionen WHERE bestellung_id = ANY(%s::uuid[]) ORDER BY name", ([str(b["id"]) for b in best],))
        pos: dict = {}
        for p in cur.fetchall():
            pos.setdefault(str(p["bestellung_id"]), []).append({"name": p["name"], "farbe": p["farbe_name"], "text": p["wunschtext"], "menge": p["menge"], "einzelpreis": shop.euro(p["einzelpreis_cent"])})
        cur.execute("SELECT coalesce(sum(groesse),0) AS s FROM shop_bilder")
        speicher = int(cur.fetchone()["s"])
    with tx("system") as cur:                       # Dienste-Einstellungen sind nur intern lesbar
        cur.execute("SELECT pp_aktiv, pp_me_link FROM website_dienste WHERE kunden_id=%s", (kid,))
        w = cur.fetchone() or {}
        cur.execute("SELECT domain FROM websites WHERE kunden_id=%s AND art='live' AND status IN ('live','pausiert') ORDER BY domain", (kid,))
        domains = [r["domain"] for r in cur.fetchall()]
    return {"einstellungen": _einst_json(e), "kategorien": kats, "farben": fs, "domains": domains,
            "paypal_bereit": bool(w.get("pp_aktiv") and str(w.get("pp_me_link") or "").startswith("https://")), "speicher": speicher, "speicher_max": shop.BILD_SPEICHER_JE_KUNDE,
            "produkte": [{"id": str(p["id"]), "schluessel": p["schluessel"], "name": p["name"], "kategorie": p["kategorie"], "preis": shop.euro(p["preis_cent"]), "kurz": p["kurz"],
                          "lang": p["lang"], "material": p["material"], "masse": p["masse"], "gewicht": p["gewicht"], "farben": list(p["farben"]), "tags": list(p["tags"]),
                          "verwandt": list(p["verwandt"]), "personalisierbar": p["personalisierbar"], "textlabel": p["textlabel"] or "", "textmax": p["textmax"], "sort": p["sort"],
                          "aktiv": p["aktiv"], "bilder": [{"id": str(b["id"]), "w": b["w"], "h": b["h"], "alt": b["alt"]} for b in bilder.get(str(p["id"]), [])]} for p in prod],
            "bestellungen": [{"id": str(b["id"]), "ref": b["ref"], "status": b["status"], "name": b["name"], "email": b["email"], "telefon": b["telefon"], "lieferart": b["lieferart"],
                              "adresse": b["adresse"], "zahlungsart": b["zahlungsart"], "zwischensumme": shop.euro(b["zwischensumme_cent"]), "versand": shop.euro(b["versand_cent"]),
                              "summe": shop.euro(b["summe_cent"]), "gutschein_code": b["gutschein_code"] or "", "gutschein": shop.euro(b["gutschein_cent"]), "zu_zahlen": shop.euro(b["summe_cent"] - b["gutschein_cent"]), "anmerkung": b["anmerkung"], "sendungsnummer": b["sendungsnummer"] or "", "abholtermin": b["abholtermin"] or "",
                              "notiz": b["notiz"] or "", "erstellt_am": b["erstellt_am"], "bezahlt_am": b["bezahlt_am"], "positionen": pos.get(str(b["id"]), [])} for b in best]}


@kunde.put("/einstellungen")
def einstellungen_speichern(data: EinstellungIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    if data.gutschein_min > data.gutschein_max:
        raise HTTPException(422, "Der kleinste Gutscheinbetrag darf nicht über dem größten liegen.")
    betraege = sorted({b for b in data.gutschein_betraege if 1 <= b <= 10000})
    zust = [_t(x, 60) for x in data.gutschein_zustellung if _t(x, 60)][:6]
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        cur.execute("""INSERT INTO shop_einstellungen (kunden_id, aktiv, ref_praefix, versand_pauschale_cent, versandfrei_ab_cent, abholung, produktionszeit, lieferzeit, gutschein_aktiv,
                                                       gutschein_betraege, gutschein_min, gutschein_max, gutschein_monate, gutschein_zustellung, geaendert_am)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                       ON CONFLICT (kunden_id) DO UPDATE SET aktiv=EXCLUDED.aktiv, ref_praefix=EXCLUDED.ref_praefix, versand_pauschale_cent=EXCLUDED.versand_pauschale_cent,
                         versandfrei_ab_cent=EXCLUDED.versandfrei_ab_cent, abholung=EXCLUDED.abholung, produktionszeit=EXCLUDED.produktionszeit, lieferzeit=EXCLUDED.lieferzeit,
                         gutschein_aktiv=EXCLUDED.gutschein_aktiv, gutschein_betraege=EXCLUDED.gutschein_betraege, gutschein_min=EXCLUDED.gutschein_min,
                         gutschein_max=EXCLUDED.gutschein_max, gutschein_monate=EXCLUDED.gutschein_monate, gutschein_zustellung=EXCLUDED.gutschein_zustellung, geaendert_am=now()""",
                    (kid, data.aktiv, data.ref_praefix, shop.cent(data.versand_pauschale), shop.cent(data.versandfrei_ab) if data.versandfrei_ab is not None else None, data.abholung,
                     data.produktionszeit.strip(), data.lieferzeit.strip(), data.gutschein_aktiv, betraege, data.gutschein_min, data.gutschein_max, data.gutschein_monate, zust))
        audit(cur, user, "shop_einstellungen", kid, {"aktiv": data.aktiv})
    return {"ok": True}


def _liste_aendern(tabelle: str, farbe: bool):
    def neu(data: NameIn, user: dict = Depends(require_inhaber)):
        kid = user["kunden_id"]
        key = data.schluessel.strip() or shop.schluessel(data.name)
        if not re.match(r"^[a-z0-9][a-z0-9-]{0,48}$", key):
            raise HTTPException(422, "Der Kurzname darf nur Kleinbuchstaben, Ziffern und Bindestriche enthalten.")
        if farbe and not shop.HEX.match(data.hex):
            raise HTTPException(422, "Bitte eine Farbe im Format #aabbcc angeben.")
        with tx("kunde", kid) as cur:
            _gate(cur, user)
            cur.execute(f"SELECT 1 FROM {tabelle} WHERE schluessel=%s", (key,))
            if cur.fetchone():
                raise HTTPException(409, "Diesen Kurznamen gibt es schon.")
            if farbe:
                cur.execute("INSERT INTO shop_farben (kunden_id, schluessel, name, hex, sort) VALUES (%s,%s,%s,%s,%s) RETURNING id", (kid, key, data.name.strip(), data.hex, data.sort))
            else:
                cur.execute("INSERT INTO shop_kategorien (kunden_id, schluessel, name, sort) VALUES (%s,%s,%s,%s) RETURNING id", (kid, key, data.name.strip(), data.sort))
            return {"ok": True, "id": str(cur.fetchone()["id"])}

    def aendern(lid: str, data: NameIn, user: dict = Depends(require_inhaber)):
        kid = user["kunden_id"]
        if farbe and not shop.HEX.match(data.hex):
            raise HTTPException(422, "Bitte eine Farbe im Format #aabbcc angeben.")
        with tx("kunde", kid) as cur:
            _gate(cur, user)
            if farbe:
                cur.execute("UPDATE shop_farben SET name=%s, hex=%s, sort=%s WHERE id=%s RETURNING id", (data.name.strip(), data.hex, data.sort, _uuid(lid)))
            else:
                cur.execute("UPDATE shop_kategorien SET name=%s, sort=%s WHERE id=%s RETURNING id", (data.name.strip(), data.sort, _uuid(lid)))
            if not cur.fetchone():
                raise HTTPException(404, "Nicht gefunden.")
        return {"ok": True}

    def weg(lid: str, user: dict = Depends(require_inhaber)):
        kid = user["kunden_id"]
        with tx("kunde", kid) as cur:
            _gate(cur, user)
            cur.execute(f"DELETE FROM {tabelle} WHERE id=%s RETURNING schluessel", (_uuid(lid),))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Nicht gefunden.")
            if farbe:
                cur.execute("UPDATE shop_produkte SET farben = array_remove(farben, %s) WHERE kunden_id=%s", (r["schluessel"], kid))
            else:
                cur.execute("UPDATE shop_produkte SET kategorie = NULL WHERE kunden_id=%s AND kategorie=%s", (kid, r["schluessel"]))
        return {"ok": True}
    return neu, aendern, weg


for _tab, _farbe, _pfad in (("shop_kategorien", False, "kategorien"), ("shop_farben", True, "farben")):
    _n, _a, _w = _liste_aendern(_tab, _farbe)
    kunde.post(f"/{_pfad}", name=f"shop_{_pfad}_neu")(_n)
    kunde.put(f"/{_pfad}/{{lid}}", name=f"shop_{_pfad}_aendern")(_a)
    kunde.delete(f"/{_pfad}/{{lid}}", name=f"shop_{_pfad}_weg")(_w)


def _produkt_pruefen(cur, data: ProduktIn) -> dict:
    cur.execute("SELECT schluessel FROM shop_farben")
    farben = {r["schluessel"] for r in cur.fetchall()}
    cur.execute("SELECT schluessel FROM shop_kategorien")
    kats = {r["schluessel"] for r in cur.fetchall()}
    if data.kategorie and data.kategorie not in kats:
        raise HTTPException(422, "Diese Kategorie gibt es nicht.")
    if any(f not in farben for f in data.farben):
        raise HTTPException(422, "Eine gewählte Farbe gibt es nicht mehr. Bitte die Seite neu laden.")
    if data.personalisierbar and not 1 <= data.textmax <= 200:
        raise HTTPException(422, "Bei Artikeln mit Wunschtext bitte die höchste Zeichenzahl angeben (1 bis 200).")
    tags = [re.sub(r"[^a-z0-9äöüß-]", "", t.lower())[:30] for t in data.tags]
    tags = [t for t in dict.fromkeys(tags) if t]
    if data.personalisierbar and "personalisiert" not in tags:
        tags.append("personalisiert")
    verwandt = [v for v in dict.fromkeys(data.verwandt) if shop.SCHLUESSEL.match(v)]
    return {"tags": tags, "verwandt": verwandt, "farben": list(dict.fromkeys(data.farben))}


@kunde.post("/produkte")
def produkt_neu(data: ProduktIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    key = data.schluessel.strip() or shop.schluessel(data.name)
    if not shop.SCHLUESSEL.match(key):
        raise HTTPException(422, "Der Kurzname darf nur Kleinbuchstaben, Ziffern und Bindestriche enthalten.")
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        extra = _produkt_pruefen(cur, data)
        cur.execute("SELECT 1 FROM shop_produkte WHERE schluessel=%s", (key,))
        if cur.fetchone():
            raise HTTPException(409, "Diesen Kurznamen gibt es schon bei einem anderen Artikel.")
        cur.execute("""INSERT INTO shop_produkte (kunden_id, schluessel, name, kategorie, preis_cent, kurz, lang, material, masse, gewicht, farben, tags, verwandt, personalisierbar, textlabel, textmax, sort, aktiv)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (kid, key, data.name.strip(), data.kategorie or None, shop.cent(data.preis), data.kurz.strip(), data.lang.strip(), data.material.strip(), data.masse.strip(),
                     data.gewicht.strip(), extra["farben"], extra["tags"], extra["verwandt"], data.personalisierbar, data.textlabel.strip() or None,
                     data.textmax if data.personalisierbar else 0, data.sort, data.aktiv))
        return {"ok": True, "id": str(cur.fetchone()["id"]), "schluessel": key}


@kunde.put("/produkte/{pid}")
def produkt_aendern(pid: str, data: ProduktIn, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        extra = _produkt_pruefen(cur, data)
        cur.execute("""UPDATE shop_produkte SET name=%s, kategorie=%s, preis_cent=%s, kurz=%s, lang=%s, material=%s, masse=%s, gewicht=%s, farben=%s, tags=%s, verwandt=%s,
                              personalisierbar=%s, textlabel=%s, textmax=%s, sort=%s, aktiv=%s WHERE id=%s RETURNING id""",
                    (data.name.strip(), data.kategorie or None, shop.cent(data.preis), data.kurz.strip(), data.lang.strip(), data.material.strip(), data.masse.strip(), data.gewicht.strip(),
                     extra["farben"], extra["tags"], extra["verwandt"], data.personalisierbar, data.textlabel.strip() or None, data.textmax if data.personalisierbar else 0, data.sort,
                     data.aktiv, _uuid(pid)))
        if not cur.fetchone():
            raise HTTPException(404, "Diesen Artikel gibt es nicht.")
    return {"ok": True}


@kunde.delete("/produkte/{pid}")
def produkt_weg(pid: str, user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        _gate(cur, user)
        cur.execute("DELETE FROM shop_produkte WHERE id=%s RETURNING id", (_uuid(pid),))
        if not cur.fetchone():
            raise HTTPException(404, "Diesen Artikel gibt es nicht.")
    return {"ok": True}


async def _roh_bild(request: Request) -> bytes:
    try:
        if int(request.headers.get("content-length") or 0) > shop.BILD_MAX_BYTES + 1024:
            raise HTTPException(413, "Das Bild ist zu groß (höchstens 600 KB). Bitte verkleinern.")
    except ValueError:
        raise HTTPException(400, "Ungültige Anfrage.")
    return (await request.body())[:shop.BILD_MAX_BYTES + 1]


@kunde.post("/produkte/{pid}/bilder")
def bild_hoch(pid: str, alt: str = "", roh: bytes = Depends(_roh_bild), user: dict = Depends(require_inhaber)):
    """Ein Bild als WebP im Body (der Browser schneidet es vorher auf 4:3 zu und wandelt es um)."""
    kid = user["kunden_id"]
    rate_limit("shop-bild:" + str(kid), 120, 3600)
    if len(roh) > shop.BILD_MAX_BYTES:
        raise HTTPException(413, "Das Bild ist zu groß (höchstens 600 KB). Bitte verkleinern.")
    try:
        typ, sauber = fotos.pruefen(roh)
    except fotos.FotoFehler as e:
        raise HTTPException(400, str(e))
    if typ != "image/webp":
        raise HTTPException(400, "Bitte ein WebP-Bild hochladen. Der Browser wandelt es normalerweise selbst um.")
    masse = shop.webp_masse(sauber)
    if not masse or not (200 <= masse[0] <= 3000 and 150 <= masse[1] <= 3000):
        raise HTTPException(400, "Das Bild muss zwischen 200 und 3000 Pixel breit sein.")
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        cur.execute("SELECT 1 FROM shop_produkte WHERE id=%s", (_uuid(pid),))
        if not cur.fetchone():
            raise HTTPException(404, "Diesen Artikel gibt es nicht.")
        cur.execute("SELECT count(*) AS n, coalesce(sum(groesse),0) AS s FROM shop_bilder WHERE produkt_id=%s", (pid,))
        a = cur.fetchone()
        if a["n"] >= shop.BILD_MAX_JE_ARTIKEL:
            raise HTTPException(409, f"Mehr als {shop.BILD_MAX_JE_ARTIKEL} Bilder je Artikel sind nicht möglich.")
        cur.execute("SELECT coalesce(sum(groesse),0) AS s FROM shop_bilder")
        if int(cur.fetchone()["s"]) + len(sauber) > shop.BILD_SPEICHER_JE_KUNDE:
            raise HTTPException(413, "Der Bilder-Speicher ist voll. Bitte nicht benötigte Bilder löschen.")
        cur.execute("INSERT INTO shop_bilder (kunden_id, produkt_id, daten, groesse, w, h, alt, sort) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                    (kid, pid, sauber, len(sauber), masse[0], masse[1], alt.strip()[:200], a["n"] * 10 + 10))
        bid = str(cur.fetchone()["id"])
        cur.execute("UPDATE shop_produkte SET geaendert_am=now() WHERE id=%s", (pid,))
    return {"ok": True, "id": bid}


@kunde.get("/bilder/{bid}")
def bild_ansehen(bid: str, user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        _gate(cur, user)
        cur.execute("SELECT daten FROM shop_bilder WHERE id=%s", (_uuid(bid),))
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Nicht gefunden.")
    return Response(bytes(r["daten"]), media_type="image/webp", headers={"Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff"})


@kunde.put("/bilder/{bid}")
def bild_aendern(bid: str, data: BildIn, user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        _gate(cur, user)
        cur.execute("UPDATE shop_bilder SET alt=%s, sort=%s WHERE id=%s RETURNING produkt_id", (data.alt.strip(), data.sort, _uuid(bid)))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Nicht gefunden.")
        cur.execute("UPDATE shop_produkte SET geaendert_am=now() WHERE id=%s", (r["produkt_id"],))
    return {"ok": True}


@kunde.delete("/bilder/{bid}")
def bild_weg(bid: str, user: dict = Depends(require_inhaber)):
    with tx("kunde", user["kunden_id"]) as cur:
        _gate(cur, user)
        cur.execute("DELETE FROM shop_bilder WHERE id=%s RETURNING produkt_id", (_uuid(bid),))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Nicht gefunden.")
        cur.execute("UPDATE shop_produkte SET geaendert_am=now() WHERE id=%s", (r["produkt_id"],))
    return {"ok": True}


@kunde.put("/bestellungen/{bid}")
def bestellung_aendern(bid: str, data: BestellungIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    if data.status not in shop.STATI:
        raise HTTPException(422, "Unbekannter Status.")
    with tx("kunde", kid) as cur:
        _gate(cur, user)
        cur.execute("SELECT * FROM shop_bestellungen WHERE id=%s FOR UPDATE", (_uuid(bid),))
        alt = cur.fetchone()
        if not alt:
            raise HTTPException(404, "Diese Bestellung gibt es nicht.")
        if alt["status"] == "storniert" and data.status != "storniert":
            raise HTTPException(409, "Eine stornierte Bestellung lässt sich nicht wieder öffnen. Bitte eine neue Bestellung anlegen lassen.")
        if data.status == "abholbereit" and alt["lieferart"] != "abholung":
            raise HTTPException(409, "„Abholbereit“ gibt es nur bei Abholung.")
        if data.status == "versendet" and alt["lieferart"] != "versand":
            raise HTTPException(409, "„Versendet“ gibt es nur bei Versand.")
        cur.execute("""UPDATE shop_bestellungen SET status=%s, sendungsnummer=%s, abholtermin=%s, notiz=%s,
                              bezahlt_am = CASE WHEN %s = 'bezahlt' AND bezahlt_am IS NULL THEN now() ELSE bezahlt_am END WHERE id=%s RETURNING *""",
                    (data.status, data.sendungsnummer.strip() or None, data.abholtermin.strip() or None, data.notiz.strip() or None, data.status, alt["id"]))
        neu = cur.fetchone()
        cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
        firma = cur.fetchone()["firma"]
        audit(cur, user, "shop_bestellung", kid, {"ref": alt["ref"], "status": data.status})
    if data.status == "storniert" and alt["status"] != "storniert" and alt["gutschein_id"] and alt["gutschein_cent"]:     # Gutschein-Guthaben zurückbuchen (Gutscheine sind nur intern schreibbar)
        with tx("system") as cur:
            cur.execute("UPDATE website_gutscheine SET eingeloest = greatest(0, eingeloest - %s) WHERE id=%s AND kunden_id=%s", (alt["gutschein_cent"] / 100, alt["gutschein_id"], kid))
    gesendet = False
    if data.mail and data.status != alt["status"]:
        m = shop.status_mail(data.status, dict(neu), firma)
        if m:
            ok, _via = sd.kundenmail(kid, neu["email"], m[0], m[1], art="bestellung")
            gesendet = ok
            if not ok:
                raise HTTPException(502, "Der Status ist gespeichert, aber die Mail an die Kundin oder den Kunden ging nicht raus. Bitte per Hand melden.")
    return {"ok": True, "mail": gesendet}
