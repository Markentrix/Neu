"""Kunden-Werkzeuge: „Heute“-Seite, Anfragen mit Antwortvorlagen, Bewertungsbitten mit Freigabe. Das Portal versendet nichts."""
import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import kundenwerkzeuge as kw
from .db import tx
from .security import audit, modul_aktiv, rate_limit, require_kunde

router = APIRouter(prefix="/api/kunde")


def _firma(cur, kid) -> str:
    cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
    return cur.fetchone()["firma"]


# ---------------------------------------------------------------- Heute
@router.get("/heute")
def heute(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        a_t = modul_aktiv(cur, kid, "anfragen_termine")
        anfragen, termine, morgen = [], [], []
        if a_t:
            cur.execute("""SELECT id, name, kontakt, nachricht, quelle, status, erstellt_am,
                                  round((extract(epoch FROM now() - erstellt_am) / 3600)::numeric, 1) AS wartet_h
                           FROM anfragen WHERE status IN ('neu','in_bearbeitung') ORDER BY erstellt_am LIMIT 30""")
            anfragen = cur.fetchall()
            cur.execute("""SELECT id, titel, beginn, kontakt_name, kontakt_info, status FROM termine
                           WHERE (beginn AT TIME ZONE 'Europe/Berlin')::date = (now() AT TIME ZONE 'Europe/Berlin')::date AND status IN ('geplant','bestaetigt') ORDER BY beginn""")
            termine = cur.fetchall()
            cur.execute("""SELECT id, titel, beginn, kontakt_name, status FROM termine
                           WHERE (beginn AT TIME ZONE 'Europe/Berlin')::date = (now() AT TIME ZONE 'Europe/Berlin')::date + 1 AND status IN ('geplant','bestaetigt') ORDER BY beginn""")
            morgen = cur.fetchall()
        cur.execute("""SELECT (SELECT count(*) FROM kundenfreigaben WHERE status='wartet') AS freigaben,
                              (SELECT count(*) FROM tickets WHERE status='wartet_auf_kunde' OR kunde_ungelesen) AS nachrichten""")
        offen = cur.fetchone()
        bew = 0
        if a_t:
            cur.execute("""SELECT count(*) AS n FROM termine t WHERE t.status='erledigt' AND t.beginn > now() - interval '14 days' AND coalesce(t.kontakt_name, t.kontakt_info, '') <> ''
                           AND NOT EXISTS (SELECT 1 FROM bewertungsanfragen b WHERE b.name = t.kontakt_name AND b.erstellt_am > now() - interval '90 days')""")
            bew = cur.fetchone()["n"]
    rueck = [a for a in anfragen if a["quelle"] == "telefon"]
    return {"anfragen": anfragen, "rueckrufe": rueck, "termine_heute": termine, "termine_morgen": morgen,
            "freigaben": offen["freigaben"], "nachrichten": offen["nachrichten"], "bewertung_vorschlaege": bew, "modul": a_t}


# ---------------------------------------------------------------- Antwortvorlagen und Antworten
@router.get("/anfragen/{aid}/entwuerfe")
def entwuerfe(aid: str, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            if not modul_aktiv(cur, kid, "anfragen_termine"):
                raise HTTPException(403, "Dieses Modul ist für dein Konto nicht freigeschaltet.")
            cur.execute("SELECT id, name, kontakt, nachricht, antwort_am FROM anfragen WHERE id=%s", (aid,))
            a = cur.fetchone()
            if not a:
                raise HTTPException(404, "Anfrage nicht gefunden.")
            firma = _firma(cur, kid)
            cur.execute("SELECT id, name, text FROM antwortvorlagen_kunde ORDER BY erstellt_am")
            eigene = cur.fetchall()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Anfrage nicht gefunden.")
    werte = {"name": kw.vorname(a["name"]), "firma": firma, "tag": "morgen"}
    liste = [{"code": c, "name": n, "text": kw.fuellen(t, **werte), "eigene": False} for c, n, t in kw.STANDARD_VORLAGEN]
    liste += [{"code": str(e["id"]), "name": e["name"], "text": kw.fuellen(e["text"], **werte), "eigene": True} for e in eigene]
    return {"anfrage": {"id": a["id"], "name": a["name"], "kontakt": a["kontakt"], "nachricht": a["nachricht"], "kanal": kw.kanal_aus_kontakt(a["kontakt"]), "antwort_am": a["antwort_am"]}, "vorlagen": liste}


class VorlageIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=1500)


@router.post("/antwortvorlagen")
def vorlage_neu(data: VorlageIn, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("SELECT count(*) AS n FROM antwortvorlagen_kunde")
        if cur.fetchone()["n"] >= 30:
            raise HTTPException(400, "Mehr als 30 eigene Vorlagen sind nicht möglich.")
        cur.execute("INSERT INTO antwortvorlagen_kunde (kunden_id, name, text) VALUES (%s,%s,%s) RETURNING id", (user["kunden_id"], data.name.strip(), data.text.strip()))
        return cur.fetchone()


@router.delete("/antwortvorlagen/{vid}")
def vorlage_weg(vid: str, user: dict = Depends(require_kunde)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("DELETE FROM antwortvorlagen_kunde WHERE id=%s", (vid,))
            if cur.rowcount == 0:
                raise HTTPException(404, "Vorlage nicht gefunden.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Vorlage nicht gefunden.")
    return {"ok": True}


class BeantwortetIn(BaseModel):
    kanal: str = Field(pattern="^(mail|telefon|whatsapp|sms|sonst)$")


@router.post("/anfragen/{aid}/beantwortet")
def beantwortet(aid: str, data: BeantwortetIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            if not modul_aktiv(cur, kid, "anfragen_termine"):
                raise HTTPException(403, "Dieses Modul ist für dein Konto nicht freigeschaltet.")
            cur.execute("UPDATE anfragen SET status='beantwortet', antwort_am=now(), antwort_kanal=%s WHERE id=%s RETURNING id", (data.kanal, aid))
            if not cur.fetchone():
                raise HTTPException(404, "Anfrage nicht gefunden.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Anfrage nicht gefunden.")
    return {"ok": True}


# ---------------------------------------------------------------- Bewertungen
_LINK = re.compile(r"^https://[^\s<>\"']{4,500}$")


class BewEinstIn(BaseModel):
    link: str | None = Field(default=None, max_length=500)
    text: str | None = Field(default=None, max_length=1000)


@router.put("/bewertungen/einstellung")
def bew_einstellung(data: BewEinstIn, user: dict = Depends(require_kunde)):
    link = (data.link or "").strip() or None
    text = (data.text or "").strip() or None
    if link and not _LINK.match(link):
        raise HTTPException(400, "Der Bewertungslink muss mit https:// beginnen.")
    if text and "{link}" not in text:
        raise HTTPException(400, "Im Text muss {link} stehen, dort wird der Bewertungslink eingesetzt.")
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("""INSERT INTO kunden_werkzeuge (kunden_id, bewertungslink, bewertungstext) VALUES (%s,%s,%s)
                       ON CONFLICT (kunden_id) DO UPDATE SET bewertungslink=EXCLUDED.bewertungslink, bewertungstext=EXCLUDED.bewertungstext""", (user["kunden_id"], link, text))
        audit(cur, user, "bewertungslink_gesetzt", user["kunden_id"])
    return {"ok": True}


def _einst(cur, kid):
    cur.execute("SELECT bewertungslink, bewertungstext FROM kunden_werkzeuge WHERE kunden_id=%s", (kid,))
    return cur.fetchone() or {"bewertungslink": None, "bewertungstext": None}


@router.get("/bewertungen")
def bewertungen(user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        e = _einst(cur, kid)
        cur.execute("""SELECT id, name, empfaenger_kontakt AS kontakt, ausloeser, status, kanal, text, gesendet_am, erstellt_am FROM bewertungsanfragen ORDER BY erstellt_am DESC LIMIT 50""")
        liste = cur.fetchall()
        vorschlaege = []
        if modul_aktiv(cur, kid, "anfragen_termine"):
            cur.execute("""SELECT t.id, t.kontakt_name AS name, t.kontakt_info AS kontakt, t.titel, t.beginn FROM termine t
                           WHERE t.status='erledigt' AND t.beginn > now() - interval '30 days' AND coalesce(t.kontakt_name,'') <> ''
                             AND NOT EXISTS (SELECT 1 FROM bewertungsanfragen b WHERE b.name = t.kontakt_name AND b.erstellt_am > now() - interval '90 days')
                           ORDER BY t.beginn DESC LIMIT 20""")
            vorschlaege = cur.fetchall()
        cur.execute("SELECT to_char(monat,'YYYY-MM') AS monat, google_bewertungen, google_sterne FROM kennzahlen_extern ORDER BY monat DESC LIMIT 2")
        k = cur.fetchall()
    return {"link": e["bewertungslink"], "text": e["bewertungstext"] or kw.STANDARD_BEWERTUNG, "standard_text": kw.STANDARD_BEWERTUNG, "liste": liste, "vorschlaege": vorschlaege,
            "google": {"jetzt": k[0] if k else None, "vorher": k[1] if len(k) > 1 else None},
            "gesendet_30d": sum(1 for b in liste if b["status"] == "gesendet" and b["gesendet_am"] and (b["gesendet_am"].date() >= date.today() - timedelta(days=30)))}


class BitteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kontakt: str = Field(min_length=3, max_length=200)
    ausloeser: str | None = Field(default=None, max_length=200)


@router.post("/bewertungen/bitte")
def bitte_neu(data: BitteIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    rate_limit("bewbitte:" + str(kid), 60, 3600)
    with tx("kunde", kid) as cur:
        e = _einst(cur, kid)
        if not e["bewertungslink"]:
            raise HTTPException(400, "Bitte hinterlege zuerst deinen Bewertungslink (z. B. den Google-Link).")
        cur.execute("""SELECT 1 FROM bewertungsanfragen WHERE (name = %s OR empfaenger_kontakt = %s) AND status IN ('geplant','gesendet') AND erstellt_am > now() - interval '90 days'""", (data.name.strip(), data.kontakt.strip()))
        if cur.fetchone():
            raise HTTPException(409, "Diese Person hast du in den letzten 90 Tagen schon um eine Bewertung gebeten.")
        text = kw.fuellen(e["bewertungstext"] or kw.STANDARD_BEWERTUNG, name=kw.vorname(data.name), firma=_firma(cur, kid), link=e["bewertungslink"])
        cur.execute("""INSERT INTO bewertungsanfragen (kunden_id, name, empfaenger_kontakt, ausloeser, status, text) VALUES (%s,%s,%s,%s,'geplant',%s) RETURNING id""",
                    (kid, data.name.strip(), data.kontakt.strip(), data.ausloeser, text))
        r = cur.fetchone()
    return {"id": r["id"], "text": text, "kanal": kw.kanal_aus_kontakt(data.kontakt)}


class FreigabeIn(BaseModel):
    kanal: str = Field(pattern="^(mail|whatsapp|sms|sonst)$")
    text: str | None = Field(default=None, max_length=1500)


@router.post("/bewertungen/{bid}/freigeben")
def bitte_freigeben(bid: str, data: FreigabeIn, user: dict = Depends(require_kunde)):
    """Der Inhaber hat die Bitte selbst abgeschickt (eigenes Telefon/Mailprogramm). Das Portal markiert nur."""
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("""UPDATE bewertungsanfragen SET status='gesendet', gesendet_am=now(), kanal=%s, text=coalesce(%s,text) WHERE id=%s AND status='geplant' RETURNING id""", (data.kanal, data.text, bid))
            if not cur.fetchone():
                raise HTTPException(404, "Entwurf nicht gefunden oder schon erledigt.")
            audit(cur, user, "bewertungsbitte_freigegeben", user["kunden_id"], {"kanal": data.kanal})
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Entwurf nicht gefunden oder schon erledigt.")
    return {"ok": True}


@router.delete("/bewertungen/{bid}")
def bitte_verwerfen(bid: str, user: dict = Depends(require_kunde)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("UPDATE bewertungsanfragen SET status='abgelehnt' WHERE id=%s AND status='geplant' RETURNING id", (bid,))
            if not cur.fetchone():
                raise HTTPException(404, "Entwurf nicht gefunden oder schon erledigt.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Entwurf nicht gefunden oder schon erledigt.")
    return {"ok": True}
