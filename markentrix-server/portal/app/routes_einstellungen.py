from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, einstellungen, jobs, ki, mailer, rechtstexte
from .db import tx
from .ki import STANDARD_MODELL
from .security import EMAIL_RE, audit, rate_limit, require_admin

router = APIRouter(prefix="/api/admin/einstellungen")


@router.get("")
def lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        smtp = einstellungen.lesen(cur, "smtp")
        ki = einstellungen.lesen(cur, "ki")
    return {
        "geheimnis_ok": bool(config.PORTAL_SECRET),
        "smtp": {"host": smtp.get("host", ""), "port": smtp.get("port", 587), "sicherung": smtp.get("sicherung", "starttls"),
                 "benutzer": smtp.get("benutzer", ""), "passwort_gesetzt": bool(smtp.get("passwort")),
                 "absender": smtp.get("absender", ""), "absender_name": smtp.get("absender_name", "Markentrix")},
        "ki": {"key_gesetzt": bool(ki.get("api_key")), "modell": ki.get("modell", STANDARD_MODELL), "tageslimit": ki.get("tageslimit", 50),
               "preis_ein_eur": ki.get("preis_ein_eur", 3.0), "preis_aus_eur": ki.get("preis_aus_eur", 15.0)},
    }


class SmtpIn(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    sicherung: str = "starttls"
    benutzer: str = Field(default="", max_length=254)
    passwort: str = Field(default="", max_length=300)
    absender: str = Field(max_length=254)
    absender_name: str = Field(default="Markentrix", max_length=100)


@router.put("/smtp")
def smtp_speichern(data: SmtpIn, user: dict = Depends(require_admin)):
    if data.sicherung not in ("starttls", "ssl", "keine"):
        raise HTTPException(400, "Unbekannte Verschlüsselung.")
    if not EMAIL_RE.match(data.absender.strip()):
        raise HTTPException(400, "Die Absender-Adresse ist ungültig.")
    if not config.PORTAL_SECRET:
        raise HTTPException(500, "PORTAL_SECRET fehlt in der .env. Bitte install.sh erneut ausführen.")
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "smtp")
        neu = data.model_dump()
        neu["host"] = neu["host"].strip()
        neu["absender"] = neu["absender"].strip()
        if not neu["passwort"]:
            neu["passwort"] = alt.get("passwort", "")      # leer lassen = unverändert
        einstellungen.schreiben(cur, "smtp", neu)
        audit(cur, user, "einstellungen_smtp", None, {"host": neu["host"]})
    return {"ok": True}


class KiIn(BaseModel):
    api_key: str = Field(default="", max_length=300)
    modell: str = Field(default=STANDARD_MODELL, max_length=80)
    tageslimit: int = Field(default=50, ge=1, le=1000)
    preis_ein_eur: float = Field(default=3.0, ge=0, le=1000)
    preis_aus_eur: float = Field(default=15.0, ge=0, le=1000)


@router.put("/ki")
def ki_speichern(data: KiIn, user: dict = Depends(require_admin)):
    if not config.PORTAL_SECRET:
        raise HTTPException(500, "PORTAL_SECRET fehlt in der .env. Bitte install.sh erneut ausführen.")
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "ki")
        neu = {"api_key": data.api_key.strip() or alt.get("api_key", ""), "modell": data.modell.strip() or STANDARD_MODELL, "tageslimit": data.tageslimit,
               "preis_ein_eur": data.preis_ein_eur, "preis_aus_eur": data.preis_aus_eur}
        einstellungen.schreiben(cur, "ki", neu)
        audit(cur, user, "einstellungen_ki", None, {"modell": neu["modell"]})
    return {"ok": True}


@router.post("/ki-test")
def ki_test(user: dict = Depends(require_admin)):
    """Kleine Testfrage an den KI-Dienst mit den gespeicherten Einstellungen. Bei einem Fehler steht der genaue Grund in der Antwort."""
    rate_limit("ki-test:" + user["email"], 10, 600)
    with tx("admin") as cur:
        cfg = einstellungen.lesen(cur, "ki")
    if not cfg.get("api_key"):
        raise HTTPException(400, "Es ist noch kein API-Key gespeichert.")
    modell = cfg.get("modell") or STANDARD_MODELL
    try:
        antwort, _e, _a = ki.fragen(cfg["api_key"], modell, "Antworte mit genau einem Wort.", [{"role": "user", "content": "Sag OK."}], 20)
    except Exception as e:
        ki.fehler(e, user, "")
        raise HTTPException(400, f"Der Test ist fehlgeschlagen. Grund: {ki.grund(e)} (Modell: {modell})")
    return {"ok": True, "modell": modell, "antwort": antwort[:80]}


