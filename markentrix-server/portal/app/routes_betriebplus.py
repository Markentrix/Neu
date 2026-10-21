"""Betrieb Plus: Mail-Zustellbarkeit (Admin und Kunde), Datenexport und Kündigungswunsch durch den Kunden."""
import json
import re
import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from . import config, einstellungen, mailer, offboarding, push, zustellung
from . import sitedienste as sd
from .db import tx
from .routes_websites import auftrag
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit, rate_limit, require_admin, require_inhaber

admin = APIRouter(prefix="/api/admin")
kunde = APIRouter(prefix="/api/kunde")


# ---------------------------------------------------------------- Zustellbarkeit
def _domain(adresse: str | None) -> str:
    return (adresse or "").rsplit("@", 1)[-1].strip().lower() if adresse and "@" in adresse else ""


def _dns_ansicht(cur, domain: str, neu_pruefen: bool = False) -> dict | None:
    if not domain:
        return None
    r = zustellung.lesen(cur, domain)
    if neu_pruefen or not r:
        p = zustellung.pruefen_domain(domain)
        zustellung.speichern(cur, p)
        r = zustellung.lesen(cur, domain)
    return {"domain": r["domain"], "geprueft_am": r["geprueft_am"], "spf": r["spf"], "dkim": r["dkim"], "dmarc": r["dmarc"], "details": r["details"]}


def _admin_zustellung(neu: bool) -> dict:
    with tx("admin") as cur:
        smtp = einstellungen.lesen(cur, "smtp") or {}
        sys_domain = _domain(smtp.get("absender"))
    # DNS-Abfragen dauern: außerhalb der Datenbank-Transaktion
    if neu and sys_domain:
        p = zustellung.pruefen_domain(sys_domain)
        with tx("admin") as cur:
            zustellung.speichern(cur, p)
    with tx("admin") as cur:
        system = _dns_ansicht(cur, sys_domain)
        cur.execute("""SELECT z.kunden_id, k.firma, z.smtp_absender FROM website_dienste z JOIN kunden k ON k.id = z.kunden_id
                       WHERE z.smtp_absender IS NOT NULL AND z.smtp_enc IS NOT NULL ORDER BY k.firma LIMIT 200""")
        eigene = cur.fetchall()
    kunden = []
    for e in eigene:
        d = _domain(e["smtp_absender"])
        if neu and d and d != sys_domain:
            p = zustellung.pruefen_domain(d)
            with tx("admin") as cur:
                zustellung.speichern(cur, p)
        with tx("admin") as cur:
            ans = _dns_ansicht(cur, d)
            kz = zustellung.kennzahlen(cur, e["kunden_id"], 30)
        kunden.append({"kunden_id": str(e["kunden_id"]), "firma": e["firma"], "absender": e["smtp_absender"], "dns": ans, "fehler30": kz["fehler"], "gesamt30": kz["gesamt"]})
    with tx("admin") as cur:
        kz = zustellung.kennzahlen(cur, None, 7)
    return {"absender": smtp.get("absender") or "", "system": system, "kennzahlen": kz, "kunden": kunden}


@admin.get("/zustellung")
def a_zustellung(user: dict = Depends(require_admin)):
    return _admin_zustellung(False)


@admin.post("/zustellung/pruefen")
def a_zustellung_pruefen(user: dict = Depends(require_admin)):
    rate_limit("zustellpruefung-admin", 12, 3600)
    return _admin_zustellung(True)


