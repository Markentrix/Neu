"""Vertriebler-Werkzeuge: eigene Zahlen mit Wochenziel, Gesprächsleitfaden, Angebotsanfrage mit Status, Mail-Entwurf nach dem Gespräch."""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import config, einstellungen, leitfaden, push
from .db import tx
from .routes_vertrieb import eigener_lead
from .security import audit, rate_limit, require_admin, require_vertrieb

router = APIRouter(prefix="/api")

STATUS_TEXT = {"angefragt": "Angefragt", "in_pruefung": "In Prüfung", "angebot_raus": "Angebot ist raus", "angenommen": "Angenommen", "abgelehnt": "Abgelehnt"}


# ================================================================= Eigene Zahlen
@router.get("/vertrieb/zahlen")
def zahlen(user: dict = Depends(require_vertrieb)):
    pid = user["vertriebspartner_id"]
    with tx("system") as cur:
        cur.execute("SELECT wochenziel_anrufe FROM vertriebspartner WHERE id=%s", (pid,))
        ziel = cur.fetchone()["wochenziel_anrufe"]
        cur.execute("""SELECT
              count(*) FILTER (WHERE a.art='anruf' AND a.zeit >= date_trunc('week', now()))                                        AS anrufe_woche,
              count(*) FILTER (WHERE a.art='anruf' AND a.zeit >= date_trunc('week', now()) - interval '7 days' AND a.zeit < date_trunc('week', now())) AS anrufe_vorwoche,
              count(*) FILTER (WHERE a.art='anruf' AND a.inhalt LIKE 'Angerufen: erreicht%%' AND a.zeit >= date_trunc('week', now())) AS erreicht_woche,
              count(*) FILTER (WHERE a.art='termin' AND a.zeit >= date_trunc('week', now()))                                       AS termine_woche,
              count(*) FILTER (WHERE a.art='anruf' AND a.zeit >= date_trunc('month', now()))                                       AS anrufe_monat,
              count(*) FILTER (WHERE a.art='anruf' AND a.inhalt LIKE 'Angerufen: erreicht%%' AND a.zeit >= date_trunc('month', now())) AS erreicht_monat,
              count(*) FILTER (WHERE a.art='termin' AND a.zeit >= date_trunc('month', now()))                                      AS termine_monat,
              count(*) FILTER (WHERE a.art='anruf' AND a.zeit::date = current_date)                                                AS anrufe_heute
              FROM lead_aktivitaeten a JOIN leads l ON l.id=a.lead_id WHERE l.vertriebspartner_id=%s""", (pid,))
        z = cur.fetchone()
        cur.execute("""SELECT count(*) FILTER (WHERE erstellt_am >= date_trunc('week', now())) AS abschluesse_woche,
                              count(*) FILTER (WHERE erstellt_am >= date_trunc('month', now())) AS abschluesse_monat
                       FROM kunden WHERE vertriebspartner_id=%s""", (pid,))
        z.update(cur.fetchone())
        cur.execute("SELECT count(*) AS n FROM leads WHERE vertriebspartner_id=%s AND status='angebot'", (pid,))
        offene_angebote = cur.fetchone()["n"]
        cur.execute("""SELECT coalesce(sum(betrag_cent) FILTER (WHERE status IN ('berechnet','freigegeben')),0) AS offen_cent,
                              coalesce(sum(betrag_cent) FILTER (WHERE monat = date_trunc('month', current_date) AND status<>'storniert'),0) AS monat_cent
                       FROM provisionen WHERE vertriebspartner_id=%s""", (pid,))
        prov = cur.fetchone()
        cur.execute("""SELECT avg(s) AS schnitt FROM (SELECT sum(betrag_cent) AS s FROM provisionen WHERE vertriebspartner_id=%s AND art='laufend' AND status<>'storniert'
                       AND monat = (SELECT max(monat) FROM provisionen WHERE vertriebspartner_id=%s AND art='laufend') GROUP BY kunden_id) t""", (pid, pid))
        schnitt = cur.fetchone()["schnitt"]
    quote = lambda a, b: round(100 * a / b) if b else None   # noqa: E731
    z["wochenziel"] = ziel
    z["quote_erreicht"] = quote(z["erreicht_monat"], z["anrufe_monat"])
    z["quote_termin"] = quote(z["termine_monat"], z["erreicht_monat"])
    schnitt_cent = int(schnitt) if schnitt else None
    z["provision"] = {"offen_cent": int(prov["offen_cent"]), "monat_cent": int(prov["monat_cent"]), "offene_angebote": offene_angebote,
                      "schnitt_je_kunde_cent": schnitt_cent, "rechenbeispiel_cent": schnitt_cent * offene_angebote if schnitt_cent and offene_angebote else None}
    return z


