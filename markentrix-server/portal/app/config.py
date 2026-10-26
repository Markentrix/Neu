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
PAGESPEED_BASE_URL = os.environ.get("PAGESPEED_BASE_URL", "https://www.googleapis.com/pagespeedonline/v5/runPagespeed")   # Website-Check der Funnel-Seiten (Tests: lokaler Ersatz)

SERVER_IPV4 = [x.strip() for x in os.environ.get("SERVER_IPV4", "").split(",") if x.strip()]   # Öffentliche IP des Servers (sonst vom Server-Dienst ermittelt)
SERVER_IPV6 = [x.strip() for x in os.environ.get("SERVER_IPV6", "").split(",") if x.strip()]
DNS_TEST_DATEI = os.environ.get("DNS_TEST_DATEI", "")   # nur Tests: JSON mit festen DNS-Antworten
WACHT_API_PRAEFIX = os.environ.get("WACHT_API_PRAEFIX", "")   # nur für Tests (Portal ohne Caddy davor)
WACHT_BASIS = os.environ.get("WACHT_BASIS", "").rstrip("/")   # nur für Tests: Wachdienst fragt diese Adresse statt https://<domain>
SITE_API_LIMIT = int(os.environ.get("SITE_API_LIMIT", "8"))   # Anfragen je IP-Adresse und 10 Minuten über die Website-API
