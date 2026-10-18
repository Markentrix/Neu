"""Öffentliche Seiten ohne Anmeldung: Impressum und Datenschutz."""
from fastapi import APIRouter

from . import rechtstexte
from .db import tx

router = APIRouter(prefix="/api")


@router.get("/recht")
def recht():
    with tx("system") as cur:
        return rechtstexte.lesen(cur)
