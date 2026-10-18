#!/usr/bin/env bash
# Überwachung: läuft alle 5 Minuten (cron). Meldet per Mail (über das Portal) und optional per Telegram,
# wenn etwas nicht stimmt, und sagt Bescheid, wenn es wieder läuft.
set -uo pipefail
BASE=/opt/markentrix
STATE=/var/lib/markentrix-watchdog; mkdir -p "$STATE"
# shellcheck disable=SC1091
[ -f "$BASE/.env" ] && { set -a; . "$BASE/.env"; set +a; }
PROBLEME=()
p() { PROBLEME+=("$1"); }

# 1) Container laufen und sind gesund
for c in mk-db mk-n8n-db mk-n8n mk-panel mk-portal; do
  s="$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo fehlt)"
  [ "$s" = running ] || p "Container $c läuft nicht ($s)"
  h="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$c" 2>/dev/null || true)"
  [ -z "$h" ] || [ "$h" = healthy ] || [ "$h" = starting ] || p "Container $c meldet: $h"
done
# 2) Portal von innen und von außen erreichbar
curl -fsS --max-time 10 http://127.0.0.1:8090/healthz >/dev/null 2>&1 || p "Portal antwortet lokal nicht"
[ -z "${DOMAIN:-}" ] || curl -fsS --max-time 15 "https://portal.${DOMAIN}/healthz" >/dev/null 2>&1 || p "Portal von außen nicht erreichbar (https://portal.${DOMAIN})"
# 3) Speicherplatz
USE="$(df --output=pcent / | tail -1 | tr -dc 0-9)"; [ "${USE:-0}" -lt 85 ] || p "Festplatte zu ${USE}% voll"
# 4) Sicherungen
alter() { [ -f "$1" ] && echo $(( ( $(date +%s) - $(cat "$1") ) / 3600 )) || echo 9999; }
[ "$(alter "$BASE/backups/last_success")" -le 36 ] || p "Letzte Sicherung ist älter als 36 Stunden"
if [ -n "${OFFSITE_TARGET:-}" ]; then
  [ "$(alter "$BASE/backup-status/offsite_last")" -le 36 ] || p "Externe Sicherung ist älter als 36 Stunden"
fi
[ ! -f "$BASE/backup-status/restore_fehler" ] || p "Wiederherstellungstest fehlgeschlagen: $(cat "$BASE/backup-status/restore_fehler")"

GEFUNDEN="$(printf '%s\n' "${PROBLEME[@]:-}" | sed '/^$/d' | sort)"
# Nur melden, was bei zwei Prüfungen hintereinander (ca. 5-10 Minuten) auftritt: so gibt es keinen Alarm bei Updates oder kurzen Neustarts.
VORHER="$(cat "$STATE/vorher" 2>/dev/null || true)"
printf '%s\n' "$GEFUNDEN" > "$STATE/vorher"
if [ "${1:-}" = "--test" ]; then AKTUELL="$GEFUNDEN"; else AKTUELL="$(comm -12 <(printf '%s\n' "$GEFUNDEN" | sed '/^$/d' | sort) <(printf '%s\n' "$VORHER" | sed '/^$/d' | sort))"; fi
LETZT="$(cat "$STATE/letzt" 2>/dev/null || true)"
ZEIT="$(cat "$STATE/zeit" 2>/dev/null || echo 0)"
JETZT="$(date +%s)"

senden() { # Stufe Titel Text
  local stufe="$1" titel="$2" text="$3" ok=0
  if [ -n "${TELEGRAM_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT:-}" ]; then
    curl -fsS --max-time 15 "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" --data-urlencode "chat_id=${TELEGRAM_CHAT}" --data-urlencode "text=${titel}
${text}" >/dev/null 2>&1 && ok=1
  fi
  # Mail über ein kurzlebiges Portal-Container-Abbild: funktioniert auch, wenn der Portal-Dienst selbst ausgefallen ist
  if docker image inspect markentrix-portal:local >/dev/null 2>&1; then
    docker run --rm --network markentrix_net -e "DATABASE_URL=postgresql://mk_app:${MK_APP_PASSWORD}@mk-db:5432/markentrix" -e "PORTAL_SECRET=${PORTAL_SECRET:-}" \
      -e "PORTAL_BASE_URL=https://portal.${DOMAIN:-localhost}" markentrix-portal:local python -m app.cli alarm-mail "$stufe" "$titel" "$text" >/dev/null 2>&1 && ok=1
  fi
  [ "$ok" = 1 ] || echo "[$(date '+%F %T')] Alarm konnte nicht zugestellt werden: $titel" >&2
}

if [ "${1:-}" = "--test" ]; then
  senden info "Markentrix: Testalarm" "Wenn du das liest, funktioniert die Überwachung."; echo "Testalarm gesendet."; exit 0
fi

if [ -n "$AKTUELL" ]; then
  if [ "$AKTUELL" != "$LETZT" ] || [ $(( JETZT - ZEIT )) -ge 21600 ]; then
    senden kritisch "Markentrix: Problem auf dem Server" "$AKTUELL"
    printf '%s\n' "$AKTUELL" > "$STATE/letzt"; echo "$JETZT" > "$STATE/zeit"
  fi
else
  if [ -n "$LETZT" ]; then
    senden info "Markentrix: Alles wieder in Ordnung" "Die zuvor gemeldeten Probleme sind behoben."
    : > "$STATE/letzt"; echo 0 > "$STATE/zeit"
  fi
fi
[ "${1:-}" != "--zeigen" ] || { echo "${GEFUNDEN:-Alles in Ordnung}"; }
