"""Admin-Kalender: gebuchte Erstgespräche, eigene Termine und Sperren, Wiedervorlagen der Leads. Verschieben und Absagen mit Mail an den Interessenten."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, mailer
from .db import tx
from .routes_buchung import TZ, ics, lesen
from .security import audit, require_admin

router = APIRouter(prefix="/api")
OFFEN = ("gewonnen", "verloren", "tot", "gesperrt")


def _tag(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise HTTPException(400, "Ungültiges Datum.")


def _zeit(text: str) -> datetime:
    try:
        d = datetime.fromisoformat(text)
    except ValueError:
        raise HTTPException(400, "Ungültige Uhrzeit.")
    return (d if d.tzinfo else d.replace(tzinfo=TZ)).astimezone(timezone.utc)


@router.get("/admin/kalender")
def kalender(von: str, bis: str, user: dict = Depends(require_admin)):
    """Alles zwischen zwei Tagen (einschließlich), höchstens 70 Tage am Stück."""
    v, b = _tag(von), _tag(bis)
    if b < v or (b - v).days > 70:
        raise HTTPException(400, "Zeitraum ungültig (höchstens 70 Tage).")
    a = datetime(v.year, v.month, v.day, tzinfo=TZ).astimezone(timezone.utc)
    e = datetime(b.year, b.month, b.day, tzinfo=TZ).astimezone(timezone.utc) + timedelta(days=1)
    with tx("admin") as cur:
        cur.execute("""SELECT g.id, g.start, g.ende, g.name, g.email, g.telefon, g.nachricht, g.lead_id, l.firma
                       FROM gespraechstermine g LEFT JOIN leads l ON l.id=g.lead_id
                       WHERE g.status='gebucht' AND g.start < %s AND g.ende > %s ORDER BY g.start""", (e, a))
        gespraeche = cur.fetchall()
        cur.execute("SELECT id, art, titel, start, ende, ganztag, notiz FROM kalender_eintraege WHERE start < %s AND ende > %s ORDER BY start", (e, a))
        eintraege = cur.fetchall()
        cur.execute("""SELECT id, coalesce(nullif(firma,''), ansprechpartner) AS name, status, wiedervorlage_am
                       FROM leads WHERE wiedervorlage_am BETWEEN %s AND %s AND kunden_id IS NULL AND status <> ALL(%s) ORDER BY wiedervorlage_am LIMIT 300""", (v, b, list(OFFEN)))
        wiedervorlagen = cur.fetchall()
        buchung = lesen(cur)
    return {"gespraeche": gespraeche, "eintraege": eintraege, "wiedervorlagen": wiedervorlagen,
            "buchung": {"aktiv": buchung["aktiv"], "dauer": buchung["dauer"]}}


class EintragIn(BaseModel):
    art: str = Field(default="termin", pattern="^(termin|sperre)$")
    titel: str = Field(min_length=1, max_length=200)
    start: str = Field(max_length=40)
    ende: str = Field(max_length=40)
    ganztag: bool = False
    notiz: str | None = Field(default=None, max_length=1000)


def _eintrag_werte(d: EintragIn):
    s, e = _zeit(d.start), _zeit(d.ende)
    if d.ganztag:   # ganze Tage: von 0 Uhr des ersten bis 24 Uhr des letzten Tages (Berliner Zeit)
        sl, el = s.astimezone(TZ), e.astimezone(TZ)
        s = datetime(sl.year, sl.month, sl.day, tzinfo=TZ).astimezone(timezone.utc)
        e = datetime(el.year, el.month, el.day, tzinfo=TZ).astimezone(timezone.utc) + timedelta(days=1)
    if e <= s:
        raise HTTPException(400, "Das Ende muss nach dem Beginn liegen.")
    if (e - s).days > 120:
        raise HTTPException(400, "Ein Eintrag darf höchstens 120 Tage dauern.")
    return s, e


@router.post("/admin/kalender/eintraege")
def eintrag_neu(d: EintragIn, user: dict = Depends(require_admin)):
    s, e = _eintrag_werte(d)
    with tx("admin") as cur:
        cur.execute("""INSERT INTO kalender_eintraege (art, titel, start, ende, ganztag, notiz, erstellt_von) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (d.art, d.titel.strip(), s, e, d.ganztag, (d.notiz or "").strip() or None, user["id"]))
        i = cur.fetchone()["id"]
        audit(cur, user, "kalender_eintrag_neu", None, {"art": d.art})
    return {"ok": True, "id": i}


@router.put("/admin/kalender/eintraege/{eid}")
def eintrag_aendern(eid: str, d: EintragIn, user: dict = Depends(require_admin)):
    s, e = _eintrag_werte(d)
    with tx("admin") as cur:
        cur.execute("UPDATE kalender_eintraege SET art=%s, titel=%s, start=%s, ende=%s, ganztag=%s, notiz=%s WHERE id=%s RETURNING id",
                    (d.art, d.titel.strip(), s, e, d.ganztag, (d.notiz or "").strip() or None, eid))
        if not cur.fetchone():
            raise HTTPException(404, "Eintrag nicht gefunden.")
    return {"ok": True}


