"""Zusammenarbeit mit dem Kunden: Nachrichten/Aufträge (Tickets), Anhänge, Dokumentenablage, Freigaben, Zufriedenheit.
Kunde: /api/kunde/...   Admin: /api/admin/...   Mails gehen im Hintergrund raus (BackgroundTasks)."""
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from psycopg import errors
from pydantic import BaseModel, Field

from . import dateien, einstellungen, mailer, push
from .db import tx
from .security import audit, client_ip, require_admin, require_kunde

router = APIRouter(prefix="/api/admin")
kunde_router = APIRouter(prefix="/api/kunde")

NR = "'T-' || lpad(t.nummer::text, 4, '0')"
ART_NAMEN = {"frage": "Frage", "auftrag": "Auftrag", "aenderung": "Änderungswunsch", "problem": "Problem", "modul": "Zusatzmodul-Anfrage"}
STATI = ("offen", "in_arbeit", "wartet_auf_kunde", "erledigt")


def nicht_gefunden():
    return HTTPException(404, "Nicht gefunden.")


def admin_empfaenger(cur) -> str | None:
    an = (einstellungen.lesen(cur, "benachrichtigung") or {}).get("alarm_email")
    if not an:
        cur.execute("SELECT email FROM benutzer WHERE rolle='admin' AND aktiv ORDER BY erstellt_am LIMIT 1")
        r = cur.fetchone()
        an = r and r["email"]
    return an or None


def kunden_empfaenger(cur, kid, zusatz: str | None = None) -> list[str]:
    """Wer eine Benachrichtigung bekommt: Wunschadresse bzw. Haupt-Mail des Kunden (falls nicht abgeschaltet) und optional eine weitere Adresse."""
    cur.execute("SELECT email, benachr_email, benachr_nachrichten FROM kunden WHERE id=%s", (kid,))
    k = cur.fetchone()
    if not k or not k["benachr_nachrichten"]:
        return []
    ziele = []
    for a in (zusatz, k["benachr_email"] or k["email"]):
        a = (a or "").strip()
        if a and a.lower() not in [z.lower() for z in ziele]:
            ziele.append(a)
    return ziele


def _name(user) -> str:
    return (user.get("name") or "").strip() or user["email"].split("@")[0]


def team_name(user) -> str:
    return (user.get("name") or "").strip() or "Markentrix-Team"


def _mails(bg: BackgroundTasks, an: list[str] | str | None, fn, *args):
    for a in ([an] if isinstance(an, str) else (an or [])):
        bg.add_task(fn, a, *args)


# ================================================================= Tickets: Kunde
class TicketIn(BaseModel):
    betreff: str = Field(min_length=1, max_length=200)
    art: str = Field(default="frage", pattern="^(frage|auftrag|aenderung|problem)$")
    text: str = Field(min_length=1, max_length=10000)
    prioritaet: str = Field(default="normal", pattern="^(normal|hoch)$")