@kunde.get("/website-dienste/zustellung")
def k_zustellung(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        d = _domain(z.get("smtp_absender")) if z.get("smtp_enc") else ""
        ans = _dns_ansicht(cur, d) if d else None
        kz = zustellung.kennzahlen(cur, kid, 30)
    return {"eigenes_postfach": bool(d), "absender": z.get("smtp_absender") if d else "", "dns": ans, "kennzahlen": kz}


@kunde.post("/website-dienste/zustellung/pruefen")
def k_zustellung_pruefen(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    rate_limit("zustellpruefung:" + str(kid), 6, 3600)
    with tx("system") as cur:
        z = sd.zeile(cur, kid)
        d = _domain(z.get("smtp_absender")) if z.get("smtp_enc") else ""
    if not d:
        raise HTTPException(400, "Es ist kein eigenes Postfach eingerichtet. Die Mails gehen dann über Markentrix.")
    p = zustellung.pruefen_domain(d)
    with tx("system") as cur:
        zustellung.speichern(cur, p)
    return k_zustellung(user)


# ---------------------------------------------------------------- Datenexport und Kündigung (Kunde)
@kunde.get("/datenexport.zip")
def k_export(user: dict = Depends(require_inhaber)):
    """Alle Daten des Kunden als ZIP (Anfragen, Termine, Rechnungen als PDF, Berichte, Website-Dateien …). Recht auf Datenübertragbarkeit, Art. 20 DSGVO."""
    kid = user["kunden_id"]
    rate_limit("datenexport:" + str(kid), 3, 3600)
    with tx("system") as cur:
        cur.execute("SELECT kundennummer, geloescht_am FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        if not k or k["geloescht_am"]:
            raise HTTPException(404, "Keine Daten vorhanden.")
        daten = offboarding.export_zip(cur, kid, fuer_kunde=True)
        audit(cur, user, "kunde_datenexport_selbst", kid)
    return Response(daten, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="Datenexport-{k["kundennummer"]}.zip"', "Cache-Control": "no-store"})


class KuendigungIn(BaseModel):
    grund: str = Field(default="", max_length=1500)
    wunschdatum: date | None = None
    bestaetigt: bool = False


def _offen(cur, kid):
    cur.execute("SELECT id, grund, wunschdatum, erstellt_am, von_name FROM kuendigungswuensche WHERE kunden_id=%s AND status='offen' ORDER BY erstellt_am DESC LIMIT 1", (kid,))
    return cur.fetchone()


@kunde.get("/kuendigung")
def k_kuendigung(user: dict = Depends(require_inhaber)):
    with tx("system") as cur:
        o = _offen(cur, user["kunden_id"])
    return {"offen": o}


@kunde.post("/kuendigung")
def k_kuendigung_senden(data: KuendigungIn, user: dict = Depends(require_inhaber)):
    """Kündigungswunsch in Textform. Er wird mit Zeitpunkt festgehalten; die Bearbeitung (Frist laut Vertrag, Bestätigung) übernimmt das Team."""
    kid = user["kunden_id"]
    rate_limit("kuendigung:" + str(kid), 5, 3600)
    if not data.bestaetigt:
        raise HTTPException(400, "Bitte bestätige, dass du kündigen möchtest.")
    if data.wunschdatum and data.wunschdatum < date.today():
        raise HTTPException(400, "Das Wunschdatum liegt in der Vergangenheit.")
    with tx("system") as cur:
        if _offen(cur, kid):
            raise HTTPException(400, "Dein Kündigungswunsch ist schon eingegangen. Wir melden uns.")
        cur.execute("SELECT firma, kundennummer, email FROM kunden WHERE id=%s", (kid,))
        k = cur.fetchone()
        cur.execute("INSERT INTO kuendigungswuensche (kunden_id, grund, wunschdatum, von_name, von_email) VALUES (%s,%s,%s,%s,%s) RETURNING id, erstellt_am",
                    (kid, data.grund.strip() or None, data.wunschdatum, user.get("name"), user.get("email")))
        neu = cur.fetchone()
        audit(cur, user, "kuendigungswunsch", kid, {"wunschdatum": str(data.wunschdatum or "")})
        ids = push.admins(cur)
        an_admin = admin_empfaenger(cur)
    wann = neu["erstellt_am"].astimezone(sd.TZ).strftime("%d.%m.%Y %H:%M")
    if ids:
        push.senden(ids, "Kündigungswunsch", f"{k['firma']} möchte kündigen.", "/admin#kunden", "kuendigung")
    if mailer.konfiguriert():
        if an_admin:
            mailer.senden(an_admin, f"Kündigungswunsch: {k['firma']} ({k['kundennummer']})",
                          f"{k['firma']} hat am {wann} im Kundenportal einen Kündigungswunsch gesendet.\n\nWunschdatum: {data.wunschdatum or 'nicht angegeben'}\nGrund: {data.grund.strip() or 'nicht angegeben'}\n\n"
                          "Bitte Vertragsfrist prüfen und schriftlich bestätigen." + mailer.SIGNATUR)
        ziel = user.get("email") or k["email"]
        if ziel:
            mailer.senden(ziel, "Dein Kündigungswunsch ist bei uns eingegangen",
                          f"Guten Tag,\n\ndein Kündigungswunsch ist am {wann} bei uns eingegangen" + (f" (gewünschtes Ende: {data.wunschdatum:%d.%m.%Y})" if data.wunschdatum else "") +
                          ". Wir prüfen die Vertragsfrist und bestätigen dir den Zeitpunkt schriftlich. Bis dahin läuft alles wie gewohnt weiter.\n\n"
                          "Deine Daten kannst du jederzeit unter Konto → „Meine Daten herunterladen“ als ZIP sichern." + mailer.SIGNATUR, kunden_id=kid, art="kuendigung")
    return {"ok": True, "eingegangen": wann}


@kunde.delete("/kuendigung")
def k_kuendigung_zurueck(user: dict = Depends(require_inhaber)):
    kid = user["kunden_id"]
    with tx("system") as cur:
        cur.execute("UPDATE kuendigungswuensche SET status='zurueckgenommen', bearbeitet_am=now() WHERE kunden_id=%s AND status='offen'", (kid,))
        n = cur.rowcount
        audit(cur, user, "kuendigungswunsch_zurueckgenommen", kid)
    if not n:
        raise HTTPException(404, "Es liegt kein offener Kündigungswunsch vor.")
    return {"ok": True}


@admin.get("/kuendigungswuensche")
def a_kuendigungen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        cur.execute("""SELECT w.id, w.kunden_id, k.firma, k.kundennummer, w.grund, w.wunschdatum, w.erstellt_am, w.von_name, w.status
                       FROM kuendigungswuensche w JOIN kunden k ON k.id = w.kunden_id WHERE w.status = 'offen' ORDER BY w.erstellt_am""")
        return cur.fetchall()


@admin.post("/kuendigungswuensche/{wid}/bearbeitet")
def a_kuendigung_fertig(wid: str, user: dict = Depends(require_admin)):
    from psycopg import errors
    try:
        with tx("admin") as cur:
            cur.execute("UPDATE kuendigungswuensche SET status='bearbeitet', bearbeitet_am=now() WHERE id=%s AND status='offen' RETURNING kunden_id", (wid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Nicht gefunden.")
            audit(cur, user, "kuendigungswunsch_bearbeitet", r["kunden_id"])
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Nicht gefunden.")
    return {"ok": True}


# ---------------------------------------------------------------- Daten eines Kunden aus der Datenbanksicherung zurückholen
TAG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}$")
UID_RE = re.compile(r"^[0-9a-f]{16}$")
IDENT_RE = re.compile(r"^[a-z0-9_]+$")


class AuszugIn(BaseModel):
    tag: str


@admin.get("/datensicherungen")
def a_db_sicherungen(user: dict = Depends(require_admin)):
    try:
        d = json.loads((config.QUEUE_DIR / "sicherungen.json").read_text())
        return {"tage": [t for t in d.get("db_tage", []) if TAG_RE.match(str(t))], "stand": d.get("stand")}
    except (OSError, ValueError):
        return {"tage": [], "stand": None}


@admin.post("/kunden/{kid}/auszug")
def a_auszug_anfordern(kid: str, data: AuszugIn, user: dict = Depends(require_admin)):
    """Der Server liest die Zeilen dieses Kunden aus der gewählten Sicherung in eine Prüfansicht. Die laufende Datenbank bleibt unberührt."""
    from psycopg import errors
    if not TAG_RE.match(data.tag):
        raise HTTPException(400, "Ungültiges Sicherungsdatum.")
    rate_limit("auszug-admin", 10, 3600)
    try:
        with tx("admin") as cur:
            cur.execute("SELECT 1 FROM kunden WHERE id=%s", (kid,))
            if not cur.fetchone():
                raise HTTPException(404, "Kunde nicht gefunden.")
            audit(cur, user, "kundenauszug_angefordert", kid, {"tag": data.tag})
    except errors.InvalidTextRepresentation:
        raise HTTPException(404, "Kunde nicht gefunden.")
    uid = secrets.token_hex(8)
    auftrag({"aktion": "kundenauszug", "kunden_id": kid, "tag": data.tag, "upload": uid})
    return {"id": uid, "hinweis": "Der Server liest die Sicherung. Das dauert je nach Größe einige Minuten."}


def _auszug_datei(uid: str):
    if not UID_RE.match(uid):
        raise HTTPException(404, "Nicht gefunden.")
    return config.QUEUE_DIR / f"kundenauszug-{uid}.json", config.QUEUE_DIR / f"ergebnis-{uid}.json"


def _tabelle_ok(cur, name: str) -> bool:
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name=%s", (name,))
    return bool(IDENT_RE.match(name) and cur.fetchone())


def _spalten(cur, name: str) -> list[str]:
    cur.execute("""SELECT a.attname FROM pg_attribute a WHERE a.attrelid = to_regclass(%s) AND a.attnum > 0 AND NOT a.attisdropped AND a.attgenerated = '' ORDER BY a.attnum""", ('public."' + name + '"',))
    return [r["attname"] for r in cur.fetchall()]


def _schluessel(cur, name: str) -> list[str]:
    cur.execute("""SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                   WHERE i.indrelid = to_regclass(%s) AND i.indisprimary""", ('public."' + name + '"',))
    return [r["attname"] for r in cur.fetchall()]


@admin.get("/kunden/auszug/{uid}")
def a_auszug(uid: str, user: dict = Depends(require_admin)):
    from psycopg import sql as S
    datei, erg = _auszug_datei(uid)
    if not datei.is_file():
        if erg.is_file():
            try:
                e = json.loads(erg.read_text())
                if not e.get("ok"):
                    return {"status": "fehler", "text": e.get("text", "Fehlgeschlagen.")}
            except ValueError:
                pass
        return {"status": "laeuft"}
    try:
        a = json.loads(datei.read_text())
    except (OSError, ValueError):
        raise HTTPException(500, "Der Auszug ist nicht lesbar.")
    zeilen = []
    with tx("admin") as cur:
        for name, rows in sorted(a["tabellen"].items()):
            if not _tabelle_ok(cur, name):
                continue
            pk = _schluessel(cur, name)
            if not pk:
                continue
            cond = S.SQL(" AND ").join(S.SQL("l.{c} = r.{c}").format(c=S.Identifier(c)) for c in pk)
            cur.execute(S.SQL("SELECT count(*) AS n FROM jsonb_populate_recordset(null::{t}, %s::jsonb) r WHERE NOT EXISTS (SELECT 1 FROM {t} l WHERE {cond})").format(
                t=S.Identifier("public", name), cond=cond), (json.dumps(rows),))
            fehlt = cur.fetchone()["n"]
            zeilen.append({"tabelle": name, "in_sicherung": len(rows), "fehlt_jetzt": fehlt})
    return {"status": "bereit", "tag": a["tag"], "kunden_id": a["kunden_id"], "tabellen": zeilen, "ohne_dateiinhalt": a.get("ohne_dateiinhalt", [])}


class ZurueckIn(BaseModel):
    tabellen: list[str] = Field(min_length=1, max_length=80)


@admin.post("/kunden/auszug/{uid}/zurueckspielen")
def a_auszug_zurueck(uid: str, data: ZurueckIn, user: dict = Depends(require_admin)):
    """Spielt nur FEHLENDE Zeilen zurück (nichts wird überschrieben oder gelöscht). Zeilen, deren Verknüpfungen fehlen, werden in mehreren Durchgängen versucht."""
    from psycopg import errors, sql as S
    datei, _ = _auszug_datei(uid)
    if not datei.is_file():
        raise HTTPException(404, "Der Auszug ist nicht mehr vorhanden. Bitte neu anfordern.")
    rate_limit("auszug-zurueck", 20, 3600)
    a = json.loads(datei.read_text())
    wahl = [t for t in data.tabellen if t in a["tabellen"]]
    if not wahl:
        raise HTTPException(400, "Keine passende Tabelle gewählt.")
    ergebnis = {t: {"zurueck": 0, "uebrig": 0} for t in wahl}
    with tx("admin") as cur:
        offen = {t: list(a["tabellen"][t]) for t in wahl if _tabelle_ok(cur, t)}
        for _runde in range(5):
            fortschritt = False
            for t, rows in offen.items():
                cols = _spalten(cur, t)
                ids = S.SQL(", ").join(S.Identifier(c) for c in cols)
                rest = []
                for row in rows:
                    cur.execute("SAVEPOINT z")
                    try:
                        cur.execute(S.SQL("INSERT INTO {t} ({c}) OVERRIDING SYSTEM VALUE SELECT {c} FROM jsonb_populate_record(null::{t}, %s::jsonb) ON CONFLICT DO NOTHING").format(
                            t=S.Identifier("public", t), c=ids), (json.dumps(row),))
                        if cur.rowcount:
                            ergebnis[t]["zurueck"] += 1
                            fortschritt = True
                        cur.execute("RELEASE SAVEPOINT z")
                    except (errors.ForeignKeyViolation, errors.NotNullViolation, errors.CheckViolation, errors.InvalidTextRepresentation):
                        cur.execute("ROLLBACK TO SAVEPOINT z")
                        rest.append(row)
                offen[t] = rest
            if not fortschritt or not any(offen.values()):
                break
        for t, rows in offen.items():
            ergebnis[t]["uebrig"] = len(rows)
        audit(cur, user, "kundendaten_aus_sicherung", a["kunden_id"], {"tag": a["tag"], "ergebnis": {t: v for t, v in ergebnis.items() if v["zurueck"] or v["uebrig"]}})
    return {"ok": True, "ergebnis": ergebnis}


@admin.delete("/kunden/auszug/{uid}")
def a_auszug_loeschen(uid: str, user: dict = Depends(require_admin)):
    """Entfernt den Auszug sofort (enthält personenbezogene Daten)."""
    datei, erg = _auszug_datei(uid)
    for f in (datei, erg):
        try:
            f.unlink()
        except OSError:
            pass
    return {"ok": True}
