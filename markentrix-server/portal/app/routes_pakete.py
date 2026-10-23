"""Pakete und Zusatzleistungen: Kunden (auch Referenzkunden) sehen die Preisliste und buchen im Portal dazu.
Die Buchung entsteht als „angefragt“ mit eingefrorenem Preis. Aktiv wird sie erst, wenn Markentrix im Admin bestätigt."""
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from . import mailer, push
from .db import tx
from .routes_zusammenarbeit import admin_empfaenger, kunden_empfaenger
from .security import audit, require_admin, require_inhaber

router = APIRouter(prefix="/api")

KATEGORIEN = {"ki": "KI-Assistent", "website": "Website", "ci": "Marke und Design (CI)", "sichtbarkeit": "Sichtbarkeit", "personal_branding": "Personal Branding", "lead": "Leads und Werbung"}
LAUFEND = ("angefragt", "beauftragt", "in_einrichtung", "aktiv", "pausiert")

KATALOG = """SELECT p.code, p.kategorie, p.name, p.beschreibung, p.abrechnung, p.laufzeit_monate, p.nur_auf_anfrage, p.einzeln_buchbar,
                    pp.id AS preis_id, pp.einrichtung_cent, pp.monatlich_cent, pp.projekt_cent, pp.ab_preis
             FROM produkte p LEFT JOIN LATERAL (SELECT * FROM produkt_preise x WHERE x.produkt_code=p.code AND x.gueltig_ab<=current_date ORDER BY gueltig_ab DESC LIMIT 1) pp ON true
             WHERE p.aktiv {zusatz} ORDER BY p.sortierung"""