class NachrichtIn(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


def ticket_anlegen(cur, kid, user: dict, betreff, art, text, prioritaet="normal", modul=None, von="kunde") -> dict:
    cur.execute("""INSERT INTO tickets (kunden_id, betreff, art, prioritaet, modul_code, erstellt_von, ersteller_name, letzte_nachricht_von, kunde_ungelesen, team_ungelesen)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id, 'T-' || lpad(nummer::text, 4, '0') AS nr""",
                (kid, betreff.strip(), art, prioritaet, modul, user["id"], _name(user) if von == "kunde" else None, von, von == "team", von == "kunde"))
    t = cur.fetchone()
    cur.execute("INSERT INTO ticket_nachrichten (ticket_id, kunden_id, von, autor_name, text) VALUES (%s,%s,%s,%s,%s)",
                (t["id"], kid, von, _name(user) if von == "kunde" else team_name(user), text.strip()))
    return t


@kunde_router.get("/tickets")
def k_liste(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute(f"""SELECT t.id, {NR} AS nr, t.betreff, t.art, t.status, t.letzte_nachricht_von, t.kunde_ungelesen, t.geaendert_am, t.erstellt_am,
                              EXISTS (SELECT 1 FROM zufriedenheit z WHERE z.ticket_id = t.id) AS bewertet
                        FROM tickets t ORDER BY t.geaendert_am DESC LIMIT 200""")
        return cur.fetchall()


@kunde_router.post("/tickets")
def k_neu(data: TicketIn, bg: BackgroundTasks, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    with tx("kunde", kid) as cur:
        t = ticket_anlegen(cur, kid, user, data.betreff, data.art, data.text, data.prioritaet)
        cur.execute("SELECT firma, kundennummer FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        audit(cur, user, "ticket_erstellt", kid, {"nr": t["nr"], "art": data.art})
    with tx("system") as cur:
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
    push.senden(ids, "Neue Kundennachricht", "Ein Kunde hat eine neue Nachricht im Portal geschrieben.", "/admin#postfach", "ticket")
    _mails(bg, an, mailer.ticket_neu_team, t["nr"], k["firma"], k["kundennummer"], data.betreff, ART_NAMEN[data.art], data.text)
    return {"id": t["id"], "nr": t["nr"]}


@kunde_router.get("/tickets/{tid}")
def k_detail(tid: str, user: dict = Depends(require_kunde)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute(f"SELECT t.id, {NR} AS nr, t.betreff, t.art, t.status, t.erstellt_am, t.geaendert_am, t.erledigt_am FROM tickets t WHERE t.id=%s", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("SELECT id, von, autor_name, text, erstellt_am FROM ticket_nachrichten WHERE ticket_id=%s ORDER BY id", (tid,))
            t["nachrichten"] = cur.fetchall()
            cur.execute("SELECT id, name, mime, groesse, von, erstellt_am FROM dateien WHERE ticket_id=%s ORDER BY erstellt_am", (tid,))
            t["dateien"] = cur.fetchall()
            cur.execute("SELECT punkte, kommentar FROM zufriedenheit WHERE ticket_id=%s", (tid,))
            t["bewertung"] = cur.fetchone()
            if user["kunden_rolle"] != "nur_lesen":
                cur.execute("UPDATE tickets SET kunde_ungelesen=false WHERE id=%s AND kunde_ungelesen", (tid,))
            return t
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


@kunde_router.post("/tickets/{tid}/nachricht")
def k_antwort(tid: str, data: NachrichtIn, bg: BackgroundTasks, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            cur.execute(f"SELECT t.id, {NR} AS nr, t.betreff, t.status FROM tickets t WHERE t.id=%s FOR UPDATE", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("INSERT INTO ticket_nachrichten (ticket_id, kunden_id, von, autor_name, text) VALUES (%s,%s,'kunde',%s,%s)", (tid, kid, _name(user), data.text.strip()))
            neu = "offen" if t["status"] == "erledigt" else ("in_arbeit" if t["status"] == "wartet_auf_kunde" else t["status"])
            cur.execute("""UPDATE tickets SET status=%s, letzte_nachricht_von='kunde', team_ungelesen=true, geaendert_am=now(), erledigt_am=NULL WHERE id=%s""", (neu, tid))
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
            firma = cur.fetchone()["firma"]
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    with tx("system") as cur:
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
    push.senden(ids, "Antwort vom Kunden", "Ein Kunde hat auf eine Nachricht geantwortet.", "/admin#postfach", "ticket")
    _mails(bg, an, mailer.ticket_antwort_team, t["nr"], firma, t["betreff"], data.text)
    return {"ok": True}


@kunde_router.post("/tickets/{tid}/dateien")
def k_anhang(tid: str, datei: UploadFile = File(...), user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    name, mime, daten = dateien.lesen(datei)
    try:
        with tx("kunde", kid) as cur:
            cur.execute("SELECT 1 FROM tickets WHERE id=%s", (tid,))
            if not cur.fetchone():
                raise nicht_gefunden()
            cur.execute("""INSERT INTO dateien (kunden_id, ticket_id, bereich, name, mime, groesse, daten, von, hochgeladen_von) VALUES (%s,%s,'anhang',%s,%s,%s,%s,'kunde',%s) RETURNING id""",
                        (kid, tid, name, mime, len(daten), daten, user["id"]))
            fid = cur.fetchone()["id"]
            cur.execute("UPDATE tickets SET team_ungelesen=true, geaendert_am=now() WHERE id=%s", (tid,))
            return {"id": fid, "name": name}
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


class BewertungIn(BaseModel):
    punkte: int = Field(ge=0, le=10)
    kommentar: str | None = Field(default=None, max_length=1000)


@kunde_router.post("/tickets/{tid}/zufriedenheit")
def k_bewerten(tid: str, data: BewertungIn, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    try:
        with tx("kunde", kid) as cur:
            cur.execute("SELECT status FROM tickets WHERE id=%s", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            if t["status"] != "erledigt":
                raise HTTPException(400, "Bewerten kannst du, sobald die Anfrage erledigt ist.")
            try:
                cur.execute("INSERT INTO zufriedenheit (kunden_id, ticket_id, art, punkte, kommentar, benutzer_id) VALUES (%s,%s,'ticket',%s,%s,%s)",
                            (kid, tid, data.punkte, (data.kommentar or "").strip() or None, user["id"]))
            except errors.UniqueViolation:
                raise HTTPException(400, "Diese Anfrage wurde schon bewertet.")
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


@kunde_router.post("/zufriedenheit")
def k_quartal(data: BewertungIn, user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("INSERT INTO zufriedenheit (kunden_id, art, punkte, kommentar, benutzer_id) VALUES (%s,'quartal',%s,%s,%s)",
                    (user["kunden_id"], data.punkte, (data.kommentar or "").strip() or None, user["id"]))
    return {"ok": True}


@kunde_router.get("/dateien/{fid}")
def k_datei(fid: str, user: dict = Depends(require_kunde)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("SELECT name, mime, daten FROM dateien WHERE id=%s", (fid,))
            f = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    if not f:
        raise nicht_gefunden()
    return dateien.antwort(f["name"], f["mime"], f["daten"])


# ================================================================= Dokumentenablage: Kunde
@kunde_router.get("/unterlagen")
def k_unterlagen(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("SELECT id, name, mime, groesse, kategorie, von, erstellt_am FROM dateien WHERE bereich='dokument' ORDER BY erstellt_am DESC LIMIT 500")
        return {"dateien": cur.fetchall(), "kategorien": dateien.KATEGORIE_NAMEN}


@kunde_router.post("/unterlagen")
def k_unterlage(datei: UploadFile = File(...), kategorie: str = Form("sonstiges"), user: dict = Depends(require_kunde)):
    if kategorie not in dateien.KATEGORIEN:
        raise HTTPException(400, "Kategorie ungültig.")
    name, mime, daten = dateien.lesen(datei)
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("""INSERT INTO dateien (kunden_id, bereich, kategorie, name, mime, groesse, daten, von, hochgeladen_von) VALUES (%s,'dokument',%s,%s,%s,%s,%s,'kunde',%s) RETURNING id""",
                    (user["kunden_id"], kategorie, name, mime, len(daten), daten, user["id"]))
        fid = cur.fetchone()["id"]
        audit(cur, user, "unterlage_hochgeladen", user["kunden_id"], {"name": name})
    return {"id": fid}


@kunde_router.delete("/unterlagen/{fid}")
def k_unterlage_weg(fid: str, user: dict = Depends(require_kunde)):
    try:
        with tx("kunde", user["kunden_id"]) as cur:
            cur.execute("DELETE FROM dateien WHERE id=%s AND bereich='dokument' AND von='kunde' RETURNING id", (fid,))
            if not cur.fetchone():
                raise HTTPException(404, "Nicht gefunden. Dateien vom Markentrix-Team kannst du nicht löschen.")
            audit(cur, user, "unterlage_geloescht", user["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


# ================================================================= Freigaben: Kunde
class EntscheidungIn(BaseModel):
    entscheidung: str = Field(pattern="^(freigegeben|abgelehnt)$")
    kommentar: str | None = Field(default=None, max_length=2000)


@kunde_router.get("/freigaben")
def k_freigaben(user: dict = Depends(require_kunde)):
    with tx("kunde", user["kunden_id"]) as cur:
        cur.execute("""SELECT f.id, f.titel, f.art, f.inhalt, f.status, f.angefragt_am, f.entschieden_am, f.entschieden_name, f.kommentar,
                              (SELECT coalesce(json_agg(json_build_object('id', d.id, 'name', d.name, 'mime', d.mime, 'groesse', d.groesse) ORDER BY d.erstellt_am), '[]'::json)
                               FROM dateien d WHERE d.freigabe_id = f.id) AS dateien
                       FROM kundenfreigaben f ORDER BY (f.status = 'wartet') DESC, f.angefragt_am DESC LIMIT 200""")
        return cur.fetchall()


@kunde_router.post("/freigaben/{fid}/entscheiden")
def k_entscheiden(fid: str, data: EntscheidungIn, request: Request, bg: BackgroundTasks, user: dict = Depends(require_kunde)):
    kid = user["kunden_id"]
    if data.entscheidung == "abgelehnt" and not (data.kommentar or "").strip():
        raise HTTPException(400, "Bitte schreibe kurz, was geändert werden soll.")
    try:
        with tx("kunde", kid) as cur:
            cur.execute("SELECT id, titel, status FROM kundenfreigaben WHERE id=%s FOR UPDATE", (fid,))
            f = cur.fetchone()
            if not f:
                raise nicht_gefunden()
            if f["status"] != "wartet":
                raise HTTPException(400, "Darüber wurde schon entschieden.")
            cur.execute("""UPDATE kundenfreigaben SET status=%s, kommentar=%s, entschieden_am=now(), entschieden_von=%s, entschieden_name=%s, entschieden_ip=%s WHERE id=%s""",
                        (data.entscheidung, (data.kommentar or "").strip() or None, user["id"], _name(user), client_ip(request), fid))
            cur.execute("SELECT firma FROM kunden WHERE id=%s", (kid,))
            firma = cur.fetchone()["firma"]
            audit(cur, user, "kundenfreigabe_" + data.entscheidung, kid, {"titel": f["titel"]})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    with tx("system") as cur:
        an = admin_empfaenger(cur)
    _mails(bg, an, mailer.freigabe_entschieden_team, firma, f["titel"], data.entscheidung, (data.kommentar or "").strip() or None, _name(user))
    return {"ok": True}


# ================================================================= Tickets: Admin
class AdminNachrichtIn(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    intern: bool = False
    status: str | None = Field(default=None, pattern="^(offen|in_arbeit|wartet_auf_kunde|erledigt)$")


class AdminTicketIn(BaseModel):
    status: str | None = Field(default=None, pattern="^(offen|in_arbeit|wartet_auf_kunde|erledigt)$")
    prioritaet: str | None = Field(default=None, pattern="^(normal|hoch)$")
    zustaendig: str | None = Field(default=None, max_length=200)
    faellig_am: date | None = None
    faellig_loeschen: bool = False


class AdminNeuIn(BaseModel):
    betreff: str = Field(min_length=1, max_length=200)
    art: str = Field(default="auftrag", pattern="^(frage|auftrag|aenderung|problem)$")
    text: str = Field(min_length=1, max_length=10000)


@router.get("/tickets")
def a_liste(status: str = "", kunde: str = "", user: dict = Depends(require_admin)):
    if status and status not in STATI + ("offene",):
        raise HTTPException(400, "Status ungültig.")
    with tx("admin") as cur:
        bed, par = [], []
        if status == "offene":
            bed.append("t.status <> 'erledigt'")
        elif status:
            bed.append("t.status = %s"); par.append(status)
        if kunde:
            bed.append("k.kundennummer = %s"); par.append(kunde)
        cur.execute(f"""SELECT t.id, {NR} AS nr, t.betreff, t.art, t.status, t.prioritaet, t.zustaendig, t.faellig_am, t.letzte_nachricht_von, t.team_ungelesen,
                               t.geaendert_am, t.erstellt_am, k.id AS kunden_id, k.kundennummer, k.firma
                        FROM tickets t JOIN kunden k ON k.id = t.kunden_id {('WHERE ' + ' AND '.join(bed)) if bed else ''}
                        ORDER BY (t.status = 'erledigt'), t.team_ungelesen DESC, t.geaendert_am DESC LIMIT 300""", par)
        return cur.fetchall()


@router.get("/tickets/{tid}")
def a_detail(tid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute(f"""SELECT t.id, {NR} AS nr, t.betreff, t.art, t.status, t.prioritaet, t.zustaendig, t.faellig_am, t.modul_code, t.erstellt_am, t.geaendert_am,
                                   t.erste_antwort_am, t.erledigt_am, t.ersteller_name, k.id AS kunden_id, k.kundennummer, k.firma
                            FROM tickets t JOIN kunden k ON k.id = t.kunden_id WHERE t.id=%s""", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("SELECT id, von, autor_name, intern, text, erstellt_am FROM ticket_nachrichten WHERE ticket_id=%s ORDER BY id", (tid,))
            t["nachrichten"] = cur.fetchall()
            cur.execute("SELECT id, name, mime, groesse, von, erstellt_am FROM dateien WHERE ticket_id=%s ORDER BY erstellt_am", (tid,))
            t["dateien"] = cur.fetchall()
            cur.execute("SELECT punkte, kommentar FROM zufriedenheit WHERE ticket_id=%s", (tid,))
            t["bewertung"] = cur.fetchone()
            cur.execute("UPDATE tickets SET team_ungelesen=false WHERE id=%s AND team_ungelesen", (tid,))
            return t
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


def _erledigt_setzen(cur, tid):
    cur.execute("UPDATE tickets SET erledigt_am=now() WHERE id=%s AND erledigt_am IS NULL", (tid,))


@router.post("/tickets/{tid}/nachricht")
def a_antwort(tid: str, data: AdminNachrichtIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute(f"""SELECT t.id, {NR} AS nr, t.betreff, t.status, t.kunden_id, t.erstellt_von, t.erste_antwort_am FROM tickets t WHERE t.id=%s FOR UPDATE""", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("INSERT INTO ticket_nachrichten (ticket_id, kunden_id, von, autor_name, intern, text) VALUES (%s,%s,'team',%s,%s,%s)",
                        (tid, t["kunden_id"], team_name(user), data.intern, data.text.strip()))
            ziele = []
            if data.intern:
                if data.status:
                    cur.execute("UPDATE tickets SET status=%s, geaendert_am=now() WHERE id=%s", (data.status, tid))
                    if data.status == "erledigt":
                        _erledigt_setzen(cur, tid)
            else:
                neu = data.status or ("in_arbeit" if t["status"] == "offen" else t["status"])
                cur.execute("""UPDATE tickets SET status=%s, letzte_nachricht_von='team', kunde_ungelesen=true, geaendert_am=now(),
                               erste_antwort_am=coalesce(erste_antwort_am, now()), erledigt_am=CASE WHEN %s='erledigt' THEN coalesce(erledigt_am, now()) ELSE NULL END
                               WHERE id=%s""", (neu, neu, tid))
                zusatz = None
                if t["erstellt_von"]:
                    cur.execute("SELECT email FROM benutzer WHERE id=%s AND aktiv", (t["erstellt_von"],))
                    r = cur.fetchone()
                    zusatz = r and r["email"]
                ziele = kunden_empfaenger(cur, t["kunden_id"], zusatz)
                cur.execute("SELECT ersteller_name FROM tickets WHERE id=%s", (tid,))
                ans = cur.fetchone()["ersteller_name"]
            audit(cur, user, "ticket_antwort", t["kunden_id"], {"nr": t["nr"], "intern": data.intern})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    if not data.intern:
        _mails(bg, ziele, mailer.ticket_antwort_kunde, ans, t["nr"], t["betreff"], data.text, (data.status == "erledigt"))
    return {"ok": True}


@router.patch("/tickets/{tid}")
def a_aendern(tid: str, data: AdminTicketIn, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, kunden_id FROM tickets WHERE id=%s FOR UPDATE", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("""UPDATE tickets SET status=coalesce(%s,status), prioritaet=coalesce(%s,prioritaet), zustaendig=CASE WHEN %s::boolean THEN nullif(%s,'') ELSE zustaendig END,
                           faellig_am=CASE WHEN %s::boolean THEN NULL ELSE coalesce(%s,faellig_am) END, geaendert_am=now() WHERE id=%s""",
                        (data.status, data.prioritaet, data.zustaendig is not None, data.zustaendig, data.faellig_loeschen, data.faellig_am, tid))
            if data.status == "erledigt":
                _erledigt_setzen(cur, tid)
            elif data.status:
                cur.execute("UPDATE tickets SET erledigt_am=NULL WHERE id=%s", (tid,))
            audit(cur, user, "ticket_geaendert", t["kunden_id"], data.model_dump(exclude_none=True, mode="json"))
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


@router.post("/kunden/{kid}/tickets")
def a_neu(kid: str, data: AdminNeuIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise nicht_gefunden()
            t = ticket_anlegen(cur, kid, user, data.betreff, data.art, data.text, von="team")
            cur.execute("UPDATE tickets SET status='wartet_auf_kunde', erste_antwort_am=now() WHERE id=%s", (t["id"],))
            ziele = kunden_empfaenger(cur, kid)
            audit(cur, user, "ticket_erstellt_team", kid, {"nr": t["nr"]})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    _mails(bg, ziele, mailer.ticket_antwort_kunde, None, t["nr"], data.betreff, data.text, False)
    return {"id": t["id"], "nr": t["nr"]}


@router.post("/tickets/{tid}/dateien")
def a_anhang(tid: str, datei: UploadFile = File(...), user: dict = Depends(require_admin)):
    name, mime, daten = dateien.lesen(datei)
    try:
        with tx("admin") as cur:
            cur.execute("SELECT kunden_id FROM tickets WHERE id=%s", (tid,))
            t = cur.fetchone()
            if not t:
                raise nicht_gefunden()
            cur.execute("""INSERT INTO dateien (kunden_id, ticket_id, bereich, name, mime, groesse, daten, von, hochgeladen_von) VALUES (%s,%s,'anhang',%s,%s,%s,%s,'team',%s) RETURNING id""",
                        (t["kunden_id"], tid, name, mime, len(daten), daten, user["id"]))
            fid = cur.fetchone()["id"]
            cur.execute("UPDATE tickets SET kunde_ungelesen=true, geaendert_am=now() WHERE id=%s", (tid,))
            return {"id": fid, "name": name}
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


@router.get("/dateien/{fid}")
def a_datei(fid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT name, mime, daten FROM dateien WHERE id=%s", (fid,))
            f = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    if not f:
        raise nicht_gefunden()
    return dateien.antwort(f["name"], f["mime"], f["daten"])


# ================================================================= Dokumentenablage: Admin
@router.get("/kunden/{kid}/unterlagen")
def a_unterlagen(kid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT id, name, mime, groesse, kategorie, von, sichtbar_kunde, erstellt_am FROM dateien WHERE kunden_id=%s AND bereich='dokument' ORDER BY erstellt_am DESC", (kid,))
            return {"dateien": cur.fetchall(), "kategorien": dateien.KATEGORIE_NAMEN}
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


@router.post("/kunden/{kid}/unterlagen")
def a_unterlage(kid: str, datei: UploadFile = File(...), kategorie: str = Form("sonstiges"), sichtbar_kunde: bool = Form(True), user: dict = Depends(require_admin)):
    if kategorie not in dateien.KATEGORIEN:
        raise HTTPException(400, "Kategorie ungültig.")
    name, mime, daten = dateien.lesen(datei)
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise nicht_gefunden()
            cur.execute("""INSERT INTO dateien (kunden_id, bereich, kategorie, name, mime, groesse, daten, von, hochgeladen_von, sichtbar_kunde) VALUES (%s,'dokument',%s,%s,%s,%s,%s,'team',%s,%s) RETURNING id""",
                        (kid, kategorie, name, mime, len(daten), daten, user["id"], sichtbar_kunde))
            fid = cur.fetchone()["id"]
            audit(cur, user, "unterlage_hochgeladen_team", kid, {"name": name, "sichtbar_kunde": sichtbar_kunde})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"id": fid}


@router.delete("/unterlagen/{fid}")
def a_unterlage_weg(fid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("DELETE FROM dateien WHERE id=%s AND bereich='dokument' RETURNING kunden_id", (fid,))
            r = cur.fetchone()
            if not r:
                raise nicht_gefunden()
            audit(cur, user, "unterlage_geloescht_team", r["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}


# ================================================================= Freigaben: Admin
class FreigabeIn(BaseModel):
    titel: str = Field(min_length=1, max_length=200)
    art: str = Field(default="sonstiges", pattern="^(social|text|angebot|design|website|sonstiges)$")
    inhalt: str | None = Field(default=None, max_length=20000)


@router.get("/freigaben-kunden")
def a_freigaben(status: str = "", user: dict = Depends(require_admin)):
    if status and status not in ("wartet", "freigegeben", "abgelehnt", "zurueckgezogen"):
        raise HTTPException(400, "Status ungültig.")
    with tx("admin") as cur:
        cur.execute("""SELECT f.id, f.titel, f.art, f.inhalt, f.status, f.angefragt_am, f.angefragt_von, f.entschieden_am, f.entschieden_name, f.entschieden_ip, f.kommentar,
                              k.id AS kunden_id, k.kundennummer, k.firma,
                              (SELECT coalesce(json_agg(json_build_object('id', d.id, 'name', d.name, 'groesse', d.groesse) ORDER BY d.erstellt_am), '[]'::json) FROM dateien d WHERE d.freigabe_id = f.id) AS dateien
                       FROM kundenfreigaben f JOIN kunden k ON k.id = f.kunden_id
                       WHERE (%s = '' OR f.status = %s) ORDER BY (f.status = 'wartet') DESC, f.angefragt_am DESC LIMIT 300""", (status, status))
        return cur.fetchall()


@router.post("/kunden/{kid}/freigaben-kunden")
def a_freigabe_neu(kid: str, data: FreigabeIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("SELECT ansprechpartner FROM kunden WHERE id=%s", (kid,))
            k = cur.fetchone()
            if not k:
                raise nicht_gefunden()
            cur.execute("INSERT INTO kundenfreigaben (kunden_id, titel, art, inhalt, angefragt_von) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                        (kid, data.titel.strip(), data.art, (data.inhalt or "").strip() or None, team_name(user)))
            fid = cur.fetchone()["id"]
            ziele = kunden_empfaenger(cur, kid)
            audit(cur, user, "kundenfreigabe_angefragt", kid, {"titel": data.titel})
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    _mails(bg, ziele, mailer.freigabe_anfrage_kunde, k["ansprechpartner"], data.titel)
    return {"id": fid}


@router.post("/freigaben-kunden/{fid}/dateien")
def a_freigabe_datei(fid: str, datei: UploadFile = File(...), user: dict = Depends(require_admin)):
    name, mime, daten = dateien.lesen(datei)
    try:
        with tx("admin") as cur:
            cur.execute("SELECT kunden_id FROM kundenfreigaben WHERE id=%s", (fid,))
            f = cur.fetchone()
            if not f:
                raise nicht_gefunden()
            cur.execute("""INSERT INTO dateien (kunden_id, freigabe_id, bereich, name, mime, groesse, daten, von, hochgeladen_von) VALUES (%s,%s,'anhang',%s,%s,%s,%s,'team',%s) RETURNING id""",
                        (f["kunden_id"], fid, name, mime, len(daten), daten, user["id"]))
            return {"id": cur.fetchone()["id"]}
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()


@router.post("/freigaben-kunden/{fid}/zurueckziehen")
def a_freigabe_zurueck(fid: str, user: dict = Depends(require_admin)):
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE kundenfreigaben SET status='zurueckgezogen' WHERE id=%s AND status='wartet' RETURNING kunden_id", (fid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(400, "Nur wartende Freigaben können zurückgezogen werden.")
            audit(cur, user, "kundenfreigabe_zurueckgezogen", r["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise nicht_gefunden()
    return {"ok": True}
