"""Vertriebler senden Angebote zu den offiziellen Katalogpreisen. Preisänderungen laufen über eine Preisanfrage: Der Admin gibt sie frei oder lehnt ab,
erst mit Freigabe geht das Angebot mit dem freigegebenen Preis raus. Die Preise kommen immer vom Server, nie vom Browser des Vertrieblers.
Ein- und ausgeschaltet wird das unter Admin → Leads (Standard aus)."""
import json
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import config, push, zuweisung
from .db import tx
from .routes_leadangebot import AngebotIn, SendenIn, BLOCKIERT, EMAIL, _vorname_gruss, entwurf as lead_entwurf, senden as lead_senden
from .routes_vertrieb import eigener_lead
from .security import audit, rate_limit, require_admin, require_vertrieb

router = APIRouter(prefix="/api")
FELDER = ("einrichtung_cent", "monatlich_cent", "projekt_cent")
MAX_PAKETE = 4


def erlaubt(cur) -> bool:
    return zuweisung.einstellung(cur)["vertrieb_angebote"]


def _pakete(cur) -> dict:
    cur.execute("SELECT v.code, v.name, v.einrichtung_cent, v.monatlich_cent, v.projekt_cent, v.ab_preis, v.nur_auf_anfrage, p.leistungen FROM v_preise_aktuell v JOIN produkte p ON p.code = v.code")
    return {r["code"]: r for r in cur.fetchall()}


def _preise(p: dict, override: dict | None = None) -> dict:
    return {f: int((override or {}).get(f) if (override or {}).get(f) is not None else (p[f] or 0)) for f in FELDER}


def verkaufbar(p: dict) -> str:
    """Leer = darf der Vertriebler zum Katalogpreis senden, sonst der Grund."""
    if p["nur_auf_anfrage"]:
        return "Nur auf Anfrage: bitte eine Angebotsanfrage stellen."
    if p["ab_preis"]:
        return "„Ab“-Preis: der Betrag muss geprüft werden, bitte eine Preisanfrage oder Angebotsanfrage stellen."
    if not any(p[f] for f in FELDER):
        return "Für dieses Paket ist noch kein Preis hinterlegt."
    return ""


def positionen(p: dict, preise: dict) -> list:
    out = []
    if preise["einrichtung_cent"]:
        out.append({"text": "Einrichtung " + p["name"], "menge": 1, "einheit": "", "preis_cent": preise["einrichtung_cent"]})
    if preise["monatlich_cent"]:
        out.append({"text": p["name"] + " – monatlich", "menge": 1, "einheit": "Monat", "preis_cent": preise["monatlich_cent"]})
    if preise["projekt_cent"]:
        out.append({"text": p["name"] + " – Projektpreis", "menge": 1, "einheit": "", "preis_cent": preise["projekt_cent"]})
    return out


def _leistungen(p: dict, mit_titel: bool) -> list:
    l = p["leistungen"] if isinstance(p["leistungen"], list) else []
    return ([f"## {p['name']}"] if mit_titel and l else []) + [str(x) for x in l]


def senden_mit_preisen(lid: str, wahl: list, gueltig_tage: int, user: dict) -> dict:
    """Legt das Angebot an und sendet es. wahl = [(Paketzeile, Preise)]. Die Preise stammen vom Aufrufer, der sie aus dem Katalog bzw. der Freigabe ableitet."""
    pos, leist = [], []
    for p, preise in wahl:
        pos += positionen(p, preise)
        leist += _leistungen(p, len(wahl) > 1)
    with tx("admin") as cur:
        cur.execute("SELECT * FROM leads WHERE id=%s", (lid,))
        l = cur.fetchone()
    namen = ", ".join(p["name"] for p, _ in wahl)
    e = lead_entwurf(lid, AngebotIn(betreff=f"Ihr Angebot für {l['firma']}", einleitung=_vorname_gruss(l) + f"\n\nvielen Dank für Ihr Interesse. Hier ist unser Angebot für {l['firma']}.",
                                    schluss="Bei Fragen melden Sie sich gern. Wir freuen uns auf die Zusammenarbeit.", positionen=pos, leistungen=leist), user)
    r = lead_senden(lid, str(e["id"]), SendenIn(gueltig_tage=gueltig_tage), user)
    return {**r, "beleg_id": str(e["id"]), "pakete": namen}


