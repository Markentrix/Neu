"""Admin: Änderungen an Leistungen und Preisen prüfen, die ein Kunde im Portal gemacht hat (nur bei Kunden mit Freigabepflicht)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import push
from . import sitedienste as sd
from .db import tx
from .routes_sitedienste import LeistungIn, _leistung_aendern, _leistung_neu, _leistung_weg
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin/kunden")


def _kunde(cur, kid: str):
    try:
        cur.execute("SELECT id FROM kunden WHERE id=%s", (kid,))
    except Exception:
        raise HTTPException(404, "Kunde nicht gefunden.")
    if not cur.fetchone():
        raise HTTPException(404, "Kunde nicht gefunden.")


@router.get("/{kid}/leistungs-aenderungen")
def liste(kid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _kunde(cur, kid)
        z = sd.zeile(cur, kid)
        cur.execute("""SELECT a.*, l.name AS alt_name, l.preis AS alt_preis, l.dauer_min AS alt_dauer FROM website_leistung_aenderungen a LEFT JOIN website_leistungen l ON l.id=a.leistung_id
                       WHERE a.kunden_id=%s AND (a.status='offen' OR a.bearbeitet_am > now() - interval '14 days') ORDER BY (a.status='offen') DESC, a.erstellt_am DESC LIMIT 60""", (kid,))
        return {"freigabe": z["leistungen_freigabe"], "aenderungen": [{"id": str(r["id"]), "aktion": r["aktion"], "name": r["name"], "daten": r["daten"], "status": r["status"], "notiz": r["notiz"] or "",
                                                                       "erstellt_am": r["erstellt_am"], "alt": {"name": r["alt_name"], "preis": r["alt_preis"], "dauer": r["alt_dauer"]} if r["alt_name"] else None}
                                                                      for r in cur.fetchall()]}


class FreigabeIn(BaseModel):
    freigabe: bool


@router.put("/{kid}/leistungs-freigabe")
def umstellen(kid: str, data: FreigabeIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        _kunde(cur, kid)
        sd.zeile(cur, kid)
        cur.execute("UPDATE website_dienste SET leistungen_freigabe=%s WHERE kunden_id=%s", (data.freigabe, kid))
        audit(cur, user, "leistungen_freigabe_umgestellt", kid, {"freigabe": data.freigabe})
    return {"ok": True}


class EntscheidungIn(BaseModel):
    notiz: str = Field(default="", max_length=500)


def _entscheiden(kid: str, aid: str, user: dict, uebernehmen: bool, notiz: str):
    with tx("system") as cur:
        _kunde(cur, kid)
        try:
            cur.execute("SELECT * FROM website_leistung_aenderungen WHERE id=%s AND kunden_id=%s FOR UPDATE", (aid, kid))
        except Exception:
            raise HTTPException(404, "Änderung nicht gefunden.")
        a = cur.fetchone()
        if not a:
            raise HTTPException(404, "Änderung nicht gefunden.")
        if a["status"] != "offen":
            raise HTTPException(409, "Diese Änderung ist schon bearbeitet.")
        if uebernehmen:
            if a["aktion"] == "loeschen":
                _leistung_weg(cur, kid, a["leistung_id"])
            else:
                daten = LeistungIn(**a["daten"]).pruefen()
                if a["aktion"] == "neu":
                    _leistung_neu(cur, kid, daten)
                else:
                    _leistung_aendern(cur, kid, a["leistung_id"], daten)
        cur.execute("UPDATE website_leistung_aenderungen SET status=%s, notiz=%s, bearbeitet_am=now() WHERE id=%s", ("uebernommen" if uebernehmen else "abgelehnt", notiz.strip() or None, aid))
        cur.execute("UPDATE aufgaben SET status='erledigt', erledigt_am=now(), erledigt_von=%s WHERE auto_schluessel=%s AND status='offen'", (user.get("email"), f"leistung-{aid}"))
        audit(cur, user, "leistung_" + ("uebernommen" if uebernehmen else "abgelehnt"), kid, {"name": a["name"], "aktion": a["aktion"]})
        ids = push.kunde(cur, kid)
    push.senden(ids, "Deine Leistungs-Änderung" if uebernehmen else "Änderung abgelehnt", f"„{a['name'][:60]}“: " + ("ist jetzt live." if uebernehmen else (notiz.strip()[:120] or "abgelehnt.")), "/app#dienste", "leistung")
    return {"ok": True}


@router.post("/{kid}/leistungs-aenderungen/{aid}/uebernehmen")
def uebernehmen(kid: str, aid: str, user: dict = Depends(require_admin)):
    return _entscheiden(kid, aid, user, True, "")


@router.post("/{kid}/leistungs-aenderungen/{aid}/ablehnen")
def ablehnen(kid: str, aid: str, data: EntscheidungIn, user: dict = Depends(require_admin)):
    return _entscheiden(kid, aid, user, False, data.notiz)
