import os
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "")
BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_2FA_PFLICHT = os.environ.get("PORTAL_ADMIN_2FA", "1") != "0"   # laut AVV Anlage 2: Zwei-Faktor-Anmeldung für alle Admin-Konten verpflichtend
COOKIE_SECURE = os.environ.get("PORTAL_COOKIE_SECURE", "1") != "0"
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/data/uploads"))
SITES_ROOT = Path(os.environ.get("SITES_ROOT", "/srv/sites"))
QUEUE_DIR = Path(os.environ.get("QUEUE_DIR", "/data/queue"))
SITES_LIVE = Path(os.environ.get("SITES_LIVE", "/srv/sites/live"))
CHAT_WEBHOOK_URL = os.environ.get("CHAT_WEBHOOK_URL", "")
CHAT_WEBHOOK_SECRET = os.environ.get("CHAT_WEBHOOK_SECRET", "")
SESSION_HOURS = 12
INVITE_DAYS = 7
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
PORTAL_SECRET = os.environ.get("PORTAL_SECRET", "")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
RESET_HOURS = 2
PUSH_HTTP_ERLAUBT = os.environ.get("PUSH_HTTP_ERLAUBT", "0") == "1"   # nur für Tests mit lokalem Push-Server
SITE_LOKAL_ERLAUBT = os.environ.get("SITE_LOKAL_ERLAUBT", "0") == "1"   # nur für Tests: lokale Mail-/Kalender-Server und http erlauben
PLACES_BASE_URL = os.environ.get("PLACES_BASE_URL", "https://places.googleapis.com").rstrip("/")

SITE_API_LIMIT = int(os.environ.get("SITE_API_LIMIT", "8"))   # Anfragen je IP-Adresse und 10 Minuten über die Website-API
