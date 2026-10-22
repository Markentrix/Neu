"""Zufriedenheitsumfrage (im Portal, 0–10), Einwilligungen der Kunden (mit Nachweis) und die Auswertung für das Team.
Umfragen per Mail sind Werbung im Sinne des UWG und gehen nur mit Einwilligung; im Portal selbst wird ohne Mail gefragt."""
from fastapi import APIRouter, Depends, HTTPException, Request
from psycopg import errors
from pydantic import BaseModel, Field

from . import einstellungen, mailer
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin, require_inhaber, require_kunde

kunde = APIRouter(prefix="/api/kunde")
admin = APIRouter(prefix="/api/admin")


def einwilligung(cur, kid, art="umfrage_mail") -> bool:
    cur.execute("SELECT erteilt FROM kunden_einwilligungen WHERE kunden_id=%s AND art=%s ORDER BY zeit DESC LIMIT 1", (kid, art))
    r = cur.fetchone()
    return bool(r and r["erteilt"])


def bewertungslink(cur) -> str:
    return (einstellungen.lesen(cur, "umfrage") or {}).get("bewertungslink") or ""


# ---------------------------------------------------------------- Kunde
@kunde.get("/umfrage")
def offene_umfrage(user: dict = Depends(require_kunde)):
    with tx("system") as cur:
        cur.execute("SELECT id, art, angelegt_am FROM kunden_umfragen WHERE kunden_id=%s AND beantwortet_am IS NULL AND NOT verfallen", (user["kunden_id"],))
        return {"offen": cur.fetchone()}


class UmfrageIn(BaseModel):
    punkte: int = Field(ge=0, le=10)
    kommentar: str = Field(default="", max_length=1500)


@kunde.post("/umfrage/{uid}")
def beantworten(uid: str, data: UmfrageIn, user: dict = Depends(require_kunde)):
    rate_limit("umfrage:" + str(user["kunden_id"]), 10, 600)
    try:
        with tx("system") as cur:
            cur.execute("""UPDATE kunden_umfragen SET punkte=%s, kommentar=%s, beantwortet_am=now() WHERE id=%s AND kunden_id=%s AND beantwortet_am IS NULL AND NOT verfallen RETURNING id""",
                        (data.punkte, " ".join(data.kommentar.split()) or None, uid, user["kunden_id"]))
            if not cur.fetchone():
                raise HTTPException(404, "Nicht gefunden.")
            cur.execute("SELECT firma, kundennummer FROM kunden WHERE id=%s", (user["kunden_id"],))
            k = cur.fetchone()
            link = bewertungslink(cur) if data.punkte >= 9 else ""
            an = admin_empfaenger(cur) if data.punkte <= 6 else None
            audit(cur, user, "umfrage_beantwortet", user["kunden_id"], {"punkte": data.punkte})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    if an:
        try:
            mailer.umfrage_unzufrieden(an, k["firma"], k["kundennummer"], data.punkte, " ".join(data.kommentar.split()), str(user["kunden_id"]))
        except Exception:  # noqa: BLE001
            pass
    return {"ok": True, "bewertungslink": link}


@kunde.get("/einwilligungen")
def einwilligungen_lesen(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("SELECT art, erteilt, zeit FROM kunden_einwilligungen WHERE kunden_id=%s ORDER BY zeit DESC LIMIT 20", (user["kunden_id"],))
        verlauf = cur.fetchall()
        aktuell = einwilligung(cur, user["kunden_id"])
        cur.execute("""SELECT id, unterschrieben_am, widerrufen_am FROM vertragsdokumente WHERE kunden_id=%s AND art='referenz' AND unterschrieben_am IS NOT NULL ORDER BY erstellt_am DESC LIMIT 1""", (user["kunden_id"],))
        ref = cur.fetchone()
    return {"umfrage_mail": aktuell, "verlauf": verlauf, "referenz": ref}


class EinwIn(BaseModel):
    umfrage_mail: bool


@kunde.put("/einwilligungen")
def einwilligungen_setzen(data: EinwIn, request: Request, user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        if einwilligung(cur, user["kunden_id"]) != data.umfrage_mail:
            cur.execute("INSERT INTO kunden_einwilligungen (kunden_id, art, erteilt, ip, benutzer) VALUES (%s,'umfrage_mail',%s,%s,%s)", (user["kunden_id"], data.umfrage_mail, client_ip(request), user["email"]))
            audit(cur, user, "einwilligung_umfrage_mail" if data.umfrage_mail else "einwilligung_umfrage_mail_widerrufen", user["kunden_id"], {})
    return {"ok": True}


# ---------------------------------------------------------------- Admin
@admin.get("/umfragen")
def auswertung(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT u.id, u.kunden_id, k.firma, u.art, u.punkte, u.kommentar, u.beantwortet_am FROM kunden_umfragen u JOIN kunden k ON k.id=u.kunden_id
                       WHERE u.beantwortet_am IS NOT NULL ORDER BY u.beantwortet_am DESC LIMIT 200""")
        antworten = cur.fetchall()
        cur.execute("SELECT count(*) AS n FROM kunden_umfragen WHERE beantwortet_am IS NULL AND NOT verfallen")
        offen = cur.fetchone()["n"]
        cur.execute("""SELECT to_char(date_trunc('quarter', beantwortet_am), 'YYYY-"Q"Q') AS quartal, count(*) AS n,
                              count(*) FILTER (WHERE punkte >= 9) AS foerderer, count(*) FILTER (WHERE punkte <= 6) AS kritiker
                       FROM kunden_umfragen WHERE beantwortet_am IS NOT NULL GROUP BY 1 ORDER BY 1 DESC LIMIT 8""")
        quartale = [{**q, "nps": round(100 * (q["foerderer"] - q["kritiker"]) / q["n"])} for q in cur.fetchall()]
        link = bewertungslink(cur)
        cur.execute("SELECT count(DISTINCT kunden_id) AS n FROM kunden_einwilligungen e WHERE erteilt AND zeit = (SELECT max(zeit) FROM kunden_einwilligungen x WHERE x.kunden_id=e.kunden_id AND x.art=e.art)")
        mit_einw = cur.fetchone()["n"]
    n = len(antworten)
    nps = round(100 * (sum(1 for a in antworten if a["punkte"] >= 9) - sum(1 for a in antworten if a["punkte"] <= 6)) / n) if n else None
    return {"nps": nps, "antworten": antworten, "anzahl": n, "offen": offen, "quartale": quartale, "bewertungslink": link, "mit_einwilligung": mit_einw}


class UmfrageEinst(BaseModel):
    bewertungslink: str = Field(default="", max_length=400, pattern=r"^(https://\S+)?$")


@admin.put("/umfragen/einstellungen")
def einst(data: UmfrageEinst, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "umfrage", {"bewertungslink": data.bewertungslink})
        audit(cur, user, "einstellungen_umfrage", None, {})
    return {"ok": True}
