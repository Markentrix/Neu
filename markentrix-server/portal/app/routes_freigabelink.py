"""Freigabe per Mail-Link ohne Anmeldung: Kunde sieht die Bitte, die Anhänge und entscheidet. Name ist Pflicht, Zeit und IP werden festgehalten."""
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from psycopg import errors
from pydantic import BaseModel, Field

from . import dateien, mailer
from .db import tx
from .routes_zusammenarbeit import _mails, admin_empfaenger
from .security import audit, client_ip, rate_limit, token_hash

router = APIRouter(prefix="/api/freigabe-link")


def _holen(cur, token: str) -> dict:
    cur.execute("""SELECT f.id, f.kunden_id, f.titel, f.art, f.inhalt, f.status, f.version, f.angefragt_am, f.entschieden_am, f.entschieden_name, f.kommentar, f.link_ablauf, k.firma,
                          (SELECT v.kommentar FROM kundenfreigaben v WHERE v.id = f.vorgaenger_id) AS vorgaenger_kommentar
                   FROM kundenfreigaben f JOIN kunden k ON k.id = f.kunden_id WHERE f.link_hash=%s""", (token_hash(token),))
    f = cur.fetchone()
    if not f:
        raise HTTPException(404, "Dieser Link ist nicht (mehr) gültig. Bitte melden Sie sich im Portal an oder fragen Sie bei uns nach einem neuen Link.")
    return f


@router.get("/{token}")
def ansehen(token: str, request: Request):
    rate_limit("freigabelink:" + client_ip(request), 60, 600)
    with tx("system") as cur:
        f = _holen(cur, token)
        cur.execute("SELECT id, name, mime, groesse FROM dateien WHERE freigabe_id=%s ORDER BY erstellt_am", (f["id"],))
        d = cur.fetchall()
    abgelaufen = f["link_ablauf"] is not None and f["link_ablauf"] < datetime.now(timezone.utc)
    return {"titel": f["titel"], "art": f["art"], "inhalt": f["inhalt"], "status": f["status"], "version": f["version"], "firma": f["firma"], "angefragt_am": f["angefragt_am"],
            "entschieden_am": f["entschieden_am"], "entschieden_name": f["entschieden_name"], "kommentar": f["kommentar"], "vorgaenger_kommentar": f["vorgaenger_kommentar"],
            "abgelaufen": abgelaufen and f["status"] == "wartet", "dateien": d}


@router.get("/{token}/datei/{did}")
def datei(token: str, did: str, request: Request):
    rate_limit("freigabedatei:" + client_ip(request), 120, 600)
    try:
        with tx("system") as cur:
            f = _holen(cur, token)
            cur.execute("SELECT name, mime, daten FROM dateien WHERE id=%s AND freigabe_id=%s", (did, f["id"]))
            x = cur.fetchone()
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    if not x:
        raise HTTPException(404, "Nicht gefunden.")
    return dateien.antwort(x["name"], x["mime"], x["daten"])


class EntscheidungLinkIn(BaseModel):
    entscheidung: str = Field(pattern="^(freigegeben|abgelehnt)$")
    name: str = Field(min_length=3, max_length=200)
    kommentar: str | None = Field(default=None, max_length=2000)


@router.post("/{token}/entscheiden")
def entscheiden(token: str, data: EntscheidungLinkIn, request: Request, bg: BackgroundTasks):
    rate_limit("freigabeok:" + client_ip(request), 20, 600)
    name = " ".join(data.name.split())
    kommentar = (data.kommentar or "").strip() or None
    if data.entscheidung == "abgelehnt" and not kommentar:
        raise HTTPException(400, "Bitte schreiben Sie kurz, was geändert werden soll.")
    with tx("system") as cur:
        f = _holen(cur, token)
        if f["status"] != "wartet":
            raise HTTPException(400, "Darüber wurde schon entschieden.")
        if f["link_ablauf"] is not None and f["link_ablauf"] < datetime.now(timezone.utc):
            raise HTTPException(400, "Der Link ist abgelaufen. Bitte melden Sie sich im Portal an oder fragen Sie bei uns nach einem neuen Link.")
        cur.execute("""UPDATE kundenfreigaben SET status=%s, kommentar=%s, entschieden_am=now(), entschieden_name=%s, entschieden_ip=%s, ueber_link=true WHERE id=%s AND status='wartet'""",
                    (data.entscheidung, kommentar, name, client_ip(request), f["id"]))
        audit(cur, None, "kundenfreigabe_" + data.entscheidung + "_link", f["kunden_id"], {"titel": f["titel"], "name": name})
        an = admin_empfaenger(cur)
    _mails(bg, an, mailer.freigabe_entschieden_team, f["firma"], f["titel"], data.entscheidung, kommentar, name + " (per Mail-Link)")
    return {"ok": True}
