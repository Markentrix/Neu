from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

import os

from . import config, db, jobs
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_kunde import router as kunde_router
from .routes_websites import router as websites_router
from .routes_verwaltung import router as verwaltung_router
from .routes_einstellungen import router as einstellungen_router
from .routes_vertrieb import router as vertrieb_router
from .routes_2fa import router as zweifaktor_router
from .routes_public import router as public_router
from .routes_onboarding import router as onboarding_router
from .routes_provision import router as provision_router, vertrieb_router as provision_vertrieb_router
from .routes_team import router as team_router, admin_router as team_admin_router
from .routes_avv import router as avv_router, kunde_router as avv_kunde_router
from .routes_offboarding import router as offboarding_router
from .routes_zusammenarbeit import router as zus_router, kunde_router as zus_kunde_router
from .routes_briefing import router as brief_router, kunde_router as brief_kunde_router
from .routes_angebotsinhalte import router as ang_router, kunde_router as ang_kunde_router
from .routes_aufgaben import router as aufgaben_router, kunde_router as aufgaben_kunde_router
from .routes_belege import router as belege_router, kunde_router as belege_kunde_router


@asynccontextmanager
async def lifespan(app):
    db.open_pool()
    if os.environ.get("PORTAL_JOBS", "1") != "0":
        jobs.starten()
    yield
    jobs.stoppen()
    db.close_pool()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


@app.middleware("http")
async def schutz(request: Request, call_next):
    # Änderungen nur von der eigenen Seite aus (zusätzlich zu SameSite-Cookie)
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.url.path.startswith("/api/"):
        if request.headers.get("x-mk") != "1":
            return JSONResponse({"detail": "Ungültige Anfrage."}, status_code=403)
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != urlparse(config.BASE_URL).netloc and urlparse(origin).netloc != request.headers.get("host"):
            return JSONResponse({"detail": "Ungültige Herkunft."}, status_code=403)
    r = await call_next(request)
    r.headers["Content-Security-Policy"] = CSP
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "no-referrer"
    r.headers["Cache-Control"] = "no-store"
    if config.COOKIE_SECURE:
        r.headers["Strict-Transport-Security"] = "max-age=31536000"
    return r


_letzter_alarm: dict = {}


@app.exception_handler(Exception)
async def unbehandelt(request: Request, exc: Exception):
    """Unerwartete Fehler: nicht nur 500 zeigen, sondern als Alarm ins Protokoll (max. 1x je Pfad und 10 Minuten), damit sie auffallen."""
    import logging
    import time
    logging.getLogger("uvicorn.error").exception("Unbehandelter Fehler bei %s", request.url.path, exc_info=exc)
    pfad = request.url.path
    jetzt = time.time()
    if jetzt - _letzter_alarm.get(pfad, 0) > 600:
        _letzter_alarm[pfad] = jetzt
        try:
            import json
            with db.tx("system") as cur:
                cur.execute("INSERT INTO alarme (stufe, quelle, titel, details) VALUES ('warnung','portal',%s,%s::jsonb)",
                            ("Fehler im Portal: " + request.method + " " + pfad[:120], json.dumps({"fehler": type(exc).__name__, "text": str(exc)[:500]})))
        except Exception:  # noqa: BLE001 - Alarm darf nie selbst den Fehler verdoppeln
            pass
    return JSONResponse({"detail": "Interner Fehler. Der Fehler wurde protokolliert."}, status_code=500)


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


app.include_router(auth_router)
app.include_router(kunde_router)
app.include_router(admin_router)
app.include_router(websites_router)
app.include_router(verwaltung_router)
app.include_router(einstellungen_router)
app.include_router(vertrieb_router)
app.include_router(zweifaktor_router)
app.include_router(public_router)
app.include_router(onboarding_router)
app.include_router(belege_router)
app.include_router(belege_kunde_router)
app.include_router(offboarding_router)
app.include_router(zus_router)
app.include_router(zus_kunde_router)
app.include_router(aufgaben_router)
app.include_router(brief_router)
app.include_router(brief_kunde_router)
app.include_router(ang_router)
app.include_router(ang_kunde_router)
app.include_router(aufgaben_kunde_router)
app.include_router(avv_router)
app.include_router(avv_kunde_router)
app.include_router(team_router)
app.include_router(team_admin_router)
app.include_router(provision_router)
app.include_router(provision_vertrieb_router)


def seite(name):
    return lambda: FileResponse(config.STATIC_DIR / name, media_type="text/html")


app.get("/", include_in_schema=False)(seite("login.html"))
app.get("/app", include_in_schema=False)(seite("kunde.html"))
app.get("/admin", include_in_schema=False)(seite("admin.html"))
app.get("/vertrieb", include_in_schema=False)(seite("vertrieb.html"))
app.get("/einladung", include_in_schema=False)(seite("einladung.html"))
app.get("/impressum", include_in_schema=False)(seite("recht.html"))
app.get("/datenschutz", include_in_schema=False)(seite("recht.html"))
@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(config.STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(config.STATIC_DIR / "sw.js", media_type="text/javascript", headers={"Service-Worker-Allowed": "/"})


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
