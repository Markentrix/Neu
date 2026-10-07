#!/usr/bin/env bash
# Website entfernen (Dateien werden nach /srv/backups/removed verschoben, nicht gelöscht)
set -euo pipefail
DOMAIN="${1:?Usage: remove-site.sh <domain>}"
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p /srv/backups/removed
rm -f "/srv/caddy-sites/$DOMAIN.caddy"
[ -d "/srv/sites/$DOMAIN" ] && mv "/srv/sites/$DOMAIN" "/srv/backups/removed/$DOMAIN-$(date +%F)"
cd "$SERVER_DIR" && docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
echo "Entfernt: $DOMAIN"
