#!/usr/bin/env bash
# Demo-Link für einen Interessenten einrichten (ohne Kundennummer) oder den vorhandenen Link anzeigen.
#
#   demo-anlegen.sh mueller-kfz
#       Legt https://mueller-kfz-<zufall>.vorschau.markentrix.de an – für Google gesperrt (noindex),
#       ohne Passwort, aber mit nicht erratbarem Namen. Nochmal aufgerufen: gleicher Link.
#   demo-anlegen.sh mueller-kfz --passwort
#       Zusätzlich mit Passwortschutz (Benutzer: vorschau).
#   demo-anlegen.sh mueller-kfz --entfernen
#       Nimmt die Demo vom Netz (Dateien werden nach /srv/backups/removed verschoben, nichts wird gelöscht).
#
# Dateien liegen in /srv/sites/demos/<name>. Wird der Interessent Kunde: Ordnerinhalt nach
# /srv/sites/kunden/<MX-Nummer> kopieren (kunde-anlegen.sh), danach Demo entfernen.
# Die letzte Ausgabezeile beim Anlegen ist immer:  LINK=https://...
# Voraussetzung (einmalig): DNS-Eintrag  *.vorschau  (A)  ->  IP des Servers.
set -euo pipefail

SITES_ROOT="${SITES_ROOT:-/srv/sites/demos}"
CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"
BACKUP_ROOT="${BACKUP_ROOT:-/srv/backups/removed}"
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[ $# -ge 1 ] || { sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
NAME="$1"; shift
[[ "$NAME" =~ ^[a-z0-9]([a-z0-9-]{0,28}[a-z0-9])$ ]] \
  || { echo "Ungültiger Name: $NAME (nur Kleinbuchstaben, Ziffern, Bindestrich; 2-30 Zeichen, z.B. mueller-kfz)"; exit 1; }
ASKPW=0; REMOVE=0
for opt in "$@"; do
  case "$opt" in
    --passwort) ASKPW=1 ;;
    --entfernen) REMOVE=1 ;;
    *) echo "Unbekannte Option: $opt"; exit 1 ;;
  esac
done

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

shopt -s nullglob
EXISTING=("$CADDY_SITES"/demo-"$NAME"-*.caddy)

if [ "$REMOVE" -eq 1 ]; then
  [ "${#EXISTING[@]}" -gt 0 ] || { echo "Keine Demo namens $NAME gefunden."; exit 1; }
  DEST="$BACKUP_ROOT/demo-$NAME-$(date +%F-%H%M%S)"
  mkdir -p "$DEST"
  mv "${EXISTING[@]}" "$DEST/"
  [ ! -d "$SITES_ROOT/$NAME" ] || mv "$SITES_ROOT/$NAME" "$DEST/dateien"
  reload_caddy
  echo "Demo $NAME ist offline. Gesichert in: $DEST"
  exit 0
fi

if [ "${#EXISTING[@]}" -gt 0 ]; then
  host="$(basename "${EXISTING[0]}" .caddy)"; host="${host#demo-"$NAME"-}"
  echo "Für $NAME gibt es schon eine Demo."
  echo "LINK=https://$host"
  exit 0
fi

TOKEN="$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')"
HOST="$NAME-$TOKEN.vorschau.markentrix.de"
SNIP="$CADDY_SITES/demo-$NAME-$HOST.caddy"

mkdir -p "$SITES_ROOT/$NAME" "$CADDY_SITES"
if [ ! -e "$SITES_ROOT/$NAME/index.html" ]; then
  printf '%s\n' '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>In Vorbereitung</title></head><body><h1>Diese Demo ist in Vorbereitung.</h1></body></html>' > "$SITES_ROOT/$NAME/index.html"
fi

EXTRA=$'\theader X-Robots-Tag "noindex, nofollow"\n'
if [ "$ASKPW" -eq 1 ]; then
  read -rsp "Passwort für die Demo (wird nirgends gespeichert): " PW1; echo
  read -rsp "Passwort wiederholen: " PW2; echo
  [ -n "$PW1" ] && [ "$PW1" = "$PW2" ] || { echo "Passwörter leer oder verschieden – abgebrochen."; exit 1; }
  HASH="$(cd "$SERVER_DIR" && docker compose exec -T caddy caddy hash-password --plaintext "$PW1")"
  unset PW1 PW2
  [ -n "$HASH" ] || { echo "Passwort-Hash konnte nicht erzeugt werden."; exit 1; }
  EXTRA+=$'\tbasic_auth {\n\t\tvorschau '"$HASH"$'\n\t}\n'
fi

printf '%s {\n\troot * %s/%s\n%s\timport kunden_site\n}\n' "$HOST" "$SITES_ROOT" "$NAME" "$EXTRA" > "$SNIP"

if reload_caddy; then
  echo "OK: Demo $NAME eingerichtet."
  echo "LINK=https://$HOST"
else
  rm -f "$SNIP"
  echo "Caddy-Konfiguration ungültig – Änderung zurückgenommen."
  exit 1
fi
