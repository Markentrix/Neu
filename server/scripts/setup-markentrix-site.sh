#!/usr/bin/env bash
# Richtet die Markentrix-Website (statisches dist/) unter einer Domain ein.
#   setup-markentrix-site.sh server.markentrix.de   (Test)
#   setup-markentrix-site.sh markentrix.de          (Live; legt auch www -> ohne www an)
# Die Dateien liegen immer in /srv/sites/markentrix (eine Kopie für alle Domains).
set -euo pipefail
HOST="${1:?Usage: setup-markentrix-site.sh <domain>}"
[[ "$HOST" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ ]] || { echo "Ungültige Domain: $HOST"; exit 1; }
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNIP="/srv/caddy-sites/$HOST.caddy"
BACKUP="$(mktemp)"; [ -e "$SNIP" ] && cp "$SNIP" "$BACKUP" || : > "$BACKUP"

mkdir -p /srv/sites/markentrix
cat > "$SNIP" <<CADDY
$HOST {
	root * /srv/sites/markentrix
	import markentrix_site
}
CADDY
if [ "$(tr -cd . <<<"$HOST" | wc -c)" -eq 1 ]; then
  printf 'www.%s {\n\tredir https://%s{uri} permanent\n}\n' "$HOST" "$HOST" >> "$SNIP"
fi

cd "$SERVER_DIR"
if docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1; then
  docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
  echo "OK: https://$HOST zeigt jetzt /srv/sites/markentrix"
else
  if [ -s "$BACKUP" ]; then cp "$BACKUP" "$SNIP"; else rm -f "$SNIP"; fi
  echo "Caddy-Konfiguration ungültig – zurückgesetzt."; exit 1
fi
