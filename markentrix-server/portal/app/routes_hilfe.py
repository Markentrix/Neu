"""Hilfe-Suche: Rückmeldung „Problem gelöst?“. Ungelöste Fragen landen beim Admin (Übersicht + Mail)."""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from . import anleitung_pdf, einstellungen, mailer
from .db import tx
from .security import audit, current_user, require_admin

router = APIRouter(prefix="/api")


class RueckIn(BaseModel):
    frage: str = Field(min_length=1, max_length=500)
    artikel: str | None = Field(default=None, max_length=200)
    geloest: bool
    text: str | None = Field(default=None, max_length=2000)


@router.post("/hilfe/rueckmeldung")
def rueckmeldung(data: RueckIn, user: dict = Depends(current_user)):
    rolle = "admin" if user.get("rolle") == "admin" else "vertrieb" if user.get("vertriebspartner_id") else "kunde"
    with tx("system") as cur:
        cur.execute("""INSERT INTO hilfe_rueckmeldungen (rolle, benutzer_id, kunden_id, vertriebspartner_id, name, email, frage, artikel, geloest, text)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (rolle, user.get("id"), user.get("kunden_id"), user.get("vertriebspartner_id"), user.get("name"), user.get("email"),
                     data.frage.strip(), data.artikel, data.geloest, (data.text or "").strip() or None))
        rid = cur.fetchone()["id"]
        firma = einstellungen.lesen(cur, "firma")
        wer = user.get("name") or user.get("email") or "?"
        if rolle == "kunde" and user.get("kunden_id"):
            cur.execute("SELECT firma, kundennummer FROM kunden WHERE id=%s", (user["kunden_id"],))
            k = cur.fetchone()
            if k:
                wer += f" ({k['firma']}, Kundennr. {k['kundennummer']})"
    if not data.geloest and firma.get("email"):
        mailer.senden(firma["email"], f"Hilfe-Suche: Problem nicht gelöst ({rolle})",
                      f"{wer} hat in der Hilfe-Suche ({rolle}) ein Problem nicht lösen können.\n\nFrage: {data.frage}\n"
                      f"Angezeigte Anleitung: {data.artikel or 'keine passende gefunden'}\nNachricht: {data.text or '-'}\n"
                      f"E-Mail der Person: {user.get('email') or '-'}\n\nBitte im Admin-Bereich unter Übersicht → „Hilfe-Rückmeldungen“ ansehen und als erledigt markieren.")
    return {"ok": True, "id": str(rid)}


@router.get("/admin/hilfe-rueckmeldungen")
def liste(user: dict = Depends(require_admin)):
    with tx("system") as cur:
        cur.execute("""SELECT id, rolle, name, email, frage, artikel, text, erstellt_am FROM hilfe_rueckmeldungen
                       WHERE NOT geloest AND status='offen' ORDER BY erstellt_am DESC LIMIT 50""")
        offen = cur.fetchall()
        cur.execute("""SELECT count(*) FILTER (WHERE geloest) AS geloest, count(*) FILTER (WHERE NOT geloest) AS ungeloest
                       FROM hilfe_rueckmeldungen WHERE erstellt_am > now() - interval '30 days'""")
        z = cur.fetchone()
    return {"offen": offen, "geloest_30": int(z["geloest"]), "ungeloest_30": int(z["ungeloest"])}


@router.post("/admin/hilfe-rueckmeldungen/{rid}/erledigt")
def erledigt(rid: str, user: dict = Depends(require_admin)):
    with tx("system") as cur:
        cur.execute("UPDATE hilfe_rueckmeldungen SET status='erledigt', erledigt_am=now() WHERE id=%s", (rid,))
        if not cur.rowcount:
            raise HTTPException(404, "Nicht gefunden.")
        audit(cur, user, "hilfe_erledigt", None, {"id": rid})
    return {"ok": True}


def _rolle(user: dict) -> str:
    return "admin" if user.get("rolle") == "admin" else "vertrieb" if user.get("vertriebspartner_id") else "kunde"


@router.get("/hilfe/artikel")
def artikel(rolle: str | None = None, user: dict = Depends(current_user)):
    eigene = _rolle(user)
    r = rolle if (eigene == "admin" and rolle in anleitung_pdf.ROLLEN) else eigene
    return anleitung_pdf.laden(r)


@router.get("/hilfe/anleitung.pdf")
def anleitung(rolle: str | None = None, user: dict = Depends(current_user)):
    eigene = _rolle(user)
    r = rolle if (eigene == "admin" and rolle in anleitung_pdf.ROLLEN) else eigene
    with tx("system") as cur:
        firma = einstellungen.lesen(cur, "firma")
    return Response(anleitung_pdf.bauen(r, firma), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="Markentrix-Anleitung-{r}.pdf"', "Cache-Control": "private, no-store"})
