import json
import os
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import config
from .db import tx
from .security import audit, require_admin

router = APIRouter(prefix="/api/admin/websites")

SITES = config.SITES_ROOT
QUEUE = config.QUEUE_DIR
NAME = {"live": re.compile(r"^(?=.{4,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,}$"), "demo": re.compile(r"^[a-z0-9]([a-z0-9-]{0,40}[a-z0-9])?$")}
TRASH_ID = re.compile(r"^\d{8}-\d{6}__(live|demo)__[A-Za-z0-9.-]{1,253}$")


def groesse(d: Path):
    s = n = 0
    newest = 0
    for root, _dirs, files in os.walk(d):
        for f in files:
            try:
                st = os.lstat(os.path.join(root, f))
            except OSError:
                continue
            s += st.st_size
            n += 1
            newest = max(newest, st.st_mtime)
    return s, n, newest


def ausstehend():
    out = []
    if QUEUE.is_dir():
        for f in QUEUE.glob("auftrag-*.json"):
            try:
                out.append(json.loads(f.read_text()))
            except Exception:
                pass
    return out


@router.get("")
def liste(user: dict = Depends(require_admin)):
    offen = {(a.get("art"), a.get("name")) for a in ausstehend() if a.get("aktion") == "loeschen"}
    aktiv = []
    for art, sub in (("live", "live"), ("demo", "demos")):
        basis = SITES / sub
        if not basis.is_dir():
            continue
        for d in sorted(basis.iterdir()):
            if d.is_symlink() or not d.is_dir() or not NAME[art].match(d.name):
                continue
            s, n, new = groesse(d)
            kunde = ""
            try:
                kunde = str(json.loads((d / "site.json").read_text()).get("kunde", ""))
            except Exception:
                pass
            aktiv.append({"art": art, "name": d.name, "groesse": s, "dateien": n, "geaendert": new, "kunde": kunde,
                          "loeschung_laeuft": (art, d.name) in offen})
    korb = []
    t = SITES / ".papierkorb"
    if t.is_dir():
        for d in sorted(t.iterdir(), reverse=True):
            if TRASH_ID.match(d.name) and d.is_dir() and not d.is_symlink():
                art, name = d.name.split("__")[1:3]
                korb.append({"id": d.name, "art": art, "name": name, "geloescht": d.stat().st_mtime, "groesse": groesse(d)[0]})
    return {"aktiv": aktiv, "papierkorb": korb, "aufbewahrung_tage": 14}


def auftrag(daten: dict):
    try:
        QUEUE.mkdir(exist_ok=True, mode=0o770)
        p = QUEUE / f"auftrag-{secrets.token_hex(8)}.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(daten))
        os.replace(tmp, p)
    except OSError:
        raise HTTPException(500, "Der Auftrag konnte nicht abgelegt werden (Ordner queue fehlt oder ist nicht beschreibbar).")


class LoeschIn(BaseModel):
    art: str
    name: str
    bestaetigung: str


@router.post("/loeschen")
def loeschen(data: LoeschIn, user: dict = Depends(require_admin)):
    if data.art not in NAME or not NAME[data.art].match(data.name):
        raise HTTPException(400, "Ungültiger Name.")
    if data.bestaetigung.strip() != data.name:
        raise HTTPException(400, "Zur Bestätigung muss der Name genau eingetippt werden.")
    basis = SITES / ("live" if data.art == "live" else "demos") / data.name
    if basis.is_symlink() or not basis.is_dir():
        raise HTTPException(404, "Diese Seite gibt es nicht.")
    auftrag({"aktion": "loeschen", "art": data.art, "name": data.name})
    with tx("admin") as cur:
        if data.art == "live":
            cur.execute("UPDATE websites SET status='offline' WHERE domain=%s", (data.name,))
        audit(cur, user, "website_geloescht", None, {"art": data.art, "name": data.name})
    return {"ok": True, "hinweis": "Wird innerhalb einer Minute in den Papierkorb verschoben."}


class WiederIn(BaseModel):
    id: str


@router.post("/wiederherstellen")
def wiederherstellen(data: WiederIn, user: dict = Depends(require_admin)):
    if not TRASH_ID.match(data.id) or not (SITES / ".papierkorb" / data.id).is_dir():
        raise HTTPException(404, "Eintrag nicht gefunden.")
    auftrag({"aktion": "wiederherstellen", "id": data.id})
    with tx("admin") as cur:
        audit(cur, user, "website_wiederhergestellt", None, {"id": data.id})
    return {"ok": True, "hinweis": "Wird innerhalb einer Minute wiederhergestellt."}
