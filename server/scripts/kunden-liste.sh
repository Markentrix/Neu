#!/usr/bin/env bash
# Übersicht: welche Kunden/Domains laufen auf dem Server?
set -euo pipefail
SITES_ROOT="${SITES_ROOT:-/srv/sites/kunden}"
CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"

printf '%-10s %-45s %s\n' "Kunde" "Domain" "Art"
shopt -s nullglob
for f in "$CADDY_SITES"/kunde-MX-*.caddy; do
  rest="$(basename "$f" .caddy)"; rest="${rest#kunde-}"
  id="$(sed -E 's/^(MX-[0-9]+)-.*/\1/' <<<"$rest")"; host="${rest#"$id"-}"
  art="live"; grep -q "noindex" "$f" && art="Vorschau (noindex)"
  printf '%-10s %-45s %s\n' "$id" "$host" "$art"
done
echo
echo "Dateiordner in $SITES_ROOT:"
ls -1 "$SITES_ROOT" 2>/dev/null || echo "  (noch keine)"
