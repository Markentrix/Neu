#!/usr/bin/env bash
# Wöchentliche Backup-Prüfung – per Cron (als deploy), z. B. montags 7:10 Uhr:
#   10 7 * * 1 /srv/apps/aj-atelier/deploy/backup-check.sh >> /var/log/aj-atelier-backup.log 2>&1
# Prüft, ob die letzte Sicherung frisch und lesbar ist, und schickt das Ergebnis per Mail.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
DIR="${BACKUP_DIR:-/srv/backups/daily}"
latest=$(ls -1t "$DIR"/aj-atelier-*.sqlite 2>/dev/null | head -n1)

if [ -z "$latest" ]; then
  alert "Backup fehlt" "In $DIR liegt keine Sicherung der Termine. Ist der Cron-Job für deploy/backup.sh eingerichtet?"
  exit 1
fi
age_h=$(( ( $(date +%s) - $(stat -c %Y "$latest") ) / 3600 ))
if [ "$age_h" -gt 26 ]; then
  alert "Backup veraltet" "Die letzte Sicherung $(basename "$latest") ist $age_h Stunden alt. Erwartet: täglich."
  exit 1
fi

result=$(docker run --rm -v "$latest:/backup.sqlite:ro" "$IMAGE" php -r '
  try {
    $p = new PDO("sqlite:/backup.sqlite", null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $ok = $p->query("PRAGMA integrity_check")->fetchColumn();
    $t = $p->query("SELECT COUNT(*) FROM entries WHERE type = \"booking\"")->fetchColumn();
    $v = $p->query("SELECT COUNT(*) FROM vouchers")->fetchColumn();
    echo $ok === "ok" ? "OK $t $v" : "DEFEKT $ok";
  } catch (Throwable $e) { echo "DEFEKT " . $e->getMessage(); }' 2>&1)

if [[ "$result" == OK* ]]; then
  read -r _ bookings vouchers <<<"$result"
  alert "Backup geprüft: in Ordnung" "Letzte Sicherung: $(basename "$latest") ($age_h Std. alt), lesbar.
Enthalten: $bookings Termine, $vouchers Gutscheine."
else
  alert "Backup DEFEKT" "Die Sicherung $(basename "$latest") ist nicht lesbar: $result"
  exit 1
fi
