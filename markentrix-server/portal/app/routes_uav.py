"""Änderungen bei Unterauftragsverarbeitern ankündigen (AVV Ziff. 5 Abs. 2): vier Wochen Vorlauf, Information in Textform, Widerspruch im Portal."""
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from psycopg import errors
from pydantic import BaseModel, Field

from . import avv, mailer
from .db import tx
from .security import audit, rate_limit, require_admin, require_inhaber

router = APIRouter(prefix="/api/admin")
kunde_router = APIRouter(prefix="/api/kunde")
VORLAUF_TAGE = 28
AKTIV = "('onboarding','aktiv','pausiert')"


class AenderungIn(BaseModel):
    art: str = Field(pattern="^(neu|ersetzt)$")
    name: str = Field(min_length=2, max_length=200)
    leistung: str = Field(min_length=3, max_length=400)
    modul: str = Field(default="", max_length=40)
    ort: str = Field(default="", max_length=200)
    wirksam_ab: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    hinweis: str = Field(default="", max_length=1500)


def betroffene(cur, modul: str | None) -> list:
    """Kunden mit abgelegtem AVV. Bei einem Modul nur die, die es nutzen; Kunden mit alter Fassung (ohne Modulangabe) werden immer informiert."""
    cur.execute(f"""SELECT k.id, k.firma, k.email, k.ansprechpartner FROM kunden k
                    WHERE k.status IN {AKTIV}
                      AND EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.datei IS NOT NULL AND a.unterschrieben_am IS NOT NULL)
                      AND (%s::text IS NULL
                           OR NOT EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.version=%s AND a.datei IS NOT NULL)
                           OR EXISTS (SELECT 1 FROM avv a WHERE a.kunden_id=k.id AND a.version=%s AND a.datei IS NOT NULL AND jsonb_exists(a.anlage->'module', %s)))
                    ORDER BY k.firma""", (modul, avv.VERSION, avv.VERSION, modul))
    return cur.fetchall()


@router.post("/uav-aenderungen")
def anlegen(data: AenderungIn, user: dict = Depends(require_admin)):
    if data.modul and data.modul not in avv.MODUL_KEYS:
        raise HTTPException(400, "Unbekanntes Modul.")
    try:
        wirksam = date.fromisoformat(data.wirksam_ab)
    except ValueError:
        raise HTTPException(400, "Das Datum ist ungültig.")
    fruehestens = date.today() + timedelta(days=VORLAUF_TAGE)
    if wirksam < fruehestens:
        raise HTTPException(400, f"Laut AVV braucht die Ankündigung mindestens vier Wochen Vorlauf. Frühestens möglich: {fruehestens.strftime('%d.%m.%Y')}.")
    with tx("admin") as cur:
        cur.execute("""INSERT INTO uav_aenderungen (art, name, leistung, modul, ort, wirksam_ab, hinweis, erstellt_von) VALUES (%s,%s,%s,NULLIF(%s,''),NULLIF(%s,''),%s,NULLIF(%s,''),%s) RETURNING id""",
                    (data.art, data.name.strip(), data.leistung.strip(), data.modul, data.ort.strip(), wirksam, data.hinweis.strip(), user["id"]))
        aid = cur.fetchone()["id"]
        kunden = betroffene(cur, data.modul or None)
        for k in kunden:
            cur.execute("INSERT INTO uav_mitteilungen (aenderung_id, kunden_id, email) VALUES (%s,%s,%s)", (aid, k["id"], (k["email"] or "").strip() or None))
        audit(cur, user, "uav_aenderung_angekuendigt", None, {"aenderung": str(aid), "name": data.name.strip(), "kunden": len(kunden)})
    gesendet = fehlt = 0
    for k in kunden:
        an = (k["email"] or "").strip()
        ok = False
        if an:
            ok, _f = mailer.uav_aenderung(an, k["ansprechpartner"], data.art, data.name.strip(), data.leistung.strip(), wirksam.strftime("%d.%m.%Y"), data.hinweis.strip())
        if ok:
            gesendet += 1
            with tx("admin") as cur:
                cur.execute("UPDATE uav_mitteilungen SET gesendet_am=now() WHERE aenderung_id=%s AND kunden_id=%s", (aid, k["id"]))
        else:
            fehlt += 1
    return {"id": aid, "kunden": len(kunden), "gesendet": gesendet, "ohne_mail": fehlt}


