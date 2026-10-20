"""Nutzungsmessung: welche Seiten werden wirklich genutzt? Gespeichert werden nur Seitenname, Tag und Rolle sowie, wer an einem Tag aktiv war. Keine Inhalte, nach 180 Tagen gelöscht."""
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .db import tx
from .security import current_user, rate_limit, require_admin

router = APIRouter(prefix="/api")
SEITE = re.compile(r"^[a-z0-9_-]{1,30}$")


class NutzungIn(BaseModel):
    seite: str


@router.post("/me/nutzung")
def melden(data: NutzungIn, user: dict = Depends(current_user)):
    rate_limit("nutzung:" + str(user["id"]), 300, 3600)
    if not SEITE.match(data.seite) or user["rolle"] not in ("admin", "kunde", "vertrieb"):
        return {"ok": False}
    with tx("system") as cur:
        cur.execute("INSERT INTO nutzung_seiten (tag, rolle, seite, n) VALUES (current_date, %s, %s, 1) ON CONFLICT (tag, rolle, seite) DO UPDATE SET n = nutzung_seiten.n + 1", (user["rolle"], data.seite))
        cur.execute("INSERT INTO nutzung_aktiv (tag, benutzer_id, rolle) VALUES (current_date, %s, %s) ON CONFLICT DO NOTHING", (user["id"], user["rolle"]))
    return {"ok": True}


@router.get("/admin/nutzung")
def auswertung(tage: int = 30, user: dict = Depends(require_admin)):
    tage = max(7, min(tage, 180))
    with tx("admin") as cur:
        cur.execute("SELECT rolle, seite, sum(n)::int AS aufrufe FROM nutzung_seiten WHERE tag > current_date - %s GROUP BY rolle, seite ORDER BY rolle, aufrufe DESC", (tage,))
        seiten = cur.fetchall()
        cur.execute("""SELECT rolle, count(DISTINCT benutzer_id)::int AS personen FROM nutzung_aktiv WHERE tag > current_date - %s GROUP BY rolle""", (tage,))
        aktiv = {r["rolle"]: r["personen"] for r in cur.fetchall()}
        cur.execute("""SELECT rolle, count(DISTINCT benutzer_id)::int AS personen FROM nutzung_aktiv WHERE tag > current_date - 7 GROUP BY rolle""")
        aktiv7 = {r["rolle"]: r["personen"] for r in cur.fetchall()}
        cur.execute("SELECT rolle, count(*)::int AS n FROM benutzer WHERE aktiv AND rolle IN ('kunde','vertrieb','admin') GROUP BY rolle")
        gesamt = {r["rolle"]: r["n"] for r in cur.fetchall()}
        cur.execute("SELECT count(*) FILTER (WHERE (ansicht->>'tour_gesehen') = 'true')::int AS gesehen, count(*)::int AS alle FROM benutzer WHERE aktiv AND rolle='kunde'")
        tour = cur.fetchone()
        cur.execute("SELECT min(tag) AS seit FROM nutzung_seiten")
        seit = cur.fetchone()["seit"]
    return {"tage": tage, "seiten": seiten, "aktiv": aktiv, "aktiv_7_tage": aktiv7, "konten": gesamt, "tour": tour, "messung_seit": seit}


def aufraeumen(cur) -> int:
    cur.execute("DELETE FROM nutzung_seiten WHERE tag < current_date - 180")
    n = cur.rowcount
    cur.execute("DELETE FROM nutzung_aktiv WHERE tag < current_date - 180")
    return n + cur.rowcount
