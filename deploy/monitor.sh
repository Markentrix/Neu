#!/usr/bin/env bash
# Überwachung – alle 5 Minuten per Cron (als deploy):
#   */5 * * * * /srv/apps/aj-atelier/deploy/monitor.sh https://aj-atelier-wettmar.de >> /var/log/aj-atelier-monitor.log 2>&1
# Prüft Website (Caddy + dist/) und Buchungsdienst (/api/health.php).
# Warnt nach 2 Fehlschlägen in Folge per Mail, einmal pro Störung, und meldet, wenn wieder alles läuft.
set -uo pipefail
source "$(dirname "$0")/lib.sh"
URL="${1:?Aufruf: monitor.sh https://domain}"
STATE="${STATE_FILE:-/var/tmp/aj-atelier-monitor.state}"
read -r FAILS NOTIFIED 2>/dev/null < "$STATE" || { FAILS=0; NOTIFIED=0; }

problem=""
code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$URL/") || true
[ "$code" = 200 ] || problem="Website antwortet nicht (Startseite: HTTP $code)"
if [ -z "$problem" ]; then
  body=$(curl -s -m 15 "$URL/api/health.php") || true
  if ! grep -q '"ok":true' <<<"$body"; then
    problem="Buchungsdienst meldet ein Problem: ${body:-keine Antwort}"
  fi
fi

if [ -z "$problem" ]; then
  [ "$NOTIFIED" = 1 ] && alert "Wieder in Ordnung" "Website und Buchung unter $URL laufen wieder normal."
  echo "0 0" > "$STATE"
  exit 0
fi

FAILS=$((FAILS + 1))
echo "$(date -Is) Fehler $FAILS: $problem"
if [ "$FAILS" -ge 2 ] && [ "$NOTIFIED" = 0 ]; then
  alert "Störung: $URL" "$problem

Prüfen: cd $APP_DIR && docker compose ps && docker compose logs --tail=50 web
Hinweise zu den Prüfwerten:
- database/disk: Datenbank oder Speicherplatz
- config: app/config.local.php unvollständig
- mail_configured / mail_ok_last_hour: SMTP-Zugang prüfen (Bestätigungsmails kommen nicht an)
- cron: Cron-Job für app/cron.php läuft nicht (Erinnerungen werden nicht verschickt)"
  NOTIFIED=1
fi
echo "$FAILS $NOTIFIED" > "$STATE"
