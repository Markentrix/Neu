#!/usr/bin/env bash
# Neue statische Website anlegen:  add-site.sh kunde.de
# Für eine App (z.B. CRM) statt Dateien:  add-site.sh crm.markentrix.de --proxy crm-container:3000
set -euo pipefail
DOMAIN="${1:?Usage: add-site.sh <domain> [--proxy container:port]}"
[[ "$DOMAIN" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ ]] || { echo "Ungültige Domain: $DOMAIN"; exit 1; }
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNIP="/srv/caddy-sites/$DOMAIN.caddy"
[ ! -e "$SNIP" ] || { echo "Existiert schon: $SNIP"; exit 1; }

HEADERS='	encode zstd gzip
	header {
		Strict-Transport-Security "max-age=31536000"
		X-Content-Type-Options nosniff
		Referrer-Policy strict-origin-when-cross-origin
		-Server
	}'

if [ "${2:-}" = "--proxy" ]; then
  cat > "$SNIP" <<CADDY
$DOMAIN {
$HEADERS
	reverse_proxy ${3:?--proxy braucht container:port}
}
CADDY
else
  mkdir -p "/srv/sites/$DOMAIN"
  [ -e "/srv/sites/$DOMAIN/index.html" ] || sed "s/__DOMAIN__/$DOMAIN/g" "$SERVER_DIR/www-placeholder/index.html" > "/srv/sites/$DOMAIN/index.html"
  cat > "$SNIP" <<CADDY
$DOMAIN {
	root * /srv/sites/$DOMAIN
$HEADERS
	file_server
}
CADDY
  # www-Weiterleitung nur für Hauptdomains (kunde.de), nicht für Subdomains (test.kunde.de)
  if [ "$(tr -cd . <<<"$DOMAIN" | wc -c)" -eq 1 ]; then
    printf 'www.%s {\n\tredir https://%s{uri} permanent\n}\n' "$DOMAIN" "$DOMAIN" >> "$SNIP"
  fi
fi

cd "$SERVER_DIR"
if docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1; then
  docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile
  echo "OK: https://$DOMAIN  (DNS-A-Eintrag auf diesen Server nicht vergessen; Dateien liegen in /srv/sites/$DOMAIN)"
else
  rm -f "$SNIP"
  echo "Caddy-Konfiguration ungültig – Änderung zurückgenommen."; exit 1
fi
