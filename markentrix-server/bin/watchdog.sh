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
HEILUNG_LOG="$STATE/heilung.log"
# Selbstheilung: einen hängenden oder gestoppten Container einmal neu starten (höchstens einmal pro Stunde je Container).
# Nur im normalen Lauf (nicht bei --zeigen und --test). Bleibt das Problem, meldet der Wachdienst es wie gewohnt nach der zweiten Prüfung.
heilen() { # Container Grund
  [ -z "${1:-}" ] || [ -n "${MODUS:-}" ] && return 0
  local c="$1" marke="$STATE/heil-$1" jetzt; jetzt="$(date +%s)"
  [ -f "$marke" ] && [ $(( jetzt - $(cat "$marke" 2>/dev/null || echo 0) )) -lt 3600 ] && return 0
  echo "$jetzt" > "$marke"
  docker restart "$c" >/dev/null 2>&1 && echo "$(date '+%F %T') $c wurde automatisch neu gestartet ($2)" >> "$HEILUNG_LOG"
  if [ -f "$HEILUNG_LOG" ]; then tail -n 50 "$HEILUNG_LOG" > "$HEILUNG_LOG.tmp" && mv "$HEILUNG_LOG.tmp" "$HEILUNG_LOG"; fi
  return 0
}
MODUS="${1:-}"

# 1) Container laufen und sind gesund
for c in mk-db mk-n8n-db mk-n8n mk-panel mk-portal; do
  s="$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo fehlt)"
  [ "$s" = running ] || { p "Container $c läuft nicht ($s)"; [ "$s" = fehlt ] || [ "$s" = restarting ] || heilen "$c" "Zustand $s"; }
  h="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$c" 2>/dev/null || true)"
  [ -z "$h" ] || [ "$h" = healthy ] || [ "$h" = starting ] || { p "Container $c meldet: $h"; heilen "$c" "Zustand $h"; }
  # Startet der Container ständig von selbst neu (Absturzschleife)?
  rc="$(docker inspect -f '{{.RestartCount}}' "$c" 2>/dev/null || echo 0)"; [[ "$rc" =~ ^[0-9]+$ ]] || rc=0
  rcv="$(cat "$STATE/rc-$c" 2>/dev/null || echo "$rc")"; [[ "$rcv" =~ ^[0-9]+$ ]] || rcv=$rc; echo "$rc" > "$STATE/rc-$c"
  [ $(( rc - rcv )) -lt 3 ] || p "Container $c startet ständig neu (${rcv} auf ${rc} Neustarts in 5 Minuten)"
