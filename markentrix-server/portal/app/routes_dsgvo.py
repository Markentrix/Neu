"""Anfragen nach Art. 15 bis 21 DSGVO (Auskunft, Löschung, Berichtigung, Widerspruch …): erfassen, Frist von einem Monat überwachen,
betroffene Daten finden, Auskunft als Datei erzeugen, Leads löschen. Kundenkonten werden weiter über den Offboarding-Ablauf beendet.
Die rechtliche Bewertung (z. B. ob eine Löschung zulässig ist) liegt beim Anwalt."""
import json
import re
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import config, mailer, push, sperre
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, client_ip, rate_limit, require_admin

public = APIRouter(prefix="/api/public")
admin = APIRouter(prefix="/api/admin/datenschutz-anfragen")
ARTEN = "auskunft|loeschung|berichtigung|widerspruch|einschraenkung|uebertragung|sonstiges"
ART_TEXT = {"auskunft": "Auskunft", "loeschung": "Löschung", "berichtigung": "Berichtigung", "widerspruch": "Widerspruch", "einschraenkung": "Einschränkung",
            "uebertragung": "Datenübertragung", "sonstiges": "Sonstiges"}
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[A-Za-z]{2,}$")


def _anlegen(cur, art, name, email, telefon, nachricht, quelle, eingang=None) -> str:
    eingang = eingang or date.today()
    cur.execute("""INSERT INTO datenschutz_anfragen (art, name, email, telefon, nachricht, quelle, eingang_am, frist_am)
                   VALUES (%s,%s,%s,%s,%s,%s,%s, (%s::date + interval '1 month')::date) RETURNING id, frist_am""",
                (art, name.strip(), (email or "").strip().lower() or None, (telefon or "").strip() or None, nachricht, quelle, eingang, eingang))
    r = cur.fetchone()
    cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel)
                   VALUES (NULL, %s, %s, %s, 'auto', %s) ON CONFLICT (auto_schluessel) DO NOTHING""",
                (f"Datenschutz-Anfrage ({ART_TEXT[art]}) von {name.strip()[:80]}: Frist {r['frist_am'].strftime('%d.%m.%Y')}", admin_empfaenger(cur), r["frist_am"], f"dsgvo-{r['id']}"))
    return r["id"]


class OeffentlichIn(BaseModel):
    art: str = Field(pattern=f"^({ARTEN})$")
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(max_length=320)
    nachricht: str | None = Field(default=None, max_length=3000)
    zweitfeld: str | None = Field(default=None, max_length=200)


@public.post("/datenschutz-anfrage")
def oeffentlich(d: OeffentlichIn, request: Request, bg: BackgroundTasks):
    rate_limit("dsgvo-anfrage:" + client_ip(request), 5, 3600)
    if d.zweitfeld:
        return {"ok": True}
    if not EMAIL.match(d.email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    with tx("system") as cur:
        aid = _anlegen(cur, d.art, d.name, d.email, None, (d.nachricht or "").strip() or None, "formular")
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
    push.senden(ids, "Datenschutz-Anfrage eingegangen", f"{ART_TEXT[d.art]} von {d.name.strip()}. Frist: ein Monat.", "/admin#dsgvo", "dsgvo")
    if an:
        bg.add_task(mailer.senden, an, "Neue Datenschutz-Anfrage", f"{ART_TEXT[d.art]}-Anfrage von {d.name.strip()} ({d.email.strip()}). Die Frist beträgt einen Monat.\n\n{config.BASE_URL}/admin#dsgvo")
    return {"ok": True, "id": str(aid)}


class AnlegenIn(BaseModel):
    art: str = Field(pattern=f"^({ARTEN})$")
    name: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    telefon: str | None = Field(default=None, max_length=60)
    nachricht: str | None = Field(default=None, max_length=3000)
    quelle: str = Field(default="manuell", pattern="^(manuell|mail|brief|telefon)$")
    eingang_am: date | None = None


@admin.get("")
def liste(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT *, (status IN ('neu','in_arbeit') AND frist_am < current_date) AS ueberfaellig,
                              (status IN ('neu','in_arbeit') AND frist_am - current_date <= 7) AS bald
                       FROM datenschutz_anfragen ORDER BY (status IN ('neu','in_arbeit')) DESC, frist_am LIMIT 300""")
        rows = cur.fetchall()
    for r in rows:
        r["art_text"] = ART_TEXT[r["art"]]
    return {"anfragen": rows, "offen": sum(1 for r in rows if r["status"] in ("neu", "in_arbeit")), "ueberfaellig": sum(1 for r in rows if r["ueberfaellig"])}