@router.get("/kunde/paketkatalog")
def katalog(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        cur.execute("SELECT referenzkunde FROM kunden WHERE id=%s", (kid,))
        referenz = bool(cur.fetchone()["referenzkunde"])
        cur.execute(KATALOG.format(zusatz=""))
        produkte = cur.fetchall()
        cur.execute("SELECT produkt_code, status, id FROM buchungen WHERE kunden_id=%s AND status = ANY(%s)", (kid, list(LAUFEND)))
        meine = {r["produkt_code"]: r for r in cur.fetchall()}
    gruppen: dict = {}
    for p in produkte:
        if not p["einzeln_buchbar"]:
            continue
        b = meine.get(p["code"])
        eintrag = {"code": p["code"], "name": p["name"], "beschreibung": p["beschreibung"], "abrechnung": p["abrechnung"], "laufzeit_monate": p["laufzeit_monate"],
                   "auf_anfrage": bool(p["nur_auf_anfrage"] or p["preis_id"] is None), "ab_preis": bool(p["ab_preis"]),
                   "einrichtung_cent": 0 if referenz else p["einrichtung_cent"], "monatlich_cent": 0 if referenz else p["monatlich_cent"], "projekt_cent": 0 if referenz else p["projekt_cent"],
                   "regulaer": {"einrichtung_cent": p["einrichtung_cent"], "monatlich_cent": p["monatlich_cent"], "projekt_cent": p["projekt_cent"]} if referenz else None,
                   "status": b["status"] if b else None}
        gruppen.setdefault(p["kategorie"], []).append(eintrag)
    return {"referenzkunde": referenz, "netto": True, "gruppen": [{"kategorie": k, "titel": KATEGORIEN.get(k, k), "produkte": v} for k, v in gruppen.items()]}


class DazuIn(BaseModel):
    bestaetigt: bool = False
    notiz: str | None = Field(default=None, max_length=1000)


def _eur(c) -> str:
    return f"{int(c or 0) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


@router.post("/kunde/pakete/{code}/dazubuchen")
def dazubuchen(code: str, data: DazuIn, bg: BackgroundTasks, user: dict = Depends(require_inhaber)):
    if not data.bestaetigt:
        raise HTTPException(400, "Bitte bestätige die Buchung mit dem Haken.")
    kid = user["kunden_id"]
    with tx("system") as cur:
        cur.execute("SELECT firma, kundennummer, referenzkunde, email FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        cur.execute(KATALOG.format(zusatz="AND p.code=%s AND p.einzeln_buchbar"), (code,))
        p = cur.fetchone()
        if not p:
            raise HTTPException(404, "Dieses Paket gibt es nicht.")
        cur.execute("SELECT status FROM buchungen WHERE kunden_id=%s AND produkt_code=%s AND status = ANY(%s)", (kid, code, list(LAUFEND)))
        if cur.fetchone():
            raise HTTPException(409, "Dieses Paket hast du schon gebucht oder angefragt.")
        # Wechsel innerhalb der KI-Pakete: Hinweis für Markentrix, kein automatisches Ersetzen
        wechsel = ""
        if p["kategorie"] == "ki":
            cur.execute("""SELECT p.name FROM buchungen b JOIN produkte p ON p.code=b.produkt_code WHERE b.kunden_id=%s AND p.kategorie='ki' AND b.status = ANY(%s)""", (kid, list(LAUFEND)))
            alt = [r["name"] for r in cur.fetchall()]
            if alt:
                wechsel = "Wechsel/Erweiterung, bisher: " + ", ".join(alt) + ". "
        auf_anfrage = bool(p["nur_auf_anfrage"] or p["preis_id"] is None)
        null = bool(k["referenzkunde"]) or auf_anfrage
        notiz = (wechsel + "Im Portal dazugebucht. " + (data.notiz or "")).strip()
        cur.execute("""INSERT INTO buchungen (kunden_id, produkt_code, preis_id, einrichtung_cent, monatlich_cent, projekt_cent, rabatt_cent, rabatt_grund, status, notiz)
                       VALUES (%s,%s,%s,%s,%s,%s,0,%s,'angefragt',%s) RETURNING id""",
                    (kid, code, None if auf_anfrage else p["preis_id"], None if auf_anfrage else (0 if k["referenzkunde"] else p["einrichtung_cent"]),
                     None if auf_anfrage else (0 if k["referenzkunde"] else p["monatlich_cent"]), None if auf_anfrage else (0 if k["referenzkunde"] else p["projekt_cent"]),
                     "Referenzkunde" if k["referenzkunde"] else None, notiz))
        bid = cur.fetchone()["id"]
        an = admin_empfaenger(cur)
        ids = push.admins(cur)
        if an:
            cur.execute("""INSERT INTO aufgaben (kunden_id, titel, zustaendig, faellig_am, quelle, auto_schluessel) VALUES (%s,%s,%s,current_date + 1,'auto',%s)
                           ON CONFLICT (auto_schluessel) DO NOTHING""", (kid, f"Paketbuchung prüfen: {k['firma']} · {p['name']}", an, f"paketbuchung-{bid}"))
        kunde_an = kunden_empfaenger(cur, kid)
        audit(cur, user, "paket_dazugebucht", kid, {"produkt": code, "buchung": str(bid), "referenz": bool(k["referenzkunde"])})
    preis = "auf Anfrage" if auf_anfrage else ("kostenfrei (Referenzkunde)" if null else
            " + ".join(x for x in [(_eur(p["einrichtung_cent"]) + " Einrichtung") if p["einrichtung_cent"] else "", (_eur(p["projekt_cent"]) + " einmalig") if p["projekt_cent"] else "",
                                   (_eur(p["monatlich_cent"]) + " pro Monat") if p["monatlich_cent"] else ""] if x) + " (netto)")
    if an:
        bg.add_task(mailer.senden, an, f"Neue Paketbuchung: {k['firma']} ({k['kundennummer']}) · {p['name']}",
                    f"{k['firma']} hat im Portal \"{p['name']}\" dazugebucht.\nPreis: {preis}\n{wechsel}Notiz: {data.notiz or '-'}\n\nBitte im Admin unter Übersicht → \"Neue Paketbuchungen\" bestätigen oder ablehnen." + mailer.SIGNATUR)
    if ids:
        bg.add_task(push.senden, ids, "Neue Paketbuchung", f"{k['firma']}: {p['name']}", "/admin#uebersicht", "paketbuchung")
    for a in kunde_an:
        bg.add_task(mailer.senden, a, f"Ihre Buchung: {p['name']}",
                    f"Hallo,\n\nvielen Dank. Wir haben Ihre Buchung \"{p['name']}\" erhalten.\nPreis: {preis}\n\nWir prüfen sie kurz, bestätigen Ihnen die Buchung und melden uns zur Einrichtung. Bis dahin entstehen keine Kosten." + mailer.SIGNATUR, None, None, None, kid)
    return {"ok": True, "id": str(bid), "hinweis": "Danke, wir haben deine Buchung erhalten und bestätigen sie in Kürze."}


# ---------------------------------------------------------------- Admin
@router.get("/admin/paket-buchungen")
def offene(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT b.id, b.kunden_id, k.firma, k.kundennummer, k.referenzkunde, p.name AS produkt, b.einrichtung_cent, b.monatlich_cent, b.projekt_cent, b.notiz, b.erstellt_am,
                              (b.preis_id IS NULL) AS auf_anfrage
                       FROM buchungen b JOIN kunden k ON k.id=b.kunden_id JOIN produkte p ON p.code=b.produkt_code
                       WHERE b.status='angefragt' ORDER BY b.erstellt_am LIMIT 50""")
        return cur.fetchall()


class BestaetigenIn(BaseModel):
    beginn: date | None = None


@router.post("/admin/buchungen/{bid}/bestaetigen")
def bestaetigen(bid: str, data: BestaetigenIn, bg: BackgroundTasks, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT b.kunden_id, b.produkt_code, b.preis_id, p.laufzeit_monate, p.name FROM buchungen b JOIN produkte p ON p.code=b.produkt_code
                       WHERE b.id=%s AND b.status='angefragt'""", (bid,))
        b = cur.fetchone()
        if not b:
            raise HTTPException(404, "Keine offene Buchung gefunden.")
        if b["preis_id"] is None:
            raise HTTPException(400, "Diese Buchung hat keinen festen Preis (auf Anfrage). Bitte zuerst im Kundenblatt unter Buchungen den Preis klären.")
        beginn = data.beginn or date.today()
        cur.execute("""UPDATE buchungen SET status='beauftragt', beginn=%s,
                              mindestlaufzeit_ende = CASE WHEN %s::int IS NOT NULL THEN (%s::date + make_interval(months=>%s::int))::date END WHERE id=%s""",
                    (beginn, b["laufzeit_monate"], beginn, b["laufzeit_monate"], bid))
        cur.execute("""INSERT INTO kunden_module (kunden_id, modul_code, aktiv) SELECT %s, modul_code, true FROM produkt_module WHERE produkt_code=%s
                       ON CONFLICT (kunden_id, modul_code) DO UPDATE SET aktiv=true, geaendert_am=now()""", (b["kunden_id"], b["produkt_code"]))
        an = kunden_empfaenger(cur, b["kunden_id"])
        audit(cur, user, "paket_bestaetigt", b["kunden_id"], {"buchung": bid, "produkt": b["produkt_code"]})
    for a in an:
        bg.add_task(mailer.senden, a, f"Bestätigt: {b['name']}", f"Hallo,\n\nIhre Buchung \"{b['name']}\" ist bestätigt. Wir melden uns zur Einrichtung. Den Stand sehen Sie jederzeit im Portal unter Pakete & Zusatzleistungen." + mailer.SIGNATUR, None, None, None, b["kunden_id"])
    return {"ok": True}


@router.post("/admin/buchungen/{bid}/ablehnen")
def ablehnen(bid: str, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("UPDATE buchungen SET status='beendet', ende=current_date, notiz=coalesce(notiz,'') || ' [abgelehnt]' WHERE id=%s AND status='angefragt' RETURNING kunden_id", (bid,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Keine offene Buchung gefunden.")
        audit(cur, user, "paket_abgelehnt", r["kunden_id"], {"buchung": bid})
    return {"ok": True}