done
# 2) Portal von innen und von außen erreichbar
curl -fsS --max-time 10 http://127.0.0.1:8090/healthz >/dev/null 2>&1 || p "Portal antwortet lokal nicht"
[ -z "${DOMAIN:-}" ] || curl -fsS --max-time 15 "https://portal.${DOMAIN}/healthz" >/dev/null 2>&1 || p "Portal von außen nicht erreichbar (https://portal.${DOMAIN})"
VERFUEGBAR=$(( ${#PROBLEME[@]} == 0 ))   # 1 = Dienste liefen und das Portal war erreichbar (für die Verfügbarkeit der letzten 30 Tage)
# 3) Speicherplatz
USE="$(df --output=pcent / | tail -1 | tr -dc 0-9)"; [ "${USE:-0}" -lt 85 ] || p "Festplatte zu ${USE}% voll"
RAM_FREI="$(awk '/^MemTotal/{t=$2}/^MemAvailable/{a=$2}END{if(t>0)print int(a*100/t); else print 100}' /proc/meminfo 2>/dev/null || echo 100)"
[ "${RAM_FREI:-100}" -ge 8 ] || p "Arbeitsspeicher fast voll (nur ${RAM_FREI} % frei)"
INODES="$(df --output=ipcent / 2>/dev/null | tail -1 | tr -dc 0-9)"; [ "${INODES:-0}" -lt 90 ] || p "Dateisystem fast voll an Einträgen (Inodes zu ${INODES}% belegt)"
# 3a) Mail-Versand: mehrere Fehler bei Anmeldung oder Verbindung in den letzten 6 Stunden und seitdem keine erfolgreiche Mail
MAILFEHLER="$(docker exec mk-db psql -U markentrix -d markentrix -tAc "select count(*) filter (where not ok and fehlerart in ('anmeldung','verbindung')) from mail_protokoll m where zeit > now() - interval '6 hours' and zeit > coalesce((select max(zeit) from mail_protokoll where ok), '-infinity')" 2>/dev/null | tr -dc 0-9 || true)"
[ "${MAILFEHLER:-0}" -lt 3 ] || p "Der Mail-Versand schlägt fehl (${MAILFEHLER} Fehler bei Anmeldung oder Verbindung, seitdem keine Mail durchgegangen). Einstellungen → E-Mail prüfen"
DB_MB="$(docker exec mk-db psql -U markentrix -d markentrix -tAc "select pg_database_size(current_database())/1048576" 2>/dev/null | tr -dc 0-9 || true)"
# 3b) Sicherheitsupdate wartet auf Neustart (erst nach 7 Tagen melden, damit du in Ruhe planen kannst)
if [ -f /var/run/reboot-required ] && [ $(( $(date +%s) - $(stat -c %Y /var/run/reboot-required) )) -gt 604800 ]; then p "Der Server braucht seit über 7 Tagen einen Neustart (Sicherheitsupdate). Bitte in einem ruhigen Moment: reboot"; fi
# 4) Sicherungen
alter() { [ -f "$1" ] && echo $(( ( $(date +%s) - $(cat "$1") ) / 3600 )) || echo 9999; }
[ "$(alter "$BASE/backups/last_success")" -le 36 ] || p "Letzte Sicherung ist älter als 36 Stunden"
if [ -n "${OFFSITE_TARGET:-}" ]; then
  [ "$(alter "$BASE/backup-status/offsite_last")" -le 36 ] || p "Externe Sicherung ist älter als 36 Stunden"
fi
# Der Wiederherstellungstest läuft wöchentlich: wenn er seit über 10 Tagen nicht gelaufen ist (und schon länger Sicherungen existieren), ist das selbst ein Problem
ANZ_SICH="$(ls -1 "$BASE/backups" 2>/dev/null | grep -cE '^[0-9]{4}-' || true)"
if [ "${ANZ_SICH:-0}" -ge 9 ] && [ "$(alter "$BASE/backup-status/restore_last")" -gt 240 ]; then p "Der Wiederherstellungstest der Sicherung ist seit über 10 Tagen nicht gelaufen (mkctl restore-test)"; fi
[ ! -f "$BASE/backup-status/restore_fehler" ] || p "Wiederherstellungstest fehlgeschlagen: $(cat "$BASE/backup-status/restore_fehler")"

# 5) Zertifikat des Portals (Warnung ab 14 Tagen Restlaufzeit)
CERT_TAGE=-1
if [ -n "${DOMAIN:-}" ]; then
  ENDE="$(echo | timeout 15 openssl s_client -servername "portal.${DOMAIN}" -connect "portal.${DOMAIN}:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || true)"
  if [ -n "$ENDE" ]; then
    CERT_TAGE=$(( ( $(date -d "$ENDE" +%s) - $(date +%s) ) / 86400 ))
    [ "$CERT_TAGE" -ge 14 ] || p "Das Zertifikat von portal.${DOMAIN} läuft in ${CERT_TAGE} Tagen ab"
  fi
fi

# 6) Mail-Zustellbarkeit: SPF und DMARC der Absender-Domain (ohne sie landen Mails oft im Spam). Nur wenn "dig" vorhanden ist.
if [ -n "${DOMAIN:-}" ] && command -v dig >/dev/null 2>&1; then
  dig +short +time=3 +tries=1 TXT "${DOMAIN}" 2>/dev/null | grep -qi "v=spf1" || p "Für ${DOMAIN} fehlt der SPF-Eintrag im DNS (siehe docs/MAIL-DNS.md)"
  dig +short +time=3 +tries=1 TXT "_dmarc.${DOMAIN}" 2>/dev/null | grep -qi "v=DMARC1" || p "Für ${DOMAIN} fehlt der DMARC-Eintrag im DNS (siehe docs/MAIL-DNS.md)"
fi

 # Verfügbarkeit: eine Zeile je Lauf (Zeit, 1/0), nur die letzten rund 31 Tage
if [ -d "$BASE/backup-status" ] && [ -z "$MODUS" ]; then
  VL="$BASE/backup-status/verfuegbarkeit.log"; echo "$(date +%s) $VERFUEGBAR" >> "$VL"
  [ "$(wc -l < "$VL")" -le 9200 ] || { tail -n 8900 "$VL" > "$VL.tmp" && mv "$VL.tmp" "$VL"; }
  chmod 644 "$VL" 2>/dev/null || true
fi
GEFUNDEN="$(printf '%s\n' "${PROBLEME[@]:-}" | sed '/^$/d' | sort)"
# Status für die Admin-Übersicht im Portal (nur Zahlen und Meldungen, keine Zugangsdaten)
if [ -d "$BASE/backup-status" ]; then
  BACKUP_H="$(alter "$BASE/backups/last_success")"; OFFSITE_H="$(alter "$BASE/backup-status/offsite_last")"
  JSON_PROBLEME="$GEFUNDEN" JSON_RESTORE="$(alter "$BASE/backup-status/restore_last")" JSON_BACKUP="$BACKUP_H" JSON_OFFSITE="$OFFSITE_H" JSON_OFFSITE_AKTIV="${OFFSITE_TARGET:+1}" JSON_PLATTE="${USE:-0}" JSON_CERT="$CERT_TAGE" JSON_RAM="${RAM_FREI:-100}" JSON_DB="${DB_MB:-0}" JSON_HEILUNG="$(grep -E "^$(date +%F)|^$(date -d '-1 day' +%F)|^$(date -d '-2 day' +%F)" "$HEILUNG_LOG" 2>/dev/null | tail -n 5 || true)" python3 - "$BASE/backup-status" <<'PY' 2>/dev/null || true
import json, os, sys, time
e = os.environ
d = {"zeit": time.time(), "backup_stunden": int(e["JSON_BACKUP"]), "offsite_stunden": int(e["JSON_OFFSITE"]), "offsite_aktiv": bool(e.get("JSON_OFFSITE_AKTIV")),
     "restore_stunden": int(e.get("JSON_RESTORE", 9999)), "platte_prozent": int(e["JSON_PLATTE"]), "zertifikat_tage": int(e["JSON_CERT"]), "ram_frei_prozent": int(e.get("JSON_RAM") or 100), "db_mb": int(e.get("JSON_DB") or 0), "heilung": [x for x in e.get("JSON_HEILUNG", "").splitlines() if x.strip()], "probleme": [x for x in e.get("JSON_PROBLEME", "").splitlines() if x.strip()]}
p = sys.argv[1] + "/system.json"
open(p + ".tmp", "w").write(json.dumps(d)); os.chmod(p + ".tmp", 0o644); os.replace(p + ".tmp", p)
PY
fi
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
