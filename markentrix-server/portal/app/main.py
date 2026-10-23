from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

import os

from . import config, db, jobs
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_kunde import router as kunde_router
from .routes_kundenwerkzeuge import router as kundenwerkzeuge_router
from .routes_diagramme import router as diagramme_router
from .routes_websites import router as websites_router
from .routes_verwaltung import router as verwaltung_router
from .routes_einstellungen import router as einstellungen_router
from .routes_vertrieb import router as vertrieb_router
from .routes_2fa import router as zweifaktor_router
from .routes_public import router as public_router
from .routes_onboarding import router as onboarding_router
from .routes_vertriebqualitaet import router as vqual_router
from .routes_pakete import router as pakete_router
from .routes_wert import router as wert_router
from .routes_hilfe import router as hilfe_router
from .routes_provision import router as provision_router, vertrieb_router as provision_vertrieb_router
from .routes_team import router as team_router, admin_router as team_admin_router
from .routes_avv import router as avv_router, kunde_router as avv_kunde_router
from .routes_uav import router as uav_router, kunde_router as uav_kunde_router
from .routes_domains import router as domains_router
from .routes_freigabelink import router as freigabelink_router
from .routes_offboarding import router as offboarding_router
from .routes_zusammenarbeit import router as zus_router, kunde_router as zus_kunde_router
from .routes_websitecheck import router as wcheck_router
from .routes_folgemails import router as folge_router
from .routes_buchung import router as buchung_router
from .routes_sitedienste import admin as site_admin_router
from .routes_webupload import router as webupload_router
from .routes_sitedienste import kunde as site_kunde_router
from .routes_sitedienste import router as site_router
from .routes_siteapi import router as siteapi_router
from .routes_vertriebsplus import router as vertriebsplus_router
from .routes_vertriebwerkzeuge import router as vertriebwerkzeuge_router
from .routes_nutzung import router as nutzung_router
from .routes_leadangebot import router as leadangebot_router, oeffentlich as angebot_oeffentlich_router
from .routes_system import router as system_router
from .routes_loginlink import router as loginlink_router
from .routes_zahlung import router as zahlung_router
from .routes_fruehwarnung import router as fruehwarnung_router
from . import preisaenderung, routes_betriebplus, routes_plattformstatus, routes_status, routes_leadsteuerung, routes_leadtermin, routes_rangliste, routes_referenzseite, routes_umfrage, routes_vertragportal, routes_vertraege
from .routes_push import router as push_router
from .routes_dashboard import router as dashboard_router
from .routes_telefon import router as telefon_router
from .routes_leistungsfreigabe import router as leistungsfreigabe_router
from .routes_vorlagen import router as vorlagen_router
from .routes_buchungsvorlagen import router as buchungsvorlagen_router
from .routes_kundenampel import router as kundenampel_router
from .routes_wissen import kunde as wissen_kunde_router
from .routes_wissen import router as wissen_router
from .routes_werkzeuge import router as werkzeuge_router
from .routes_leadimport import router as leadimport_router
from .routes_mitarbeiter import router as mitarbeiter_router
from .routes_briefing import router as brief_router, kunde_router as brief_kunde_router
from .routes_angebotsinhalte import router as ang_router, kunde_router as ang_kunde_router
from .routes_aufgaben import router as aufgaben_router, kunde_router as aufgaben_kunde_router
from .routes_angebotsplus import router as angebotsplus_router
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
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.url.path.startswith("/api/") and not request.url.path.startswith("/api/webhook/"):
        # /api/webhook/… wird von fremden Diensten (Stripe, Telefon-Assistent) aufgerufen und prüft Signatur bzw. Geheimnis selbst
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
    r.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"   # Portal ist nicht öffentlich: nicht in Suchmaschinen aufnehmen
    if config.COOKIE_SECURE:
        r.headers["Strict-Transport-Security"] = "max-age=31536000"
    return r


@app.exception_handler(StarletteHTTPException)
async def http_fehler(request: Request, exc: StarletteHTTPException):
    """Wie üblich {"detail": …}. Für die Website-Dienste (/site/…) bekommen auch Fehler die Herkunfts-Kopfzeile, sonst kann das Skript der Website den Text nicht lesen."""
    kopf = dict(exc.headers or {})
    if request.url.path.startswith("/site/") and request.headers.get("origin"):
        kopf.update({"Access-Control-Allow-Origin": request.headers["origin"], "Vary": "Origin"})
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=kopf)


@app.exception_handler(Exception)
async def unbehandelt(request: Request, exc: Exception):
    """Unerwartete Fehler: nicht nur 500 zeigen, sondern mit Erklärung und Lösungsvorschlag als Alarm ins Protokoll (Fehlerhilfe; je Pfad und Fehlerart höchstens alle 10 Minuten)."""
    import logging
    logging.getLogger("uvicorn.error").exception("Unbehandelter Fehler bei %s", request.url.path, exc_info=exc)
    from . import fehlerhilfe
    nr = fehlerhilfe.melden("portal", exc, sperre_von="portal:" + request.url.path[:60], titel="Fehler im Portal: " + request.method + " " + request.url.path[:120], sperre_sek=600)
    return JSONResponse({"detail": f"Interner Fehler. Der Fehler wurde protokolliert (Fehler-Nr. {nr})."}, status_code=500)


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


