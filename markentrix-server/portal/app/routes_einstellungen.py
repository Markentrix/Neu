from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import config, einstellungen, mailer
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
        "ki": {"key_gesetzt": bool(ki.get("api_key")), "modell": ki.get("modell", STANDARD_MODELL), "tageslimit": ki.get("tageslimit", 50)},
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


@router.put("/ki")
def ki_speichern(data: KiIn, user: dict = Depends(require_admin)):
    if not config.PORTAL_SECRET:
        raise HTTPException(500, "PORTAL_SECRET fehlt in der .env. Bitte install.sh erneut ausführen.")
    with tx("admin") as cur:
        alt = einstellungen.lesen(cur, "ki")
        neu = {"api_key": data.api_key.strip() or alt.get("api_key", ""), "modell": data.modell.strip() or STANDARD_MODELL, "tageslimit": data.tageslimit}
        einstellungen.schreiben(cur, "ki", neu)
        audit(cur, user, "einstellungen_ki", None, {"modell": neu["modell"]})
    return {"ok": True}


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
