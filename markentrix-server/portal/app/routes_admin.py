from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors, sql
from pydantic import BaseModel, Field

from . import berichte as bericht_modul, config, jobs, onboarding
from fastapi.responses import Response
from .db import tx
from .publish import DOMAIN_RE
from . import zugang
from . import routes_avv as avv_modul
from .routes_aufgaben import kennzahlen_laden
from .security import EMAIL_RE, audit, require_admin

router = APIRouter(prefix="/api/admin")

KUNDEN_STATUS = ("onboarding", "aktiv", "pausiert", "gekuendigt", "beendet")

# Tabellen, die der Admin pro Kunde einsehen und (teils) anlegen darf. Spalten sind fest vorgegeben.
DATEN = {
    "anfragen": {"lesen": "id, name, kontakt, nachricht, quelle, status, erstellt_am", "order": "erstellt_am DESC", "neu": ["name", "kontakt", "nachricht", "quelle", "status"]},
    "termine": {"lesen": "id, titel, beginn, ende, kontakt_name, status, notiz", "order": "beginn DESC", "neu": ["titel", "beginn", "ende", "kontakt_name", "status", "notiz"]},
    "kontakte": {"lesen": "id, name, firma, email, telefon, notiz", "order": "lower(name)", "neu": ["name", "firma", "email", "telefon", "notiz"]},
    "angebote": {"lesen": "id, nummer, titel, betrag_cent, status, gueltig_bis, erstellt_am", "order": "erstellt_am DESC", "neu": ["nummer", "titel", "betrag_cent", "status", "gueltig_bis"]},
    "vertraege": {"lesen": "id, titel, beginn, ende, status, unterschrieben_am", "order": "erstellt_am DESC", "neu": ["titel", "beginn", "ende", "status"]},
    "projekte": {"lesen": "id, titel, art, status, url, beschreibung", "order": "erstellt_am DESC", "neu": ["titel", "art", "status", "url", "beschreibung"]},
    "berichte": {"lesen": "id, titel, art, zeitraum_von, zeitraum_bis, erstellt_am", "order": "erstellt_am DESC", "neu": ["titel", "art", "zeitraum_von", "zeitraum_bis"]},
    "wochenangebote_uploads": {"lesen": "id, dateiname, mime, groesse, status, gueltig_von, gueltig_bis, fehlertext, erstellt_am, veroeffentlicht_am", "order": "erstellt_am DESC", "neu": []},
    "chat_verlauf": {"lesen": "id, absender, text, erstellt_am", "order": "id DESC", "neu": []},
    "nachrichten": {"lesen": "id, kanal, richtung, absender, betreff, text, zeit", "order": "zeit DESC", "neu": []},
}


def pflicht(cur, kid):
    cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
    if not cur.fetchone():
        raise HTTPException(404, "Kunde nicht gefunden.")