class TestIn(BaseModel):
    an: str


@router.post("/testmail")
def testmail(data: TestIn, user: dict = Depends(require_admin)):
    rate_limit("testmail:" + user["email"], 10, 600)
    if not EMAIL_RE.match(data.an.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    ok, fehler = mailer.senden(data.an.strip(), "Testnachricht Markentrix-Portal", "Das ist eine Testnachricht. Der E-Mail-Versand funktioniert.\n\nIhr Markentrix-Team")
    if not ok:
        raise HTTPException(400, "Versand fehlgeschlagen: " + fehler)
    return {"ok": True}


# ---------------------------------------------------------------- Firmendaten und Rechtstexte
class FirmaIn(BaseModel):
    name: str = Field(default="", max_length=200)
    inhaber: str = Field(default="", max_length=200)
    strasse: str = Field(default="", max_length=200)
    plz: str = Field(default="", max_length=10)
    ort: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=254)
    telefon: str = Field(default="", max_length=60)
    website: str = Field(default="", max_length=200)
    ustid: str = Field(default="", max_length=30)
    steuernummer: str = Field(default="", max_length=40)
    kleinunternehmer: bool = False
    iban: str = Field(default="", max_length=40)
    bic: str = Field(default="", max_length=20)
    bank: str = Field(default="", max_length=100)
    zahlungsziel_tage: int = Field(default=14, ge=0, le=90)
    mwst_satz: int = Field(default=19, ge=0, le=30)
    rechnungsprefix: str = Field(default="RE", max_length=8, pattern=r"^[A-Za-z0-9-]*$")
    angebotsprefix: str = Field(default="AN", max_length=8, pattern=r"^[A-Za-z0-9-]*$")
    fusszeile: str = Field(default="", max_length=300)
    angebotsbedingungen: str = Field(default="", max_length=1500)   # erscheint unter jedem Angebot (PDF und Online-Seite)


@router.get("/firma")
def firma_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return rechtstexte.firma(cur)


@router.put("/firma")
def firma_speichern(data: FirmaIn, user: dict = Depends(require_admin)):
    if data.email and not EMAIL_RE.match(data.email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "firma", data.model_dump())
        audit(cur, user, "einstellungen_firma")
    return {"ok": True}


class RechtIn(BaseModel):
    impressum: str = Field(default="", max_length=20000)
    datenschutz: str = Field(default="", max_length=40000)


@router.get("/recht")
def recht_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        f = rechtstexte.firma(cur)
        r = einstellungen.lesen(cur, "recht")
    return {"impressum": r.get("impressum", ""), "datenschutz": r.get("datenschutz", ""),
            "impressum_standard": rechtstexte.impressum_standard(f), "datenschutz_standard": rechtstexte.datenschutz_standard(f),
            "nutzung_satz": rechtstexte.NUTZUNG_SATZ, "nutzung_fehlt": bool(r.get("datenschutz", "").strip()) and "Seitenname, Tag und Rolle" not in r.get("datenschutz", "")}


@router.put("/recht")
def recht_speichern(data: RechtIn, user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "recht", data.model_dump())
        audit(cur, user, "einstellungen_recht")
    return {"ok": True}


# ---------------------------------------------------------------- Benachrichtigungen
class BenachrIn(BaseModel):
    alarm_email: str = Field(default="", max_length=254)
    anfrage_mails: bool = True
    termin_erinnerung: bool = True
    termin_stunden: int = Field(default=24, ge=1, le=168)
    monatsbericht: bool = True


@router.get("/benachrichtigung")
def benachr_lesen(user: dict = Depends(require_admin)):
    with tx("admin") as cur:
        return jobs.einstellungen_lesen(cur)


@router.put("/benachrichtigung")
def benachr_speichern(data: BenachrIn, user: dict = Depends(require_admin)):
    if data.alarm_email and not EMAIL_RE.match(data.alarm_email.strip()):
        raise HTTPException(400, "Die E-Mail-Adresse ist ungültig.")
    with tx("admin") as cur:
        einstellungen.schreiben(cur, "benachrichtigung", data.model_dump())
        audit(cur, user, "einstellungen_benachrichtigung")
    return {"ok": True}
