#!/usr/bin/env bash
# Kundenwebsite entfernen – nichts wird gelöscht, alles wandert nach /srv/backups/removed.
#
#   kunde-entfernen.sh MX-1007 mx-1007.vorschau.markentrix.de
#       nimmt nur diese eine Domain (z.B. die Vorschau) aus dem Betrieb; die Dateien bleiben.
#   kunde-entfernen.sh MX-1007 --alles
#       nimmt ALLE Domains dieses Kunden aus dem Betrieb und verschiebt auch den Dateiordner.
set -euo pipefail

SITES_ROOT="${SITES_ROOT:-/srv/sites/kunden}"
CADDY_SITES="${CADDY_SITES:-/srv/caddy-sites}"
BACKUP_ROOT="${BACKUP_ROOT:-/srv/backups/removed}"
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[ $# -eq 2 ] || { sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1; }
ID="$1"; TARGET="$2"
[[ "$ID" =~ ^MX-[0-9]{4,}$ ]] || { echo "Ungültige Kundennummer: $ID"; exit 1; }

STAMP="$(date +%F-%H%M%S)"
DEST="$BACKUP_ROOT/kunde-$ID-$STAMP"

if [ "$TARGET" = "--alles" ]; then
  mapfile -t FILES < <(ls "$CADDY_SITES"/kunde-"$ID"-*.caddy 2>/dev/null || true)
  FOLDER="$SITES_ROOT/$ID"
else
  [[ "$TARGET" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ && "$TARGET" != *..* ]] || { echo "Ungültige Domain: $TARGET"; exit 1; }
  FILES=()
  [ ! -e "$CADDY_SITES/kunde-$ID-$TARGET.caddy" ] || FILES=("$CADDY_SITES/kunde-$ID-$TARGET.caddy")
  FOLDER=""
fi

if [ "${#FILES[@]}" -eq 0 ] && { [ -z "$FOLDER" ] || [ ! -d "$FOLDER" ]; }; then
  echo "Nichts gefunden für $ID / $TARGET."; exit 1
fi

echo "Folgendes wird in $DEST verschoben (nicht gelöscht):"
for f in "${FILES[@]}"; do echo "  Konfiguration: $f"; done
[ -z "$FOLDER" ] || [ ! -d "$FOLDER" ] || echo "  Dateiordner:   $FOLDER"
if [ "${ASSUME_YES:-0}" != 1 ]; then
  read -rp "Wirklich ausführen? (ja/nein): " ANSWER
  [ "$ANSWER" = "ja" ] || { echo "Abgebrochen. Es wurde nichts verändert."; exit 0; }
fi

mkdir -p "$DEST"
for f in "${FILES[@]}"; do mv "$f" "$DEST/"; done
if [ -n "$FOLDER" ] && [ -d "$FOLDER" ]; then mv "$FOLDER" "$DEST/dateien"; fi

if [ "${NO_RELOAD:-0}" != 1 ]; then
  cd "$SERVER_DIR"
  docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null
fi
echo "Erledigt. Gesichert in: $DEST"