# ---------------------------------------------------------------- Übersicht und Katalog
@router.get("/uebersicht")
def uebersicht(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT status, count(*) AS n FROM kunden GROUP BY status")
        status = {r["status"]: r["n"] for r in cur.fetchall()}
        cur.execute("SELECT coalesce(sum(b.monatlich_cent - b.rabatt_cent),0) AS cent FROM buchungen b JOIN kunden k ON k.id=b.kunden_id WHERE b.status IN ('aktiv','in_einrichtung','beauftragt') AND b.monatlich_cent IS NOT NULL AND NOT k.referenzkunde")
        mrr = cur.fetchone()["cent"]
        cur.execute("SELECT count(*) AS n FROM kunden WHERE referenzkunde")
        referenz = cur.fetchone()["n"]
        cur.execute("""SELECT coalesce(sum(brutto_cent) FILTER (WHERE status IN ('gestellt','versendet')),0) AS offen,
                              count(*) FILTER (WHERE status IN ('gestellt','versendet') AND faellig_am < current_date) AS ueberfaellig
                       FROM belege WHERE art='rechnung'""")
        rechn = cur.fetchone()
        cur.execute("SELECT count(*) AS n FROM anfragen WHERE status='neu'")
        neu = cur.fetchone()["n"]
        cur.execute("SELECT count(*) AS n FROM wochenangebote_uploads WHERE erstellt_am > now() - interval '7 days'")
        uploads = cur.fetchone()["n"]
        cur.execute("SELECT count(*) AS n FROM freigaben WHERE status='offen'")
        freigaben = cur.fetchone()["n"]
        zus = kennzahlen_laden(cur)
        cur.execute("SELECT zeit, aktion, details, kunden_id FROM audit_log ORDER BY id DESC LIMIT 12")
        letzte = cur.fetchall()
        avv_fehlt = avv_modul.fehlende(cur)
    return {"avv_fehlt": avv_fehlt, "kunden_status": status, "monatlich_cent": int(mrr), "referenzkunden": referenz, "rechnungen_offen_cent": int(rechn["offen"]), "rechnungen_ueberfaellig": rechn["ueberfaellig"], "neue_anfragen": neu, "uploads_7d": uploads, "offene_freigaben": freigaben, "letzte_aktionen": letzte, "zusammenarbeit": zus}


@router.get("/katalog")
def katalog(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT * FROM v_preise_aktuell ORDER BY kategorie, code")
        preise = cur.fetchall()
        cur.execute("SELECT code, name, beschreibung, art FROM module ORDER BY art DESC, sortierung")
        module = cur.fetchall()
        cur.execute("SELECT schluessel, wert_text, wert_zahl, beschreibung FROM konditionen ORDER BY schluessel")
        konditionen = cur.fetchall()
    return {"produkte": preise, "module": module, "konditionen": konditionen}


@router.get("/audit")
def audit_liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT a.id, a.zeit, a.aktion, a.details, k.kundennummer, b.email
                       FROM audit_log a LEFT JOIN kunden k ON k.id=a.kunden_id LEFT JOIN benutzer b ON b.id=a.benutzer_id
                       ORDER BY a.id DESC LIMIT 200""")
        return cur.fetchall()


# ---------------------------------------------------------------- Kunden
class KundeIn(BaseModel):
    firma: str = Field(min_length=1, max_length=200)
    rechtsform: str | None = Field(default=None, max_length=60)
    ansprechpartner: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    telefon: str | None = Field(default=None, max_length=60)
    branche: str | None = Field(default=None, max_length=120)
    strasse: str | None = Field(default=None, max_length=200)
    plz: str | None = Field(default=None, max_length=10)
    ort: str | None = Field(default=None, max_length=120)
    domain: str | None = Field(default=None, max_length=253)
    paket_code: str | None = None
    notizen: str | None = Field(default=None, max_length=4000)
    einladen: bool = False
    referenzkunde: bool = False
    referenz_leistung: str | None = Field(default=None, max_length=1000)
    referenz_nennen_erlaubt: bool = False


class KundePatch(BaseModel):
    firma: str | None = Field(default=None, max_length=200)
    rechtsform: str | None = None
    ansprechpartner: str | None = None
    email: str | None = None
    telefon: str | None = None
    branche: str | None = None
    strasse: str | None = None
    plz: str | None = None
    ort: str | None = None
    domain: str | None = None
    paket_code: str | None = None
    notizen: str | None = None
    referenzkunde: bool | None = None
    referenz_leistung: str | None = Field(default=None, max_length=1000)
    referenz_nennen_erlaubt: bool | None = None
    standardmodule_anwenden: bool = False


def standardmodule(cur, kid, paket):
    if paket:
        cur.execute("""INSERT INTO kunden_module (kunden_id, modul_code, aktiv)
                       SELECT %s, modul_code, true FROM produkt_module WHERE produkt_code=%s
                       ON CONFLICT (kunden_id, modul_code) DO UPDATE SET aktiv=true, geaendert_am=now()""", (kid, paket))


def einladung_erzeugen(cur, kid, email, name=None):
    return zugang.link_erzeugen(cur, email, name, "kunde", kunden_id=kid)


@router.get("/kunden")
def kunden_liste(q: str = "", user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT k.id, k.kundennummer, k.firma, k.ansprechpartner, k.email, k.domain, k.status, k.referenzkunde, p.name AS paket, k.erstellt_am,
                              (SELECT count(*) FROM kunden_module km WHERE km.kunden_id=k.id AND km.aktiv) AS module_aktiv,
                              (SELECT coalesce(json_agg(json_build_object('code', m.code, 'name', m.name, 'art', m.art, 'aktiv', coalesce(km.aktiv, false)) ORDER BY m.art, m.sortierung), '[]'::json)
                                 FROM module m LEFT JOIN kunden_module km ON km.modul_code=m.code AND km.kunden_id=k.id) AS module,
                              (SELECT count(*) FROM benutzer b WHERE b.kunden_id=k.id AND b.passwort_hash IS NOT NULL) AS zugang_aktiv,
                              EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL) AS avv_ok
                       FROM kunden k LEFT JOIN produkte p ON p.code=k.paket_code
                       WHERE %s = '' OR k.firma ILIKE %s OR k.kundennummer ILIKE %s OR coalesce(k.email,'') ILIKE %s
                       ORDER BY k.kundennummer DESC LIMIT 500""", (q, f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = cur.fetchall()
        for r in rows:   # Fortschritt der Einrichtung nur für Kunden im Onboarding
            if r["status"] == "onboarding":
                punkte = onboarding.lesen(cur, r["id"])
                r["onboarding"] = {"fertig": sum(1 for p in punkte if p["fertig"]), "gesamt": len(punkte)}
        return rows


@router.post("/kunden")
def kunde_neu(data: KundeIn, user: dict = Depends(require_admin)):
    if data.email and not EMAIL_RE.match(data.email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if data.domain and not DOMAIN_RE.match(data.domain.strip().lower()):
        raise HTTPException(400, "Die Domain ist ungültig (zum Beispiel firma.de).")
    if data.einladen and not data.email:
        raise HTTPException(400, "Zum Einladen wird eine E-Mail-Adresse gebraucht.")
    with tx("admin") as cur:
        try:
            cur.execute("""INSERT INTO kunden (firma, rechtsform, ansprechpartner, email, telefon, branche, strasse, plz, ort, domain, paket_code, notizen,
                                               referenzkunde, referenz_leistung, referenz_nennen_erlaubt)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id, kundennummer""",
                        (data.firma.strip(), data.rechtsform, data.ansprechpartner, data.email and data.email.strip(), data.telefon, data.branche,
                         data.strasse, data.plz, data.ort, data.domain and data.domain.strip().lower(), data.paket_code or None, data.notizen,
                         data.referenzkunde, data.referenz_leistung, data.referenz_nennen_erlaubt))
        except errors.ForeignKeyViolation:
            raise HTTPException(400, "Unbekanntes Paket.")
        k = cur.fetchone()
        standardmodule(cur, k["id"], data.paket_code)
        onboarding.anlegen(cur, k["id"])
        link = einladung_erzeugen(cur, k["id"], data.email, data.ansprechpartner) if data.einladen else None
        audit(cur, user, "kunde_angelegt", k["id"], {"kundennummer": k["kundennummer"]})
    mail = zugang.per_mail(data.email, data.ansprechpartner, link, "kunde") if link else None
    return {"id": k["id"], "kundennummer": k["kundennummer"], "einladungslink": link, "mail": mail}


@router.get("/kunden/{kid}")
def kunde_detail(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT k.*, p.name AS paket FROM kunden k LEFT JOIN produkte p ON p.code=k.paket_code WHERE k.id=%s", (kid,))
        k = cur.fetchone()
        if not k:
            raise HTTPException(404, "Kunde nicht gefunden.")
        k["logo_vorhanden"] = k.pop("logo", None) is not None
        cur.execute("""SELECT m.code, m.name, m.beschreibung, m.art, coalesce(km.aktiv,false) AS aktiv
                       FROM module m LEFT JOIN kunden_module km ON km.modul_code=m.code AND km.kunden_id=%s ORDER BY m.art, m.sortierung""", (kid,))
        module = cur.fetchall()
        cur.execute("SELECT id, email, name, aktiv, letzter_login, totp_aktiv, kunden_rolle, passwort_hash IS NOT NULL AS hat_passwort, einladung_ablauf FROM benutzer WHERE kunden_id=%s ORDER BY erstellt_am", (kid,))
        benutzer = cur.fetchall()
        cur.execute("""SELECT b.id, b.produkt_code, p.name, b.einrichtung_cent, b.monatlich_cent, b.projekt_cent, b.rabatt_cent, b.rabatt_grund, b.beginn,
                              b.mindestlaufzeit_ende, b.ende, b.status, b.standort, b.notiz
                       FROM buchungen b JOIN produkte p ON p.code=b.produkt_code WHERE b.kunden_id=%s ORDER BY b.erstellt_am DESC""", (kid,))
        buchungen = cur.fetchall()
        cur.execute("SELECT id, domain, art, status, sprachen, letzte_veroeffentlichung FROM websites WHERE kunden_id=%s ORDER BY erstellt_am", (kid,))
        websites = cur.fetchall()
        zaehler = {}
        for t in ("anfragen", "termine", "kontakte", "angebote", "vertraege", "projekte", "berichte", "wochenangebote_uploads"):
            cur.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE kunden_id=%s").format(sql.Identifier(t)), (kid,))
            zaehler[t] = cur.fetchone()["n"]
    return {"kunde": k, "module": module, "benutzer": benutzer, "buchungen": buchungen, "websites": websites, "zaehler": zaehler}


@router.patch("/kunden/{kid}")
def kunde_aendern(kid: str, data: KundePatch, user: dict = Depends(require_admin)):
    felder = {k: v for k, v in data.model_dump(exclude={"standardmodule_anwenden"}).items() if v is not None}
    if "domain" in felder:
        felder["domain"] = felder["domain"].strip().lower()
        if felder["domain"] and not DOMAIN_RE.match(felder["domain"]):
            raise HTTPException(400, "Die Domain ist ungültig.")
    if "email" in felder and felder["email"] and not EMAIL_RE.match(felder["email"].strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    if not felder:
        return {"ok": True}
    with tx("admin") as cur:
        pflicht(cur, kid)
        teile = sql.SQL(", ").join(sql.SQL("{}=%s").format(sql.Identifier(k)) for k in felder)
        try:
            cur.execute(sql.SQL("UPDATE kunden SET {} WHERE id=%s").format(teile), (*felder.values(), kid))
        except errors.ForeignKeyViolation:
            raise HTTPException(400, "Unbekanntes Paket.")
        if data.standardmodule_anwenden and felder.get("paket_code"):
            standardmodule(cur, kid, felder["paket_code"])
        audit(cur, user, "kunde_geaendert", kid, {"felder": list(felder)})
    return {"ok": True}


class StatusIn(BaseModel):
    status: str


@router.post("/kunden/{kid}/status")
def kunde_status(kid: str, data: StatusIn, user: dict = Depends(require_admin)):
    if data.status not in KUNDEN_STATUS:
        raise HTTPException(400, "Unbekannter Status.")
    with tx("admin") as cur:
        pflicht(cur, kid)
        cur.execute("UPDATE kunden SET status=%s WHERE id=%s", (data.status, kid))
        # Pausiert oder beendet: Zugänge sperren, bei aktiv wieder freigeben
        cur.execute("UPDATE benutzer SET aktiv=%s WHERE kunden_id=%s", (data.status in ("onboarding", "aktiv"), kid))
        if data.status not in ("onboarding", "aktiv"):
            cur.execute("DELETE FROM sitzungen WHERE benutzer_id IN (SELECT id FROM benutzer WHERE kunden_id=%s)", (kid,))
        audit(cur, user, "kunde_status", kid, {"status": data.status})
    return {"ok": True}


class ModulIn(BaseModel):
    aktiv: bool


@router.put("/kunden/{kid}/module/{code}")
def modul_schalten(kid: str, code: str, data: ModulIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        pflicht(cur, kid)
        cur.execute("SELECT 1 FROM module WHERE code=%s", (code,))
        if not cur.fetchone():
            raise HTTPException(404, "Unbekanntes Modul.")
        cur.execute("""INSERT INTO kunden_module (kunden_id, modul_code, aktiv) VALUES (%s,%s,%s)
                       ON CONFLICT (kunden_id, modul_code) DO UPDATE SET aktiv=EXCLUDED.aktiv, geaendert_am=now()""", (kid, code, data.aktiv))
        audit(cur, user, "modul_geschaltet", kid, {"modul": code, "aktiv": data.aktiv})
    return {"ok": True}


class EinladungIn(BaseModel):
    email: str
    name: str | None = Field(default=None, max_length=200)
    per_mail: bool = True


@router.post("/kunden/{kid}/einladung")
def einladung(kid: str, data: EinladungIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        pflicht(cur, kid)
        link = einladung_erzeugen(cur, kid, data.email, data.name)
        audit(cur, user, "einladung_erzeugt", kid)
    mail = zugang.per_mail(data.email, data.name, link, "kunde") if data.per_mail else None
    return {"einladungslink": link, "gueltig_tage": config.INVITE_DAYS, "mail": mail}


@router.post("/benutzer/{bid}/aktiv")
def benutzer_aktiv(bid: str, data: ModulIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE benutzer SET aktiv=%s WHERE id=%s AND rolle='kunde' RETURNING kunden_id", (data.aktiv, bid))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Zugang nicht gefunden.")
        if not data.aktiv:
            cur.execute("DELETE FROM sitzungen WHERE benutzer_id=%s", (bid,))
        audit(cur, user, "zugang_aktiv", r["kunden_id"], {"aktiv": data.aktiv})
    return {"ok": True}


# ---------------------------------------------------------------- Buchungen
class BuchungIn(BaseModel):
    produkt_code: str
    rabatt_cent: int = Field(default=0, ge=0)
    rabatt_grund: str | None = Field(default=None, max_length=200)
    beginn: date | None = None
    standort: str | None = Field(default=None, max_length=200)
    notiz: str | None = Field(default=None, max_length=1000)


@router.post("/kunden/{kid}/buchungen")
def buchung_neu(kid: str, data: BuchungIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (kid,))
        kr = cur.fetchone()
        if not kr:
            raise HTTPException(404, "Kunde nicht gefunden.")
        referenz = kr["referenzkunde"]
        cur.execute("""SELECT pp.id AS preis_id, pp.einrichtung_cent, pp.monatlich_cent, pp.projekt_cent, p.laufzeit_monate, p.nur_auf_anfrage
                       FROM produkte p LEFT JOIN LATERAL (SELECT * FROM produkt_preise x WHERE x.produkt_code=p.code AND x.gueltig_ab<=current_date ORDER BY gueltig_ab DESC LIMIT 1) pp ON true
                       WHERE p.code=%s AND p.aktiv""", (data.produkt_code,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Unbekanntes Produkt.")
        if p["preis_id"] is None and not p["nur_auf_anfrage"]:
            raise HTTPException(400, "Für dieses Produkt ist kein Preis hinterlegt.")
        beginn = data.beginn
        if referenz:  # Referenzkunde: Preise auf 0, kein Rabattgrund nötig
            p = {**p, "einrichtung_cent": 0, "monatlich_cent": 0, "projekt_cent": 0}
            data.rabatt_cent = 0
            data.rabatt_grund = "Referenzkunde"
        cur.execute("""INSERT INTO buchungen (kunden_id, produkt_code, preis_id, einrichtung_cent, monatlich_cent, projekt_cent, rabatt_cent, rabatt_grund, beginn,
                                             mindestlaufzeit_ende, status, standort, notiz)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, CASE WHEN %s::date IS NOT NULL AND %s::int IS NOT NULL THEN (%s::date + make_interval(months=>%s::int))::date END,
                               'beauftragt',%s,%s) RETURNING id""",
                    (kid, data.produkt_code, p["preis_id"], p["einrichtung_cent"], p["monatlich_cent"], p["projekt_cent"], data.rabatt_cent, data.rabatt_grund, beginn,
                     beginn, p["laufzeit_monate"], beginn, p["laufzeit_monate"], data.standort, data.notiz))
        b = cur.fetchone()
        cur.execute("""INSERT INTO kunden_module (kunden_id, modul_code, aktiv) SELECT %s, modul_code, true FROM produkt_module WHERE produkt_code=%s
                       ON CONFLICT (kunden_id, modul_code) DO UPDATE SET aktiv=true, geaendert_am=now()""", (kid, data.produkt_code))
        audit(cur, user, "buchung_angelegt", kid, {"produkt": data.produkt_code})
    return b


class BuchungPatch(BaseModel):
    status: str | None = None
    ende: date | None = None


@router.patch("/buchungen/{bid}")
def buchung_aendern(bid: str, data: BuchungPatch, user: dict = Depends(require_admin)):
    if data.status and data.status not in ("angefragt", "beauftragt", "in_einrichtung", "aktiv", "pausiert", "gekuendigt", "beendet"):
        raise HTTPException(400, "Unbekannter Status.")
    with tx("admin") as cur:
        cur.execute("UPDATE buchungen SET status=coalesce(%s,status), ende=coalesce(%s,ende) WHERE id=%s RETURNING kunden_id", (data.status, data.ende, bid))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Buchung nicht gefunden.")
        audit(cur, user, "buchung_geaendert", r["kunden_id"], {"status": data.status})
    return {"ok": True}


# ---------------------------------------------------------------- Websites
class WebsiteIn(BaseModel):
    domain: str
    art: str = "live"


@router.post("/kunden/{kid}/websites")
def website_neu(kid: str, data: WebsiteIn, user: dict = Depends(require_admin)):
    d = data.domain.strip().lower()
    if not DOMAIN_RE.match(d):
        raise HTTPException(400, "Die Domain ist ungültig (zum Beispiel firma.de).")
    if data.art not in ("live", "demo"):
        raise HTTPException(400, "Art muss live oder demo sein.")
    with tx("admin") as cur:
        pflicht(cur, kid)
        try:
            cur.execute("INSERT INTO websites (kunden_id, domain, art, status, verzeichnis) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                        (kid, d, data.art, "live" if data.art == "live" else "demo", str(config.SITES_LIVE / d)))
        except errors.UniqueViolation:
            raise HTTPException(409, "Diese Domain ist schon angelegt.")
        r = cur.fetchone()
        audit(cur, user, "website_angelegt", kid, {"domain": d})
    return r


# ---------------------------------------------------------------- Kundendaten ansehen und anlegen
@router.get("/kunden/{kid}/daten/{tabelle}")
def daten_lesen(kid: str, tabelle: str, user: dict = Depends(require_admin)):
    if tabelle not in DATEN:
        raise HTTPException(404, "Unbekannte Tabelle.")
    d = DATEN[tabelle]
    with tx("admin") as cur:
        pflicht(cur, kid)
        cur.execute(sql.SQL("SELECT {} FROM {} WHERE kunden_id=%s ORDER BY {} LIMIT 200").format(sql.SQL(d["lesen"]), sql.Identifier(tabelle), sql.SQL(d["order"])), (kid,))
        return cur.fetchall()


@router.post("/kunden/{kid}/daten/{tabelle}")
def daten_anlegen(kid: str, tabelle: str, data: dict, user: dict = Depends(require_admin)):
    if tabelle not in DATEN or not DATEN[tabelle]["neu"]:
        raise HTTPException(404, "Hier kann nichts angelegt werden.")
    erlaubt = DATEN[tabelle]["neu"]
    werte = {k: (v if v != "" else None) for k, v in data.items() if k in erlaubt}
    if not werte:
        raise HTTPException(400, "Keine gültigen Felder.")
    with tx("admin") as cur:
        pflicht(cur, kid)
        spalten = sql.SQL(", ").join(sql.Identifier(k) for k in ["kunden_id", *werte])
        platz = sql.SQL(", ").join(sql.Placeholder() for _ in ["kunden_id", *werte])
        try:
            cur.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(sql.Identifier(tabelle), spalten, platz), (kid, *werte.values()))
        except (errors.CheckViolation, errors.InvalidTextRepresentation, errors.InvalidDatetimeFormat, errors.NotNullViolation, errors.DatatypeMismatch):
            raise HTTPException(400, "Ein Feld hat einen ungültigen oder fehlenden Wert.")
        r = cur.fetchone()
        audit(cur, user, "daten_angelegt", kid, {"tabelle": tabelle})
    return r


@router.delete("/kunden/{kid}/daten/{tabelle}/{rid}")
def daten_loeschen(kid: str, tabelle: str, rid: str, user: dict = Depends(require_admin)):
    if tabelle not in DATEN or not DATEN[tabelle]["neu"]:
        raise HTTPException(404, "Hier kann nichts gelöscht werden.")
    with tx("admin") as cur:
        cur.execute(sql.SQL("DELETE FROM {} WHERE id=%s AND kunden_id=%s").format(sql.Identifier(tabelle)), (rid, kid))
        audit(cur, user, "daten_geloescht", kid, {"tabelle": tabelle})
    return {"ok": True}


# ---------------------------------------------------------------- Berichte
@router.get("/kunden/{kid}/berichte")
def berichte_liste(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        pflicht(cur, kid)
        cur.execute("SELECT id, titel, zeitraum_von, versendet_am, erstellt_am FROM berichte WHERE kunden_id=%s AND art='monatsbericht' ORDER BY zeitraum_von DESC LIMIT 36", (kid,))
        return cur.fetchall()


class BerichtIn(BaseModel):
    monat: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    senden: bool = False


@router.post("/kunden/{kid}/bericht")
def bericht_erstellen(kid: str, data: BerichtIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        pflicht(cur, kid)
    monat = date.fromisoformat(data.monat + "-01")
    if monat >= date.today().replace(day=1):
        raise HTTPException(400, "Berichte gibt es nur für abgeschlossene Monate.")
    r = jobs.bericht_senden(kid, monat, mail=data.senden)
    with tx("admin") as cur:
        audit(cur, user, "bericht_erstellt", kid, {"monat": data.monat, "gesendet": r["gesendet"]})
    return r


@router.get("/berichte/{bid}")
def bericht_texte(bid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, titel, daten, einordnung, naechste_schritte, einordnung_geaendert_am FROM berichte WHERE id=%s AND art='monatsbericht'", (bid,))
            b = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Bericht nicht gefunden.")
    if not b:
        raise HTTPException(404, "Bericht nicht gefunden.")
    auto_t, auto_s = bericht_modul.einordnung_auto(b["daten"])
    text, schritte = bericht_modul.texte(b)
    return {"id": b["id"], "titel": b["titel"], "einordnung": text, "schritte": schritte, "angepasst": bool(b["einordnung_geaendert_am"]),
            "auto_einordnung": auto_t, "auto_schritte": auto_s}


class BerichtTexteIn(BaseModel):
    einordnung: str = Field(default="", max_length=3000)
    schritte: list[str] = Field(default_factory=list, max_length=8)


@router.put("/berichte/{bid}")
def bericht_texte_speichern(bid: str, data: BerichtTexteIn, user: dict = Depends(require_admin)):
    schritte = "\n".join(z.strip()[:400] for z in data.schritte if z.strip())
    try:
        with tx("admin") as cur:
            cur.execute("""UPDATE berichte SET einordnung=%s, naechste_schritte=%s, einordnung_geaendert_am=CASE WHEN %s='' AND %s='' THEN NULL ELSE now() END
                           WHERE id=%s AND art='monatsbericht' RETURNING kunden_id""", (data.einordnung.strip() or None, schritte or None, data.einordnung.strip(), schritte, bid))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Bericht nicht gefunden.")
            audit(cur, user, "bericht_texte", r["kunden_id"], {"id": bid})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Bericht nicht gefunden.")
    return {"ok": True}


@router.post("/berichte/{bid}/senden")
def bericht_erneut_senden(bid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT kunden_id, zeitraum_von FROM berichte WHERE id=%s AND art='monatsbericht'", (bid,))
            b = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Bericht nicht gefunden.")
    if not b:
        raise HTTPException(404, "Bericht nicht gefunden.")
    r = jobs.bericht_senden(b["kunden_id"], b["zeitraum_von"], mail=True)
    with tx("admin") as cur:
        audit(cur, user, "bericht_gesendet", b["kunden_id"], {"id": bid, "gesendet": r["gesendet"]})
    return r


@router.post("/berichte/{bid}/ki-entwurf")
def bericht_ki_entwurf(bid: str, user: dict = Depends(require_admin)):
    """KI-Entwurf für Einordnung und nächste Schritte. Wird nur vorgeschlagen, gespeichert wird erst nach deiner Freigabe."""
    from . import einstellungen, ki
    try:
        with tx("admin") as cur:
            cur.execute("SELECT b.daten, k.firma, k.branche FROM berichte b JOIN kunden k ON k.id=b.kunden_id WHERE b.id=%s AND b.art='monatsbericht'", (bid,))
            b = cur.fetchone()
            cfg = einstellungen.lesen(cur, "ki") or {}
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Bericht nicht gefunden.")
    if not b:
        raise HTTPException(404, "Bericht nicht gefunden.")
    if not cfg.get("api_key"):
        raise HTTPException(400, "Für den KI-Entwurf fehlt der Schlüssel unter Einstellungen → KI.")
    try:
        ergebnis = ki.bericht_entwurf(cfg["api_key"], cfg.get("modell") or ki.STANDARD_MODELL, b["firma"], b["branche"], b["daten"])
    except Exception:
        raise HTTPException(502, "Der KI-Dienst hat nicht geantwortet. Bitte später erneut versuchen.")
    return ergebnis


@router.get("/berichte/{bid}/pdf")
def bericht_pdf(bid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            daten, name = bericht_modul.pdf_erzeugen(cur, bid)
    except (LookupError, errors.InvalidTextRepresentation):
        raise HTTPException(404, "Bericht nicht gefunden.")
    return Response(daten, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