@router.delete("/admin/kalender/eintraege/{eid}")
def eintrag_loeschen(eid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("DELETE FROM kalender_eintraege WHERE id=%s RETURNING id", (eid,))
        if not cur.fetchone():
            raise HTTPException(404, "Eintrag nicht gefunden.")
        audit(cur, user, "kalender_eintrag_geloescht")
    return {"ok": True}


def _gespraech(cur, gid: str) -> dict:
    cur.execute("SELECT id, start, ende, name, email, lead_id, token, status FROM gespraechstermine WHERE id=%s FOR UPDATE", (gid,))
    g = cur.fetchone()
    if not g or g["status"] != "gebucht":
        raise HTTPException(404, "Termin nicht gefunden oder schon abgesagt.")
    return g


def _wann(d: datetime) -> str:
    return d.astimezone(TZ).strftime("%d.%m.%Y um %H:%M Uhr")


class VerschiebenIn(BaseModel):
    start: str = Field(max_length=40)
    mail: bool = True


def _verschoben_mail(g: dict, alt: datetime, ort: str, sequenz: int):
    absagen = f"{config.BASE_URL}/api/public/buchung/absagen?t={g['token']}"
    anhang = ("termin.ics", ics(str(g["id"]), g["start"], g["ende"], "Erstgespräch mit Markentrix", ort, sequenz=sequenz), "text/calendar")
    mailer.senden(g["email"], "Ihr Gespräch mit Markentrix wurde verschoben",
                  f"Guten Tag {g['name']},\n\nwir mussten Ihr Gespräch leider verschieben.\nBisher: {_wann(alt)}\nNeu: {_wann(g['start'])}.\n{ort}\n\n"
                  f"Die aktualisierte Kalendereinladung hängt an. Falls der neue Termin nicht passt, sagen Sie bitte hier ab oder schreiben Sie uns: {absagen}" + mailer.SIGNATUR, anhang)


@router.post("/admin/gespraeche/{gid}/verschieben")
def verschieben(gid: str, d: VerschiebenIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    neu = _zeit(d.start)
    if neu < datetime.now(timezone.utc):
        raise HTTPException(400, "Der neue Termin liegt in der Vergangenheit.")
    with tx("admin") as cur:
        g = _gespraech(cur, gid)
        c = lesen(cur)
        ende = neu + (g["ende"] - g["start"])
        cur.execute("SELECT 1 FROM gespraechstermine WHERE status='gebucht' AND id<>%s AND start < %s AND ende > %s", (gid, ende, neu))
        if cur.fetchone():
            raise HTTPException(409, "Zu dieser Zeit ist schon ein anderes Gespräch.")
        alt = g["start"]
        cur.execute("UPDATE gespraechstermine SET start=%s, ende=%s, erinnert_24=false, erinnert_2=false WHERE id=%s RETURNING id, start, ende, name, email, token", (neu, ende, gid))
        g2 = cur.fetchone()
        if g["lead_id"]:
            cur.execute("UPDATE leads SET wiedervorlage_am=%s WHERE id=%s AND kunden_id IS NULL", (neu.astimezone(TZ).date(), g["lead_id"]))
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'termin',%s,'admin')", (g["lead_id"], f"Gespräch verschoben auf {_wann(neu)}"))
        audit(cur, user, "gespraech_verschoben", None, {"id": gid})
        ort = c["ort"]
    if d.mail:
        bg.add_task(_verschoben_mail, g2, alt, ort, 1)
    return {"ok": True, "wann": _wann(neu)}


class AbsagenIn(BaseModel):
    mail: bool = True
    grund: str | None = Field(default=None, max_length=500)


def _abgesagt_mail(g: dict, ort: str, grund: str | None):
    anhang = ("termin.ics", ics(str(g["id"]), g["start"], g["ende"], "Erstgespräch mit Markentrix", ort, abgesagt=True, sequenz=2), "text/calendar")
    zusatz = f"\n\n{grund}" if grund else ""
    mailer.senden(g["email"], "Ihr Gespräch mit Markentrix wurde abgesagt",
                  f"Guten Tag {g['name']},\n\nwir müssen Ihr Gespräch am {_wann(g['start'])} leider absagen.{zusatz}\n\nSie können jederzeit einen neuen Termin buchen: {config.BASE_URL}/buchen" + mailer.SIGNATUR, anhang)


@router.post("/admin/gespraeche/{gid}/absagen")
def absagen(gid: str, d: AbsagenIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        g = _gespraech(cur, gid)
        cur.execute("UPDATE gespraechstermine SET status='abgesagt' WHERE id=%s", (gid,))
        if g["lead_id"]:
            cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'termin','Gespräch von uns abgesagt','admin')", (g["lead_id"],))
            cur.execute("""UPDATE leads SET status=CASE WHEN status='termin' THEN 'antwort' ELSE status END, wiedervorlage_am=current_date
                           WHERE id=%s AND kunden_id IS NULL AND status NOT IN ('verloren','tot','gesperrt')""", (g["lead_id"],))
        audit(cur, user, "gespraech_abgesagt_admin", None, {"id": gid})
        ort = lesen(cur)["ort"]
    if d.mail:
        bg.add_task(_abgesagt_mail, g, ort, (d.grund or "").strip() or None)
    return {"ok": True}