@admin.post("")
def anlegen(d: AnlegenIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        aid = _anlegen(cur, d.art, d.name, d.email, d.telefon, d.nachricht, d.quelle, d.eingang_am)
        audit(cur, user, "dsgvo_anlegen", None, {"id": str(aid), "art": d.art})
    return {"id": str(aid)}


class AendernIn(BaseModel):
    status: str = Field(pattern="^(neu|in_arbeit|erledigt|abgelehnt)$")
    identitaet_geprueft: bool = False
    notiz: str | None = Field(default=None, max_length=3000)


@admin.put("/{aid}")
def aendern(aid: str, d: AendernIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""UPDATE datenschutz_anfragen SET status=%s, identitaet_geprueft=%s, notiz=%s,
                         erledigt_am = CASE WHEN %s IN ('erledigt','abgelehnt') THEN coalesce(erledigt_am, current_date) ELSE NULL END WHERE id=%s RETURNING id""",
                    (d.status, d.identitaet_geprueft, d.notiz, d.status, aid))
        if not cur.fetchone():
            raise HTTPException(404, "Anfrage nicht gefunden.")
        audit(cur, user, "dsgvo_aendern", None, {"id": aid, "status": d.status})
    return {"ok": True}


def _treffer(cur, a: dict) -> dict:
    email = (a["email"] or "").lower()
    tel = re.sub(r"\D", "", a["telefon"] or "")
    out = {"leads": [], "kunden": [], "benutzer": [], "partner": [], "sperrliste": []}
    if email:
        cur.execute("SELECT id, firma, ansprechpartner, email, telefon, status, erstellt_am FROM leads WHERE lower(email)=%s", (email,))
        out["leads"] = cur.fetchall()
        cur.execute("SELECT id, kundennummer, firma, ansprechpartner, email, status FROM kunden WHERE lower(email)=%s OR lower(benachr_email)=%s", (email, email))
        out["kunden"] = cur.fetchall()
        cur.execute("SELECT id, name, email, rolle, kunden_id FROM benutzer WHERE lower(email)=%s", (email,))
        out["benutzer"] = cur.fetchall()
        cur.execute("SELECT id, name, email, status FROM vertriebspartner WHERE lower(email)=%s", (email,))
        out["partner"] = cur.fetchall()
    if len(tel) >= 6:
        cur.execute("""SELECT id, firma, ansprechpartner, email, telefon, status, erstellt_am FROM leads
                       WHERE regexp_replace(coalesce(telefon,''), '\\D', '', 'g') = %s AND id <> ALL(%s::uuid[])""", (tel, [str(l["id"]) for l in out["leads"]]))
        out["leads"] += cur.fetchall()
    for art, wert in sperre.schluessel(email or None, a["telefon"], None):
        cur.execute("SELECT id, art, grund, erstellt_am FROM sperrliste WHERE art=%s AND wert=%s", (art, wert))
        out["sperrliste"] += cur.fetchall()
    return out


def _anfrage(cur, aid):
    cur.execute("SELECT * FROM datenschutz_anfragen WHERE id=%s", (aid,))
    a = cur.fetchone()
    if not a:
        raise HTTPException(404, "Anfrage nicht gefunden.")
    return a


@admin.get("/{aid}/suche")
def suche(aid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return _treffer(cur, _anfrage(cur, aid))


@admin.get("/{aid}/auskunft")
def auskunft(aid: str, user: dict = Depends(require_admin)):
    """Auskunftsdatei (JSON) mit allen gefundenen Daten der Person. Kundenkonten: Datenexport über die Kundenakte."""
    with tx("admin") as cur:
        a = _anfrage(cur, aid)
        t = _treffer(cur, a)
        ids = [str(l["id"]) for l in t["leads"]]
        daten = {"erstellt_am": date.today().isoformat(), "anfrage": {"art": ART_TEXT[a["art"]], "name": a["name"], "eingang_am": a["eingang_am"].isoformat()},
                 "leads": [], "benutzer": t["benutzer"], "kunden": t["kunden"], "vertriebspartner": t["partner"], "sperrliste": [{"art": s["art"], "grund": s["grund"], "seit": s["erstellt_am"]} for s in t["sperrliste"]]}
        for lid in ids:
            cur.execute("SELECT firma, ansprechpartner, email, telefon, website, branche, plz, ort, quelle, status, notiz, erstellt_am, loeschen_nach FROM leads WHERE id=%s", (lid,))
            l = cur.fetchone()
            cur.execute("SELECT art, inhalt, zeit, von FROM lead_aktivitaeten WHERE lead_id=%s ORDER BY zeit", (lid,))
            l["verlauf"] = cur.fetchall()
            cur.execute("SELECT website, score, erstellt_am FROM lead_checks WHERE lead_id=%s", (lid,))
            l["website_checks"] = cur.fetchall()
            daten["leads"].append(l)
        audit(cur, user, "dsgvo_auskunft", None, {"id": aid, "leads": len(ids)})
    return Response(json.dumps(daten, ensure_ascii=False, indent=2, default=str), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="auskunft-{aid[:8]}.json"'})


class LoeschenIn(BaseModel):
    lead_ids: list[str] = Field(min_length=1, max_length=50)
    sperren: bool = True


@admin.post("/{aid}/loeschen")
def loeschen(aid: str, d: LoeschenIn, user: dict = Depends(require_admin)):
    """Löscht gefundene Leads der Person (mit Verlauf). Auf Wunsch kommt die E-Mail-Adresse auf die Sperrliste, damit sie nicht erneut angesprochen wird."""
    with tx("admin") as cur:
        a = _anfrage(cur, aid)
        erlaubt = {str(l["id"]): l for l in _treffer(cur, a)["leads"]}
        weg, fehler = 0, []
        for lid in d.lead_ids:
            l = erlaubt.get(lid)
            if not l:
                fehler.append(f"{lid[:8]}: gehört nicht zu dieser Anfrage")
                continue
            try:
                with cur.connection.transaction():
                    if d.sperren:
                        sperre.eintragen(cur, "widerspruch", "Datenschutz-Anfrage", l["email"], l["telefon"], None)
                    cur.execute("DELETE FROM leads WHERE id=%s AND kunden_id IS NULL", (lid,))
                    if not cur.rowcount:
                        raise ValueError("Der Lead gehört zu einem Kunden. Bitte über die Kundenakte beenden.")
                weg += 1
            except Exception as e:  # noqa: BLE001
                fehler.append(f"{l['firma']}: {str(e)[:120] if isinstance(e, ValueError) else 'lässt sich nicht löschen (verknüpfte Belege)'}")
        if weg:
            cur.execute("INSERT INTO loeschprotokoll (tabelle, geloescht_anzahl, ausgeloest_durch) VALUES ('leads (Datenschutz-Anfrage)', %s, %s)", (weg, f"admin {user['email']}"))
        cur.execute("UPDATE datenschutz_anfragen SET status = CASE WHEN status='neu' THEN 'in_arbeit' ELSE status END WHERE id=%s", (aid,))
        audit(cur, user, "dsgvo_loeschen", None, {"id": aid, "geloescht": weg, "sperren": d.sperren})
    return {"geloescht": weg, "fehler": fehler}