def _lead_pruefen(cur, lid: str, user: dict) -> dict:
    l = eigener_lead(cur, lid, user["vertriebspartner_id"])
    if l["status"] in BLOCKIERT or l["status"] == "gewonnen":
        raise HTTPException(400, "Für diesen Lead kann kein Angebot gesendet werden (gesperrt, ohne Einwilligung, verloren oder schon Kunde).")
    return l


def _ein(cur):
    if not erlaubt(cur):
        raise HTTPException(403, "Angebote sendet bei dir aktuell Markentrix. Bitte eine Angebotsanfrage stellen.")


# ---------------------------------------------------------------- Vertriebler
@router.get("/vertrieb/leads/{lid}/angebot-start")
def start(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if not erlaubt(cur):
            return {"erlaubt": False}
        pk = _pakete(cur)
        cur.execute("SELECT 1 FROM angebot_preisanfragen WHERE lead_id=%s AND status='offen'", (lid,))
        offen = bool(cur.fetchone())
    liste = [{"code": p["code"], "name": p["name"], "einrichtung_cent": p["einrichtung_cent"], "monatlich_cent": p["monatlich_cent"], "projekt_cent": p["projekt_cent"], "grund": verkaufbar(p)}
             for p in sorted(pk.values(), key=lambda x: x["name"])]
    gesperrt = l["status"] in BLOCKIERT or l["status"] == "gewonnen"
    return {"erlaubt": True, "pakete": liste, "email": l.get("email") or "", "lead_gesperrt": gesperrt, "preisanfrage_offen": offen}


class SendenVIn(BaseModel):
    paket_codes: list[str] = Field(min_length=1, max_length=MAX_PAKETE)
    gueltig_tage: int = Field(default=30, ge=7, le=60)


@router.post("/vertrieb/leads/{lid}/angebot-senden")
def vertriebler_sendet(lid: str, data: SendenVIn, user: dict = Depends(require_vertrieb)):
    rate_limit("vertrieblerangebot:" + str(user["id"]), 20, 3600)
    with tx("system") as cur:
        _ein(cur)
        l = _lead_pruefen(cur, lid, user)
        if not EMAIL.match((l.get("email") or "").strip()):
            raise HTTPException(400, "Beim Lead fehlt eine gültige E-Mail-Adresse.")
        pk = _pakete(cur)
        wahl = []
        for code in dict.fromkeys(data.paket_codes):
            p = pk.get(code)
            if not p:
                raise HTTPException(400, "Unbekanntes Paket.")
            grund = verkaufbar(p)
            if grund:
                raise HTTPException(400, f"{p['name']}: {grund}")
            wahl.append((p, _preise(p)))
        cur.execute("SELECT name FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        pname = cur.fetchone()["name"]
    r = senden_mit_preisen(lid, wahl, data.gueltig_tage, user)
    with tx("admin") as cur:
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)", (lid, f"Angebot {r['nummer']} ({r['pakete']}) von {pname} zu Katalogpreisen gesendet", user["email"]))
        audit(cur, user, "vertriebler_angebot", None, {"lead": lid, "nummer": r["nummer"], "pakete": r["pakete"], "gesendet": r["gesendet"]})
        ids = push.admins(cur)
    if r["gesendet"] and ids:
        push.senden(ids, "Angebot vom Vertriebler", f"{pname}: {l['firma']} ({r['pakete']})", "/admin#lead/" + lid, "angebotsstatus")
    return {"nummer": r["nummer"], "gesendet": r["gesendet"], "grund": r["grund"], "an": r["an"]}


class PreisanfrageIn(BaseModel):
    paket_code: str = Field(max_length=60)
    einrichtung_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    monatlich_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    projekt_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    nachlass_prozent: float | None = Field(default=None, gt=0, le=100)
    begruendung: str = Field(min_length=10, max_length=1000)


@router.post("/vertrieb/leads/{lid}/preisanfrage")
def preisanfrage(lid: str, data: PreisanfrageIn, user: dict = Depends(require_vertrieb)):
    rate_limit("preisanfrage:" + str(user["id"]), 20, 3600)
    with tx("system") as cur:
        _ein(cur)
        l = _lead_pruefen(cur, lid, user)
        cur.execute("SELECT 1 FROM angebot_preisanfragen WHERE lead_id=%s AND status='offen'", (lid,))
        if cur.fetchone():
            raise HTTPException(409, "Für diesen Lead wartet schon eine Preisanfrage auf Freigabe.")
        p = _pakete(cur).get(data.paket_code)
        if not p:
            raise HTTPException(400, "Unbekanntes Paket.")
        if p["nur_auf_anfrage"] or not any(p[f] for f in FELDER):
            raise HTTPException(400, "Für dieses Paket gibt es keinen Katalogpreis. Bitte eine Angebotsanfrage stellen.")
        katalog = _preise(p)
        if data.nachlass_prozent:
            faktor = (Decimal(100) - Decimal(str(data.nachlass_prozent))) / Decimal(100)
            wunsch = {f: int((Decimal(katalog[f]) * faktor).quantize(Decimal(1), ROUND_HALF_UP)) for f in FELDER}
        else:
            wunsch = _preise(p, {f: getattr(data, f) for f in FELDER})
        if wunsch == katalog:
            raise HTTPException(400, "Der gewünschte Preis entspricht dem Katalogpreis. Dann kannst du das Angebot direkt senden.")
        cur.execute("SELECT name FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        pname = cur.fetchone()["name"]
        cur.execute("""INSERT INTO angebot_preisanfragen (lead_id, vertriebspartner_id, paket_code, katalog, wunsch, nachlass_prozent, begruendung) VALUES (%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s) RETURNING id""",
                    (lid, user["vertriebspartner_id"], data.paket_code, json.dumps(katalog), json.dumps(wunsch), data.nachlass_prozent, data.begruendung.strip()))
        pid = cur.fetchone()["id"]
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)", (lid, f"Preisanfrage für {p['name']} gestellt (wartet auf Freigabe)", user["email"]))
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        a = cur.fetchone()
        cur.execute("INSERT INTO aufgaben (titel, beschreibung, zustaendig, faellig_am) VALUES (%s,%s,%s,current_date + 1)",
                    (f"Preisfreigabe prüfen: {l['firma']}"[:200], f"Vertriebler: {pname}\nPaket: {p['name']}\nBegründung: {data.begruendung.strip()}\n{config.BASE_URL}/admin#uebersicht", a and a["email"]))
        audit(cur, user, "preisanfrage", None, {"lead": lid, "paket": data.paket_code})
        ids = push.admins(cur)
    push.senden(ids, "Preisfreigabe nötig", f"{pname} möchte für {l['firma']} einen anderen Preis ({p['name']}).", "/admin#uebersicht", "preisanfrage")
    return {"id": str(pid)}


@router.get("/vertrieb/leads/{lid}/preisanfragen")
def preisanfragen_zum_lead(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        eigener_lead(cur, lid, user["vertriebspartner_id"])
        cur.execute("""SELECT a.id, a.status, a.katalog, a.wunsch, a.freigegeben, a.nachlass_prozent, a.begruendung, a.admin_notiz, a.erstellt_am, a.entschieden_am, p.name AS paket
                       FROM angebot_preisanfragen a LEFT JOIN produkte p ON p.code=a.paket_code WHERE a.lead_id=%s ORDER BY a.erstellt_am DESC LIMIT 20""", (lid,))
        return cur.fetchall()


# ---------------------------------------------------------------- Admin: Freigabe
@router.get("/admin/preisanfragen")
def admin_liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT a.id, a.lead_id, l.firma, l.email, a.status, a.katalog, a.wunsch, a.freigegeben, a.nachlass_prozent, a.begruendung, a.admin_notiz, a.erstellt_am, a.entschieden_am,
                              p.name AS paket, vp.name AS vertriebler
                       FROM angebot_preisanfragen a JOIN leads l ON l.id=a.lead_id LEFT JOIN produkte p ON p.code=a.paket_code LEFT JOIN vertriebspartner vp ON vp.id=a.vertriebspartner_id
                       WHERE a.status='offen' OR a.entschieden_am > now() - interval '14 days' ORDER BY (a.status='offen') DESC, a.erstellt_am DESC LIMIT 40""")
        return cur.fetchall()


class GenehmigenIn(BaseModel):
    einrichtung_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    monatlich_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    projekt_cent: int | None = Field(default=None, ge=0, le=100_000_000)
    notiz: str = Field(default="", max_length=500)


def _anfrage(cur, aid: str) -> dict:
    try:
        cur.execute("SELECT * FROM angebot_preisanfragen WHERE id=%s FOR UPDATE", (aid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Preisanfrage nicht gefunden.")
    a = cur.fetchone()
    if not a:
        raise HTTPException(404, "Preisanfrage nicht gefunden.")
    if a["status"] != "offen":
        raise HTTPException(409, "Diese Preisanfrage ist schon entschieden.")
    return a


@router.post("/admin/preisanfragen/{aid}/genehmigen")
def genehmigen(aid: str, data: GenehmigenIn, user: dict = Depends(require_admin)):
    """Gibt den Preis frei (Wunschpreis oder von dir geänderte Preise), legt das Angebot an und sendet es sofort an den Lead."""
    rate_limit("preisfreigabe:" + str(user["id"]), 30, 3600)
    with tx("admin") as cur:
        a = _anfrage(cur, aid)
        cur.execute("SELECT * FROM leads WHERE id=%s", (a["lead_id"],))
        l = cur.fetchone()
        if l["status"] in BLOCKIERT or l["status"] == "gewonnen":
            raise HTTPException(400, "Der Lead ist inzwischen gesperrt, verloren oder schon Kunde. Bitte ablehnen.")
        if not EMAIL.match((l.get("email") or "").strip()):
            raise HTTPException(400, "Beim Lead fehlt eine gültige E-Mail-Adresse. Bitte zuerst eintragen.")
        p = _pakete(cur).get(a["paket_code"])
        if not p:
            raise HTTPException(400, "Das Paket gibt es nicht mehr.")
        override = {f: getattr(data, f) for f in FELDER}
        preise = _preise(p, {f: (override[f] if override[f] is not None else a["wunsch"].get(f)) for f in FELDER})
        cur.execute("UPDATE angebot_preisanfragen SET status='genehmigt', freigegeben=%s::jsonb, admin_notiz=%s, entschieden_am=now(), entschieden_von=%s WHERE id=%s",
                    (json.dumps(preise), data.notiz.strip() or None, user["email"], aid))
    partner_user = {"id": user["id"], "email": user["email"], "vertriebspartner_id": a["vertriebspartner_id"]}
    r = senden_mit_preisen(str(a["lead_id"]), [(p, preise)], 30, partner_user)
    with tx("admin") as cur:
        cur.execute("UPDATE angebot_preisanfragen SET beleg_id=%s WHERE id=%s", (r["beleg_id"], aid))
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)",
                    (a["lead_id"], f"Preisanfrage genehmigt, Angebot {r['nummer']} gesendet" + (f" ({data.notiz.strip()})" if data.notiz.strip() else ""), user["email"]))
        audit(cur, user, "preisanfrage_genehmigt", None, {"lead": str(a["lead_id"]), "nummer": r["nummer"], "preise": preise, "gesendet": r["gesendet"]})
        ids = push.partner(cur, a["vertriebspartner_id"]) if a["vertriebspartner_id"] else []
    if ids:
        push.senden(ids, "Preisanfrage genehmigt", f"{l['firma']}: Das Angebot ist raus.", "/vertrieb#lead/" + str(a["lead_id"]), "angebotsstatus")
    return {"nummer": r["nummer"], "gesendet": r["gesendet"], "grund": r["grund"], "preise": preise}


class AblehnenIn(BaseModel):
    notiz: str = Field(default="", max_length=500)


@router.post("/admin/preisanfragen/{aid}/ablehnen")
def ablehnen(aid: str, data: AblehnenIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        a = _anfrage(cur, aid)
        cur.execute("UPDATE angebot_preisanfragen SET status='abgelehnt', admin_notiz=%s, entschieden_am=now(), entschieden_von=%s WHERE id=%s", (data.notiz.strip() or None, user["email"], aid))
        cur.execute("SELECT firma FROM leads WHERE id=%s", (a["lead_id"],))
        l = cur.fetchone()
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)", (a["lead_id"], "Preisanfrage abgelehnt" + (f": {data.notiz.strip()}" if data.notiz.strip() else ""), user["email"]))
        audit(cur, user, "preisanfrage_abgelehnt", None, {"lead": str(a["lead_id"])})
        ids = push.partner(cur, a["vertriebspartner_id"]) if a["vertriebspartner_id"] else []
    if ids:
        push.senden(ids, "Preisanfrage abgelehnt", f"{l['firma']}: Es gilt der Katalogpreis." + (f" {data.notiz.strip()}" if data.notiz.strip() else ""), "/vertrieb#lead/" + str(a["lead_id"]), "angebotsstatus")
    return {"ok": True}
