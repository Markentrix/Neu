#!/usr/bin/env bash
# Demo-Link für einen Kunden einrichten (oder den vorhandenen Link anzeigen).
#
#   demo-anlegen.sh MX-1007
#       Legt https://mx-1007-<zufall>.vorschau.markentrix.de an – für Google gesperrt (noindex),
#       ohne Passwort, aber mit nicht erratbarem Namen. Läuft der Befehl nochmal, wird derselbe Link gezeigt.
#   demo-anlegen.sh MX-1007 --passwort
#       Zusätzlich mit Passwortschutz (Benutzer: vorschau).
#
# Die Dateien liegen wie bei jedem Kunden in /srv/sites/kunden/<Kundennummer>.
# Die letzte Ausgabezeile ist immer:  LINK=https://...
# Voraussetzung (einmalig): DNS-Eintrag  *.vorschau  (A)  ->  IP des Servers.
set -euo pipefail

CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ $# -ge 1 ] || { sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
ID="$1"; shift
[[ "$ID" =~ ^MX-[0-9]{4,}$ ]] || { echo "Ungültige Kundennummer: $ID (erwartet z.B. MX-1007)"; exit 1; }
EXTRA=()
for opt in "$@"; do
  case "$opt" in
    --passwort) EXTRA+=(--passwort) ;;
    *) echo "Unbekannte Option: $opt"; exit 1 ;;
  esac
done

LOWER="${ID,,}"
shopt -s nullglob
for f in "$CADDY_SITES"/kunde-"$ID"-"$LOWER"-*.vorschau.markentrix.de.caddy; do
  host="$(basename "$f" .caddy)"; host="${host#kunde-"$ID"-}"
  echo "Für $ID gibt es schon eine Demo."
  echo "LINK=https://$host"
  exit 0
done

TOKEN="$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')"
HOST="$LOWER-$TOKEN.vorschau.markentrix.de"
"$HERE/kunde-anlegen.sh" "$ID" "$HOST" --vorschau "${EXTRA[@]}"
echo "LINK=https://$HOST"