class ZielIn(BaseModel):
    anrufe: int = Field(ge=1, le=500)


@router.put("/vertrieb/ziel")
def ziel_setzen(data: ZielIn, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("UPDATE vertriebspartner SET wochenziel_anrufe=%s WHERE id=%s", (data.anrufe, user["vertriebspartner_id"]))
    return {"ok": True}


# ================================================================= Gesprächsleitfaden
def _cfg(cur) -> dict:
    return leitfaden.zusammenfuehren(einstellungen.lesen(cur, "leitfaden") or None)


@router.get("/vertrieb/leitfaden")
def leitfaden_lesen(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        c = _cfg(cur)
    return {"abschnitte": c["abschnitte"], "einwaende": c["einwaende"], "branchen": c["branchen"]}


@router.get("/vertrieb/leads/{lid}/branchenhinweis")
def branchenhinweis(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        c = _cfg(cur)
    code = leitfaden.branche_fuer(l.get("gruppe"), l.get("branche"))
    b = c["branchen"].get(code) if code else None
    return {"code": code, "name": b["name"], "tipps": b["tipps"]} if b else None


@router.get("/admin/einstellungen/leitfaden")
def leitfaden_admin_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        gespeichert = bool(einstellungen.lesen(cur, "leitfaden"))
        text = leitfaden.als_text(_cfg(cur))
    return {"text": text, "angepasst": gespeichert}


class LeitfadenIn(BaseModel):
    text: str = Field(default="", max_length=40000)
    standard: bool = False


@router.put("/admin/einstellungen/leitfaden")
def leitfaden_admin_speichern(data: LeitfadenIn, user: dict = Depends(require_admin)):
    if data.standard:
        cfg = {}
    else:
        try:
            cfg = leitfaden.aus_text(data.text)
        except ValueError as e:
            raise HTTPException(400, str(e))
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "leitfaden", cfg)
        audit(cur, user, "leitfaden_geaendert", None, {"standard": data.standard})
    return {"ok": True}


# ================================================================= Mail-Entwurf nach dem Gespräch (öffnet im eigenen Mailprogramm, das Portal versendet nichts)
@router.get("/vertrieb/leads/{lid}/nachgespraech")
def nachgespraech(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        cur.execute("SELECT name FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        pname = cur.fetchone()["name"]
        m = _cfg(cur)["mail"]
    f = lambda t: (t or "").replace("{firma}", l["firma"] or "").replace("{name}", (l.get("ansprechpartner") or "").strip() or "Damen und Herren").replace("{vertriebler}", pname)   # noqa: E731
    return {"an": l.get("email") or "", "betreff": f(m["betreff"]), "text": f(m["text"])}


# ================================================================= Angebotsanfrage aus dem Lead
class AnfrageIn(BaseModel):
    paket_code: str | None = Field(default=None, max_length=60)
    notiz: str | None = Field(default=None, max_length=2000)


@router.get("/vertrieb/pakete")
def pakete(user: dict = Depends(require_vertrieb)):
    """Nur Namen, keine Preise: Preise nennt Markentrix im Gespräch."""
    with tx("system") as cur:
        cur.execute("SELECT code, name FROM produkte WHERE aktiv ORDER BY kategorie, name")
        return cur.fetchall()


@router.post("/vertrieb/leads/{lid}/angebotsanfrage")
def anfrage_neu(lid: str, data: AnfrageIn, user: dict = Depends(require_vertrieb)):
    rate_limit("angebotsanfrage:" + str(user["id"]), 20, 3600)
    with tx("system") as cur:
        l = eigener_lead(cur, lid, user["vertriebspartner_id"])
        if l["status"] in ("verloren", "gewonnen", "gesperrt", "consent_ausstehend"):
            raise HTTPException(400, "Für diesen Lead kann keine Angebotsanfrage gestellt werden.")
        cur.execute("SELECT 1 FROM angebotsanfragen WHERE lead_id=%s AND status IN ('angefragt','in_pruefung')", (lid,))
        if cur.fetchone():
            raise HTTPException(409, "Für diesen Lead läuft schon eine Anfrage.")
        paket = None
        if data.paket_code:
            cur.execute("SELECT name FROM produkte WHERE code=%s", (data.paket_code,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(400, "Unbekanntes Paket.")
            paket = p["name"]
        cur.execute("INSERT INTO angebotsanfragen (lead_id, vertriebspartner_id, paket_code, notiz) VALUES (%s,%s,%s,%s) RETURNING id", (lid, user["vertriebspartner_id"], data.paket_code, data.notiz))
        aid = cur.fetchone()["id"]
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'notiz',%s,%s)", (lid, "Angebot angefragt" + (f" ({paket})" if paket else ""), user["email"]))
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        a = cur.fetchone()
        cur.execute("SELECT name FROM vertriebspartner WHERE id=%s", (user["vertriebspartner_id"],))
        pname = cur.fetchone()["name"]
        beschr = f"Vertriebler: {pname}\nPaket: {paket or 'offen'}\nNotiz: {data.notiz or '–'}\nLead: {config.BASE_URL}/admin#lead/{lid}"
        cur.execute("INSERT INTO aufgaben (titel, beschreibung, zustaendig, faellig_am) VALUES (%s,%s,%s,current_date + 1)", (f"Angebot erstellen: {l['firma']}"[:200], beschr, a and a["email"]))
        audit(cur, user, "angebotsanfrage", None, {"lead": lid, "paket": data.paket_code})
        ids = push.admins(cur)
    push.senden(ids, "Angebot angefragt", f"{pname} bittet um ein Angebot für {l['firma']}.", "/admin#lead/" + lid, "angebotsanfrage")
    return {"id": aid}


@router.get("/vertrieb/leads/{lid}/angebotsanfragen")
def anfragen_zum_lead(lid: str, user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        eigener_lead(cur, lid, user["vertriebspartner_id"])
        cur.execute("""SELECT a.id, a.status, a.notiz, a.admin_notiz, a.erstellt_am, a.geaendert_am, p.name AS paket FROM angebotsanfragen a LEFT JOIN produkte p ON p.code=a.paket_code
                       WHERE a.lead_id=%s ORDER BY a.erstellt_am DESC""", (lid,))
        return cur.fetchall()


@router.get("/vertrieb/angebotsanfragen")
def anfragen_liste(user: dict = Depends(require_vertrieb)):
    with tx("system") as cur:
        cur.execute("""SELECT a.id, a.lead_id, l.firma, a.status, a.admin_notiz, a.erstellt_am, a.geaendert_am, p.name AS paket
                       FROM angebotsanfragen a JOIN leads l ON l.id=a.lead_id LEFT JOIN produkte p ON p.code=a.paket_code
                       WHERE a.vertriebspartner_id=%s ORDER BY a.geaendert_am DESC LIMIT 100""", (user["vertriebspartner_id"],))
        return cur.fetchall()


@router.get("/admin/leads/{lid}/angebotsanfragen")
def anfragen_admin(lid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("""SELECT a.id, a.status, a.notiz, a.admin_notiz, a.erstellt_am, a.geaendert_am, p.name AS paket, v.name AS vertriebler
                           FROM angebotsanfragen a LEFT JOIN produkte p ON p.code=a.paket_code LEFT JOIN vertriebspartner v ON v.id=a.vertriebspartner_id
                           WHERE a.lead_id=%s ORDER BY a.erstellt_am DESC""", (lid,))
            return cur.fetchall()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Lead nicht gefunden.")


class AnfrageStatusIn(BaseModel):
    status: str = Field(pattern="^(angefragt|in_pruefung|angebot_raus|angenommen|abgelehnt)$")
    admin_notiz: str | None = Field(default=None, max_length=1000)


@router.patch("/admin/angebotsanfragen/{aid}")
def anfrage_status(aid: str, data: AnfrageStatusIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT a.status, a.vertriebspartner_id, l.firma, l.id AS lead_id FROM angebotsanfragen a JOIN leads l ON l.id=a.lead_id WHERE a.id=%s", (aid,))
            a = cur.fetchone()
            if not a:
                raise HTTPException(404, "Anfrage nicht gefunden.")
            cur.execute("UPDATE angebotsanfragen SET status=%s, admin_notiz=coalesce(%s, admin_notiz), geaendert_am=now() WHERE id=%s", (data.status, data.admin_notiz, aid))
            audit(cur, user, "angebotsanfrage_status", None, {"id": aid, "status": data.status})
            ids = push.partner(cur, a["vertriebspartner_id"]) if a["vertriebspartner_id"] and a["status"] != data.status else []
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Anfrage nicht gefunden.")
    if ids:
        push.senden(ids, "Angebotsanfrage: " + STATUS_TEXT[data.status], a["firma"], "/vertrieb#lead/" + str(a["lead_id"]), "angebotsstatus")
    return {"ok": True}
