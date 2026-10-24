"""Erinnerung an ein Angebot ohne Antwort (an Leads und an bestehende Kunden): Vorschau mit änderbarem Text, Versand per Mail mit PDF.
Nichts geht automatisch raus. Begrenzung: frühestens 3 Tage nach der letzten Mail zum Angebot, höchstens 3 Erinnerungen."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import belege, config, einstellungen, mailer, rechtstexte
from .db import tx
from .security import audit, rate_limit, require_admin

router = APIRouter(prefix="/api/admin")
MIN_TAGE = 3
MAX_ERINNERUNGEN = 3
BLOCKIERT = ("gesperrt", "consent_ausstehend", "tot", "verloren")


def _laden(cur, bid):
    try:
        cur.execute("SELECT * FROM belege WHERE id=%s AND art='angebot'", (bid,))
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Angebot nicht gefunden.")
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Angebot nicht gefunden.")
    return b


def text_bauen(stufe: int, name: str | None, firma: str, nummer: str, gueltig, link: str, absender: str, lead: bool) -> tuple[str, str]:
    """(Betreff, Text) der Erinnerung. Stufe 1 freundliche Nachfrage, 2 Rückfrage zu offenen Fragen, 3 letzte Nachfrage. Endet mit Grußzeile (für Signatur und Logo)."""
    hallo = f"Guten Tag {name}," if name else "Guten Tag,"
    ort = f"Sie können es hier online ansehen und direkt annehmen:\n{link}" if lead else f"Sie finden es auch in Ihrem Kundenportal und können es dort direkt annehmen:\n{link}"
    frist = f"\n\nDas Angebot ist gültig bis zum {gueltig:%d.%m.%Y}." if gueltig else ""
    if stufe <= 1:
        kern = f"vor einigen Tagen haben wir Ihnen unser Angebot {nummer} für {firma} geschickt. Wir wollten kurz nachfragen, ob Sie es schon ansehen konnten. Zur Sicherheit hängen wir es noch einmal an."
        schluss = "Gibt es Fragen oder soll etwas angepasst werden? Antworten Sie einfach auf diese Mail, wir melden uns gern."
        betreff = f"Erinnerung: Ihr Angebot {nummer} von {absender}"
    elif stufe == 2:
        kern = f"wir melden uns noch einmal zu unserem Angebot {nummer} für {firma}. Sind noch Fragen offen, zum Umfang, zum Preis oder zum Ablauf?"
        schluss = "Wenn Sie möchten, besprechen wir alles in einem kurzen Telefonat. Antworten Sie einfach auf diese Mail oder rufen Sie uns an."
        betreff = f"Noch Fragen zu Ihrem Angebot {nummer}?"
    else:
        kern = f"zu unserem Angebot {nummer} für {firma} haben wir noch nichts von Ihnen gehört. Das ist völlig in Ordnung. Wir wollten nur sicher sein, dass es Sie erreicht hat und nichts offen geblieben ist."
        schluss = "Wir melden uns dazu nicht erneut von uns aus. Wenn Sie es später umsetzen möchten, schreiben Sie uns einfach, wir sind dann gern für Sie da."
        betreff = f"Ihr Angebot {nummer}: kurze Rückmeldung"
    return betreff, f"{hallo}\n\n{kern}\n\n{ort}{frist}\n\n{schluss}\n\nViele Grüße\n{absender}"


def _pruefen(cur, b: dict, user: dict | None = None) -> dict:
    """Empfänger, Stufe und Link; wirft HTTPException(400) mit verständlichem Grund, wenn jetzt keine Erinnerung möglich ist."""
    if user is not None and b["kunden_id"]:
        r = user.get("admin_rechte")
        if r is not None and "finanzen" not in r:
            raise HTTPException(403, "Dafür fehlt dir das Recht „Angebote, Rechnungen & Preise“.")
    if b["status"] != "versendet" or not b["nummer"]:
        raise HTTPException(400, "Eine Erinnerung ist nur für ein gesendetes Angebot möglich, das noch nicht angenommen oder abgelehnt wurde.")
    if b["faellig_am"] and b["faellig_am"] < date.today():
        raise HTTPException(400, f"Das Angebot ist seit {b['faellig_am']:%d.%m.%Y} abgelaufen. Bitte ein neues Angebot senden.")
    if b["erinnerungen"] >= MAX_ERINNERUNGEN:
        raise HTTPException(400, f"Es wurden schon {MAX_ERINNERUNGEN} Erinnerungen gesendet. Mehr sind nicht vorgesehen, bitte persönlich anrufen.")
    letzte = b["erinnert_am"] or b["versendet_am"]
    if letzte:
        tage = (datetime.now(timezone.utc) - letzte).days
        if tage < MIN_TAGE:
            raise HTTPException(400, f"Die letzte Mail zu diesem Angebot ging erst vor {tage} Tag(en) raus. Erinnern geht frühestens nach {MIN_TAGE} Tagen.")
    if b["lead_id"]:
        cur.execute("SELECT * FROM leads WHERE id=%s", (b["lead_id"],))
        l = cur.fetchone()
        if not l:
            raise HTTPException(404, "Lead nicht gefunden.")
        if l["status"] in BLOCKIERT:
            raise HTTPException(400, "Für diesen Lead darf nichts gesendet werden (gesperrt, ohne Einwilligung, verloren oder tot).")
        an, name, firma, lead = (l.get("email") or "").strip(), l.get("ansprechpartner"), l["firma"], True
        token = einstellungen.entschluesseln(b["annahme_token_enc"]) if b.get("annahme_token_enc") else None
        if not token:
            raise HTTPException(400, "Für dieses Angebot gibt es keinen Online-Link mehr. Bitte im Lead „Neuen Link erzeugen“ und erneut senden.")
        from .routes_leadangebot import _link
        link = _link(token)
    else:
        cur.execute("SELECT email, ansprechpartner, firma FROM kunden WHERE id=%s", (b["kunden_id"],))
        k = cur.fetchone()
        an, name, firma, lead = (k["email"] or "").strip(), k["ansprechpartner"], k["firma"], False
        link = f"{config.BASE_URL}/app#belege"
    if not an:
        raise HTTPException(400, "Es ist keine E-Mail-Adresse hinterlegt.")
    return {"an": an, "name": name, "firma": firma, "lead": lead, "link": link, "stufe": b["erinnerungen"] + 1}


@router.get("/angebote-erinnerung/{bid}")
def vorschau(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        b = _laden(cur, bid)
        try:
            p = _pruefen(cur, b, user)
        except HTTPException as e:
            if e.status_code == 403:
                raise
            return {"moeglich": False, "grund": e.detail, "erinnerungen": b["erinnerungen"], "nummer": b["nummer"]}
        absender = rechtstexte.firma(cur)["name"] or "Markentrix"
    betreff, text = text_bauen(p["stufe"], p["name"], p["firma"], b["nummer"], b["faellig_am"], p["link"], absender, p["lead"])
    return {"moeglich": True, "an": p["an"], "betreff": betreff, "text": text, "stufe": p["stufe"], "erinnerungen": b["erinnerungen"], "nummer": b["nummer"], "firma": p["firma"],
            "hinweis": "Der Link zum Angebot bleibt unverändert gültig." if p["lead"] else ""}


class SendenIn(BaseModel):
    text: str | None = Field(default=None, max_length=6000)
    betreff: str | None = Field(default=None, max_length=200)


@router.post("/angebote-erinnerung/{bid}")
def senden(bid: str, data: SendenIn, user: dict = Depends(require_admin)):
    rate_limit("angebotserinnerung:" + str(user["id"]), 40, 3600)
    with tx("admin") as cur:
        b = _laden(cur, bid)
        p = _pruefen(cur, b, user)
        f = rechtstexte.firma(cur)
        absender = f["name"] or "Markentrix"
        betreff, text = text_bauen(p["stufe"], p["name"], p["firma"], b["nummer"], b["faellig_am"], p["link"], absender, p["lead"])
        if data.text and data.text.strip():
            text = data.text.strip()
            if p["lead"] and p["link"] not in text:
                raise HTTPException(400, "Der Link zum Angebot muss im Text stehen bleiben.")
        if data.betreff and data.betreff.strip():
            betreff = data.betreff.strip()
        pdf, name = belege.beleg_pdf(cur, bid, f) if p["lead"] else belege.beleg_pdf(cur, bid)
    ok, grund = mailer.senden(p["an"], betreff, text, (name, pdf, "application/pdf"), kunden_id=b["kunden_id"], art="angebot")
    if ok:
        with tx("admin") as cur:
            cur.execute("UPDATE belege SET erinnerungen = erinnerungen + 1, erinnert_am = now(), geaendert_am = now() WHERE id=%s", (bid,))
            if b["lead_id"]:
                cur.execute("UPDATE leads SET wiedervorlage_am = current_date + 3, letzter_kontakt_am = now() WHERE id=%s", (b["lead_id"],))
                cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,%s,%s,%s)",
                            (b["lead_id"], "mail_gesendet", f"Angebot {b['nummer']}: Erinnerung {p['stufe']} per E-Mail gesendet", user["email"]))
            audit(cur, user, "angebot_erinnert", b["kunden_id"], {"nummer": b["nummer"], "stufe": p["stufe"], "lead": str(b["lead_id"]) if b["lead_id"] else None})
    return {"gesendet": ok, "grund": grund, "stufe": p["stufe"], "an": p["an"]}