@router.get("/uav-aenderungen")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT a.id, a.art, a.name, a.leistung, a.modul, a.wirksam_ab, a.erstellt_am,
                              (SELECT count(*) FROM uav_mitteilungen m WHERE m.aenderung_id=a.id) AS kunden,
                              (SELECT count(*) FROM uav_mitteilungen m WHERE m.aenderung_id=a.id AND m.gesendet_am IS NOT NULL) AS gesendet,
                              (SELECT count(*) FROM uav_mitteilungen m WHERE m.aenderung_id=a.id AND m.widerspruch_am IS NOT NULL) AS widersprueche
                       FROM uav_aenderungen a ORDER BY a.erstellt_am DESC LIMIT 50""")
        rows = cur.fetchall()
        for r in rows:
            cur.execute("""SELECT m.kunden_id, k.firma, m.gesendet_am, m.widerspruch_am, m.widerspruch_grund, m.widerspruch_von
                           FROM uav_mitteilungen m JOIN kunden k ON k.id=m.kunden_id WHERE m.aenderung_id=%s AND m.widerspruch_am IS NOT NULL ORDER BY m.widerspruch_am""", (r["id"],))
            r["widerspruch_liste"] = cur.fetchall()
    return rows


# ---------------------------------------------------------------- Kundenseite
@kunde_router.get("/uav-aenderungen")
def kunde_liste(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        cur.execute("""SELECT m.id, a.art, a.name, a.leistung, a.hinweis, a.wirksam_ab, a.erstellt_am, m.widerspruch_am, (a.wirksam_ab > current_date) AS widerspruch_moeglich
                       FROM uav_mitteilungen m JOIN uav_aenderungen a ON a.id=m.aenderung_id WHERE m.kunden_id=%s ORDER BY a.erstellt_am DESC LIMIT 20""", (user["kunden_id"],))
        return cur.fetchall()


class WiderspruchIn(BaseModel):
    grund: str = Field(min_length=10, max_length=1500)
    name: str = Field(min_length=3, max_length=200)


@kunde_router.post("/uav-aenderungen/{mid}/widerspruch")
def widerspruch(mid: str, data: WiderspruchIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    rate_limit("uavw:" + str(user["kunden_id"]), 5, 600)
    kid = user["kunden_id"]
    grund = " ".join(data.grund.split())
    name = " ".join(data.name.split())
    try:
        with tx("system") as cur:
            cur.execute("""SELECT m.id, a.name AS uav, a.wirksam_ab, m.widerspruch_am, k.firma, k.kundennummer FROM uav_mitteilungen m
                           JOIN uav_aenderungen a ON a.id=m.aenderung_id JOIN kunden k ON k.id=m.kunden_id WHERE m.id=%s AND m.kunden_id=%s""", (mid, kid))
            m = cur.fetchone()
            if not m:
                raise HTTPException(404, "Nicht gefunden.")
            if m["widerspruch_am"]:
                raise HTTPException(400, "Der Widerspruch wurde schon eingelegt.")
            if m["wirksam_ab"] <= date.today():
                raise HTTPException(400, "Die Frist für den Widerspruch ist abgelaufen. Bitte wende dich direkt an uns.")
            cur.execute("UPDATE uav_mitteilungen SET widerspruch_am=now(), widerspruch_grund=%s, widerspruch_von=%s WHERE id=%s", (grund, name, mid))
            audit(cur, user, "uav_widerspruch", kid, {"mitteilung": str(mid), "uav": m["uav"]})
            from .routes_zusammenarbeit import admin_empfaenger
            an = admin_empfaenger(cur)
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    if an:
        bg.add_task(mailer.uav_widerspruch_team, an, m["firma"], m["kundennummer"], m["uav"], name, grund, str(kid))
    return {"ok": True}
