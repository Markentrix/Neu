from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_kunde import router as kunde_router
from .routes_websites import router as websites_router
from .routes_verwaltung import router as verwaltung_router


@asynccontextmanager
async def lifespan(app):
    db.open_pool()
    yield
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


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


app.include_router(auth_router)
app.include_router(kunde_router)
app.include_router(admin_router)
app.include_router(websites_router)
app.include_router(verwaltung_router)


def seite(name):
    return lambda: FileResponse(config.STATIC_DIR / name, media_type="text/html")


app.get("/", include_in_schema=False)(seite("login.html"))
app.get("/app", include_in_schema=False)(seite("kunde.html"))
app.get("/admin", include_in_schema=False)(seite("admin.html"))
app.get("/einladung", include_in_schema=False)(seite("einladung.html"))
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
