#!/usr/bin/env bash
# Domain für AJ Atelier im gemeinsamen Caddy einrichten (Markentrix-Server).
# Anstelle von kunde-anlegen.sh verwenden – die Seite braucht zusätzlich den Buchungsdienst.
#
#   einrichten.sh MX-1234 mx-1234.vorschau.markentrix.de --vorschau --passwort
#       Vorschau: für Google gesperrt (noindex), mit Passwortschutz (Benutzer: vorschau).
#   einrichten.sh MX-1234 aj-atelier-wettmar.de
#       Live-Domain; www.domain.de wird auf domain.de weitergeleitet.
#
# Die Seiten (dist/) liegen wie bei allen Kunden in /srv/sites/kunden/<Kundennummer>
# und werden mit kunde-veroeffentlichen.bat hochgeladen. Nur /api/*, /admin/*,
# /gutschein-pdf und /termin-stornieren gehen an den Container "aj-atelier".
set -euo pipefail

CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"
SITES_ROOT="${SITES_ROOT:-/srv/sites/kunden}"
SERVER_DIR="${SERVER_DIR:-/opt/neu/server}"
UPSTREAM="${UPSTREAM:-aj-atelier:80}"

usage() { sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
[ $# -ge 2 ] || usage
ID="$1"; HOST="$2"; shift 2

MODE=live; ASKPW=0
for opt in "$@"; do
  case "$opt" in
    --vorschau) MODE=vorschau ;;
    --passwort) ASKPW=1 ;;
    *) echo "Unbekannte Option: $opt"; usage ;;
  esac
done

[[ "$ID" =~ ^MX-[0-9]{4,}$ ]] || { echo "Ungültige Kundennummer: $ID (erwartet z.B. MX-1007)"; exit 1; }
[[ "$HOST" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ && "$HOST" != .* && "$HOST" != *..* && "$HOST" != -* ]] \
  || { echo "Ungültige Domain: $HOST"; exit 1; }
[ "$ASKPW" -eq 0 ] || [ "$MODE" = vorschau ] || { echo "--passwort gibt es nur zusammen mit --vorschau."; exit 1; }

SNIP="$CADDY_SITES/kunde-$ID-$HOST.caddy"
[ ! -e "$SNIP" ] || { echo "Existiert schon: $SNIP"; exit 1; }
HOST_RE="${HOST//./\\.}"
if grep -lsE "^(www\.)?${HOST_RE}[[:space:]]*(,|\{)" "$CADDY_SITES"/*.caddy 2>/dev/null | grep -q .; then
  echo "Die Domain $HOST wird schon in einer anderen Konfiguration verwendet."; exit 1
fi
docker network inspect web >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx "${UPSTREAM%%:*}" \
  || { echo "Container ${UPSTREAM%%:*} läuft nicht. Zuerst: docker compose up -d --build"; exit 1; }

EXTRA=""
if [ "$MODE" = vorschau ]; then
  EXTRA=$'\theader X-Robots-Tag "noindex, nofollow"\n'
  if [ "$ASKPW" -eq 1 ]; then
    read -rsp "Passwort für die Vorschau (wird nirgends gespeichert): " PW1; echo
    read -rsp "Passwort wiederholen: " PW2; echo
    [ -n "$PW1" ] && [ "$PW1" = "$PW2" ] || { echo "Passwörter leer oder verschieden – abgebrochen."; exit 1; }
    HASH="$(cd "$SERVER_DIR" && docker compose exec -T caddy caddy hash-password --plaintext "$PW1")"
    unset PW1 PW2
    [ -n "$HASH" ] || { echo "Passwort-Hash konnte nicht erzeugt werden."; exit 1; }
    EXTRA+=$'\tbasic_auth {\n\t\tvorschau '"$HASH"$'\n\t}\n'
  fi
fi

mkdir -p "$SITES_ROOT/$ID"
[ -e "$SITES_ROOT/$ID/index.html" ] || printf '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>In Vorbereitung</title><p>Diese Website ist in Vorbereitung.</p>\n' > "$SITES_ROOT/$ID/index.html"

{
  printf '%s {\n%s\t@app path /api/* /admin /admin/* /gutschein-pdf /termin-stornieren /termin-stornieren.php\n\treverse_proxy @app %s\n\troot * %s/%s\n\timport kunden_site\n}\n' "$HOST" "$EXTRA" "$UPSTREAM" "$SITES_ROOT" "$ID"
  if [ "$MODE" = live ] && [ "$(tr -cd . <<<"$HOST" | wc -c)" -eq 1 ]; then
    printf 'www.%s {\n\tredir https://%s{uri} permanent\n}\n' "$HOST" "$HOST"
  fi
} > "$SNIP"

cd "$SERVER_DIR"
if out="$(docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile 2>&1)"; then
  docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null 2>&1
  echo "OK: https://$HOST  →  Seiten aus $SITES_ROOT/$ID, Buchung über $UPSTREAM"
  echo "Seiten hochladen: dist/ mit kunde-veroeffentlichen.bat (Kundennummer $ID)."
  [ "$MODE" = live ] && echo "Danach in app/config.local.php siteUrl auf https://$HOST setzen und den Container neu starten."
  [ "$MODE" = vorschau ] && echo "Die Vorschau ist für Google gesperrt."
else
  rm -f "$SNIP"
  echo "$out" | tail -n 5
  echo "Caddy-Konfiguration ungültig – Änderung zurückgenommen."; exit 1
fi
