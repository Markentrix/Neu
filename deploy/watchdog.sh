#!/usr/bin/env bash
# Wächter: prüft alle 5 Minuten Website, App, Speicherplatz und Sicherung. Bei Störung wird die App
# neu gestartet und eine E-Mail an NOTIFY_TO geschickt (über den SMTP-Zugang aus .env).
# Per Cron einrichten:
#   */5 * * * * /opt/elbdetail/deploy/watchdog.sh >> /var/log/elbdetail-watchdog.log 2>&1
set -uo pipefail
cd "$(dirname "$0")"
DOMAIN="$(grep -E '^DOMAIN=' .env | cut -d= -f2-)"
BACKUP_DIR="${BACKUP_DIR:-/opt/elbdetail-backups}"
STATE="${STATE_DIR:-/var/lib/elbdetail-watchdog}"
mkdir -p "$STATE"

alarm() {  # gleiche Meldung höchstens alle 6 Stunden
  local key="$1"; shift
  local f="$STATE/$key"
  if [ -f "$f" ] && [ $(( $(date +%s) - $(stat -c %Y "$f") )) -lt 21600 ]; then return; fi
  touch "$f"
  echo "$(date -Is) ALARM: $*"
  docker compose run --rm --no-deps -T app python3 /app/server/app.py alarm "$*" >/dev/null 2>&1 \
    || echo "$(date -Is) E-Mail konnte nicht gesendet werden"
}
ok() { rm -f "$STATE/$1"; }

# 1) Website von außen über Caddy (HTTPS) erreichbar?
if curl -fsS --max-time 15 "https://${DOMAIN}/api/health" >/dev/null; then
  ok web; rm -f "$STATE/fail_count"
else
  n=$(( $(cat "$STATE/fail_count" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$STATE/fail_count"
  if [ "$n" -ge 2 ]; then  # zweimal hintereinander: neu starten
    echo "$(date -Is) Website nicht erreichbar, starte neu"
    docker compose up -d >/dev/null 2>&1
    docker compose restart app caddy >/dev/null 2>&1
    sleep 20
    if curl -fsS --max-time 15 "https://${DOMAIN}/api/health" >/dev/null; then
      alarm restart "Website war nicht erreichbar und wurde automatisch neu gestartet. Jetzt wieder online."
      rm -f "$STATE/fail_count"
    else
      alarm web "Website https://${DOMAIN} ist nicht erreichbar, auch nach Neustart. Bitte prüfen: docker compose ps und docker compose logs --tail 100"
    fi
  fi
fi

# 2) Speicherplatz
used=$(df --output=pcent / | tail -1 | tr -dc '0-9')
if [ "${used:-0}" -ge 90 ]; then alarm disk "Festplatte zu ${used} % voll. Alte Sicherungen oder Docker-Reste löschen (docker system prune)."; else ok disk; fi

# 3) Sicherung aktuell (jünger als 2 Tage)?
latest=$(find "$BACKUP_DIR" -name 'elbdetail-*.tar.gz' -mtime -2 2>/dev/null | head -1)
if [ -z "$latest" ]; then alarm backup "Keine Sicherung jünger als 2 Tage in ${BACKUP_DIR}. Cron-Eintrag für backup.sh prüfen."; else ok backup; fi

# 4) Zertifikat läuft in weniger als 14 Tagen ab? (Caddy erneuert normalerweise automatisch)
end=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$end" ] && [ $(( ($(date -d "$end" +%s) - $(date +%s)) / 86400 )) -lt 14 ]; then
  alarm cert "HTTPS-Zertifikat für ${DOMAIN} läuft am ${end} ab. Caddy-Logs prüfen: docker compose logs caddy"
else ok cert; fi
