#!/usr/bin/env bash
# Statische Kundenwebsite einrichten (Ordner nach Kundennummer, Domain in Caddy).
#
#   kunde-anlegen.sh MX-1007 kunde.de
#       Live-Domain; bei Hauptdomains wird www.kunde.de auf kunde.de weitergeleitet.
#   kunde-anlegen.sh MX-1007 mx-1007.vorschau.markentrix.de --vorschau --passwort
#       Vorschau: für Google gesperrt (noindex), mit Passwortschutz (Benutzer: vorschau).
#
# Die Website-Dateien liegen immer in /srv/sites/kunden/<Kundennummer>.
# Pro Domain entsteht eine Datei /srv/caddy-sites/kunde-<Kundennummer>-<domain>.caddy.
# Vorschau und Live-Domain können gleichzeitig auf denselben Ordner zeigen.
set -euo pipefail

SITES_ROOT="${SITES_ROOT:-/srv/sites/kunden}"
CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() { sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
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
  || { echo "Ungültige Domain: $HOST (nur Kleinbuchstaben, Ziffern, Punkt, Bindestrich)"; exit 1; }
[ "$ASKPW" -eq 0 ] || [ "$MODE" = vorschau ] || { echo "--passwort gibt es nur zusammen mit --vorschau."; exit 1; }
case "$HOST" in
  markentrix.de|www.markentrix.de) echo "Diese Domain gehört zur eigenen Website, nicht zu einem Kunden."; exit 1 ;;
esac

SNIP="$CADDY_SITES/kunde-$ID-$HOST.caddy"
[ ! -e "$SNIP" ] || { echo "Existiert schon: $SNIP"; exit 1; }

# Domain darf noch von keiner anderen Konfiguration benutzt werden
HOST_RE="${HOST//./\\.}"
if grep -lsE "^(www\.)?${HOST_RE}[[:space:]]*(,|\{)" "$CADDY_SITES"/*.caddy 2>/dev/null | grep -q .; then
  echo "Die Domain $HOST wird schon in einer anderen Konfiguration verwendet:"
  grep -lsE "^(www\.)?${HOST_RE}[[:space:]]*(,|\{)" "$CADDY_SITES"/*.caddy
  exit 1
fi

mkdir -p "$SITES_ROOT/$ID" "$CADDY_SITES"
if [ ! -e "$SITES_ROOT/$ID/index.html" ]; then
  cat > "$SITES_ROOT/$ID/index.html" <<'HTML'
<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>In Vorbereitung</title>
<style>body{font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;background:#f8fafc;color:#0f172a}</style>
</head><body><main><h1>Diese Website ist in Vorbereitung.</h1></main></body></html>
HTML
fi

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

{
  printf '%s {\n\troot * %s/%s\n%s\timport kunden_site\n}\n' "$HOST" "$SITES_ROOT" "$ID" "$EXTRA"
  # www-Weiterleitung nur bei Live-Hauptdomains (kunde.de), nicht bei Subdomains
  if [ "$MODE" = live ] && [ "$(tr -cd . <<<"$HOST" | wc -c)" -eq 1 ]; then
    printf 'www.%s {\n\tredir https://%s{uri} permanent\n}\n' "$HOST" "$HOST"
  fi
} > "$SNIP"

reload_caddy() {
  [ "${NO_RELOAD:-0}" = 1 ] && return 0
  cd "$SERVER_DIR"
  local out
  if out="$(docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile 2>&1)"; then
    docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null 2>&1
    return 0
  fi
  echo "$out" | tail -n 5
  return 1
}

if reload_caddy; then
  echo "OK: https://$HOST  →  $SITES_ROOT/$ID"
  if [ "$MODE" = live ]; then
    echo "Nicht vergessen: Der DNS-Eintrag der Domain muss auf diesen Server zeigen (sonst kein Zertifikat)."
  else
    echo "Die Vorschau ist für Google gesperrt."
    [ "$ASKPW" -eq 1 ] && echo "Zugang: Benutzer 'vorschau' mit dem eben eingegebenen Passwort."
  fi
  echo "Dateien hochladen: auf dem PC kunde-veroeffentlichen.bat benutzen oder per scp nach $SITES_ROOT/$ID/"
else
  rm -f "$SNIP"
  echo "Caddy-Konfiguration ungültig – Änderung zurückgenommen."
  exit 1
fi
