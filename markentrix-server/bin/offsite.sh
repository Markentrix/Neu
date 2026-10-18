#!/usr/bin/env bash
# Kopiert die neueste Sicherung verschlüsselt auf eine externe Stelle (z. B. Hetzner Storage Box).
# Wird nach jeder Sicherung automatisch aufgerufen, wenn OFFSITE_TARGET in /opt/markentrix/.env steht.
set -Eeuo pipefail
BASE=/opt/markentrix
# shellcheck disable=SC1091
[ -f "$BASE/.env" ] && { set -a; . "$BASE/.env"; set +a; }
[ -n "${OFFSITE_TARGET:-}" ] || { echo "Externe Sicherung ist nicht eingerichtet (mkctl offsite-setup)."; exit 0; }
KEY="$BASE/offsite/id_ed25519"; PASS="$BASE/offsite/passphrase"; PORT="${OFFSITE_PORT:-23}"
SSH=(ssh -p "$PORT" -i "$KEY" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$BASE/offsite/known_hosts" -o BatchMode=yes -o ConnectTimeout=20)
status() { install -d -m 755 "$BASE/backup-status"; printf '%s\n' "$2" > "$BASE/backup-status/$1"; chmod 644 "$BASE/backup-status/$1"; }
fail() { echo "[$(date '+%F %T')] OFFSITE-FEHLER: $*" >&2; status offsite_fehler "$*"; rm -f "${TMP:-/nonexistent}"; exit 1; }
trap 'fail "Zeile $LINENO"' ERR

TMP="$(mktemp /var/tmp/mk-offsite.XXXXXX)"
if [ "${1:-}" = "--test" ]; then
  echo "markentrix offsite test $(date -Is)" | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "file:$PASS" > "$TMP"
  rsync -e "${SSH[*]}" "$TMP" "${OFFSITE_TARGET}test.enc" || fail "Verbindung zum Ziel fehlgeschlagen. Ist der öffentliche Schlüssel hinterlegt?"
  rm -f "$TMP"; echo "OK: Verbindung und Verschlüsselung funktionieren."; exit 0
fi

LETZTE="$(ls -1 "$BASE/backups" | grep -E '^[0-9]{4}-' | sort | tail -1)"
[ -n "$LETZTE" ] || fail "Keine Sicherung gefunden."
tar -C "$BASE/backups" -cf - "$LETZTE" | openssl enc -aes-256-cbc -pbkdf2 -salt -pass "file:$PASS" > "$TMP"
rsync -e "${SSH[*]}" --partial "$TMP" "${OFFSITE_TARGET}markentrix-$LETZTE.tar.enc" || fail "Hochladen fehlgeschlagen."
rm -f "$TMP"
status offsite_last "$(date +%s)"; rm -f "$BASE/backup-status/offsite_fehler"
echo "[$(date '+%F %T')] Externe Sicherung fertig: markentrix-$LETZTE.tar.enc"