app.include_router(auth_router)
app.include_router(kunde_router)
app.include_router(kundenwerkzeuge_router)
app.include_router(diagramme_router)
app.include_router(admin_router)
app.include_router(websites_router)
app.include_router(verwaltung_router)
app.include_router(einstellungen_router)
app.include_router(vertrieb_router)
app.include_router(zweifaktor_router)
app.include_router(public_router)
app.include_router(onboarding_router)
app.include_router(belege_router)
app.include_router(angebotsplus_router)
app.include_router(belege_kunde_router)
app.include_router(offboarding_router)
app.include_router(zus_router)
app.include_router(zus_kunde_router)
app.include_router(aufgaben_router)
app.include_router(wcheck_router)
app.include_router(folge_router)
app.include_router(buchung_router)
app.include_router(site_router)
app.include_router(siteapi_router)
app.include_router(site_kunde_router)
app.include_router(site_admin_router)
app.include_router(webupload_router)
app.include_router(vertriebsplus_router)
app.include_router(vertriebwerkzeuge_router)
app.include_router(leadangebot_router)
app.include_router(nutzung_router)
app.include_router(angebot_oeffentlich_router)
app.include_router(system_router)
app.include_router(loginlink_router)
app.include_router(zahlung_router)
app.include_router(fruehwarnung_router)
app.include_router(routes_betriebplus.admin)
app.include_router(routes_betriebplus.kunde)
app.include_router(routes_status.kunde)
app.include_router(routes_status.public)
app.include_router(routes_plattformstatus.public)
app.include_router(routes_plattformstatus.admin)
app.include_router(routes_vertraege.router)
app.include_router(routes_vertraege.vertrieb)
app.include_router(routes_vertragportal.kunde)
app.include_router(routes_umfrage.kunde)
app.include_router(routes_referenzseite.public)
app.include_router(routes_rangliste.vertrieb)
app.include_router(routes_rangliste.admin)
app.include_router(routes_referenzseite.admin)
app.include_router(routes_umfrage.admin)
app.include_router(routes_leadsteuerung.router)
app.include_router(routes_leadtermin.router)
app.include_router(routes_vertragportal.vertrieb)
app.include_router(preisaenderung.admin)
app.include_router(preisaenderung.public)
app.include_router(push_router)
app.include_router(dashboard_router)
app.include_router(telefon_router)
app.include_router(vorlagen_router)
app.include_router(buchungsvorlagen_router)
app.include_router(kundenampel_router)
app.include_router(wissen_router)
app.include_router(leistungsfreigabe_router)
app.include_router(wissen_kunde_router)
app.include_router(werkzeuge_router)
app.include_router(leadimport_router)
app.include_router(mitarbeiter_router)
app.include_router(brief_router)
app.include_router(brief_kunde_router)
app.include_router(ang_router)
app.include_router(ang_kunde_router)
app.include_router(aufgaben_kunde_router)
app.include_router(avv_router)
app.include_router(uav_router)
app.include_router(domains_router)
app.include_router(freigabelink_router)
app.include_router(avv_kunde_router)
app.include_router(uav_kunde_router)
app.include_router(team_router)
app.include_router(team_admin_router)
app.include_router(hilfe_router)
app.include_router(wert_router)
app.include_router(pakete_router)
app.include_router(vqual_router)
app.include_router(provision_router)
app.include_router(provision_vertrieb_router)


def seite(name):
    return lambda: FileResponse(config.STATIC_DIR / name, media_type="text/html")


app.get("/", include_in_schema=False)(seite("login.html"))
app.get("/app", include_in_schema=False)(seite("kunde.html"))
app.get("/admin", include_in_schema=False)(seite("admin.html"))
app.get("/vertrieb", include_in_schema=False)(seite("vertrieb.html"))
app.get("/einladung", include_in_schema=False)(seite("einladung.html"))
app.get("/buchen", include_in_schema=False)(seite("buchen.html"))
app.get("/angebot", include_in_schema=False)(seite("angebot.html"))
app.get("/freigabe", include_in_schema=False)(seite("freigabe.html"))
app.get("/anmelden", include_in_schema=False)(seite("anmelden.html"))
app.get("/impressum", include_in_schema=False)(seite("recht.html"))
app.get("/datenschutz", include_in_schema=False)(seite("recht.html"))
@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    return FileResponse(config.STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(config.STATIC_DIR / "sw.js", media_type="text/javascript", headers={"Service-Worker-Allowed": "/"})


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
