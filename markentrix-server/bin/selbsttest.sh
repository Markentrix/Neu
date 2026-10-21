#!/usr/bin/env bash
# Selbsttest: prüft nach einem Update (und auf Wunsch jederzeit), ob die wichtigen Teile wirklich arbeiten.
# Aufruf:  mkctl selbsttest        (Exitcode 1 = mindestens ein Fehler; bei Fehlern geht eine Alarm-Mail raus)
set -uo pipefail
BASE=/opt/markentrix
# shellcheck disable=SC1091
[ -f "$BASE/.env" ] && { set -a; . "$BASE/.env"; set +a; }
FEHLER=0; BERICHT=""
z() { # ok|fehler|warn Text
  case "$1" in ok) printf '  OK       %s\n' "$2";; warn) printf '  WARNUNG  %s\n' "$2";; *) printf '  FEHLER   %s\n' "$2"; FEHLER=$((FEHLER+1)); BERICHT+="- $2"$'\n';; esac
}
echo "Selbsttest $(date '+%d.%m.%Y %H:%M')"
# 1) Container
for c in mk-db mk-portal; do
  [ "$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo fehlt)" = running ] && z ok "Container $c läuft" || z fehler "Container $c läuft nicht"
done
# 2) Portal-Funktionen (im Container): Anmeldung, Datenbank, Mail-Server, Website-API, Hintergrundaufgaben
if OUT="$(docker exec mk-portal python -m app.cli selbsttest 2>&1)"; then echo "$OUT"; else
  echo "$OUT"; N="$(echo "$OUT" | grep -c '^  FEHLER')"; FEHLER=$((FEHLER+${N:-1})); BERICHT+="$(echo "$OUT" | grep '^  FEHLER' | sed 's/^  FEHLER */- /')"$'\n'
fi
# 3) Server-Dienst für Aufträge (Cron, jede Minute): schreibt jedes Mal die Liste der Sicherungen
Q="$BASE/queue/sicherungen.json"
for _ in $(seq 1 7); do
  [ -f "$Q" ] && [ $(( $(date +%s) - $(stat -c %Y "$Q") )) -lt 150 ] && break; sleep 10
done
[ -f "$Q" ] && [ $(( $(date +%s) - $(stat -c %Y "$Q") )) -lt 150 ] && z ok "Server-Dienst für Aufträge arbeitet (Upload, Wiederherstellung)" || z fehler "Server-Dienst für Aufträge (Cron) hat sich nicht gemeldet: Websites-Upload würde hängen"
# 4) Sicherung
if [ -f "$BASE/backups/last_success" ]; then
  H=$(( ( $(date +%s) - $(cat "$BASE/backups/last_success") ) / 3600 ))
  [ "$H" -le 36 ] && z ok "Letzte Sicherung vor ${H} Stunden" || z fehler "Letzte Sicherung ist ${H} Stunden alt"
else z fehler "Noch keine erfolgreiche Sicherung vorhanden"; fi
# 5) Von außen erreichbar (Caddy, Zertifikat)
if [ -n "${DOMAIN:-}" ]; then
  curl -fsS --max-time 15 "https://portal.${DOMAIN}/healthz" >/dev/null 2>&1 && z ok "Portal von außen erreichbar (https://portal.${DOMAIN})" || z fehler "Portal von außen nicht erreichbar (https://portal.${DOMAIN})"
fi
# 5b) Kennt der Webserver jede veröffentlichte Kunden-Domain? (sonst gibt es kein Zertifikat)
CS="$(cat "$BASE/caddy-sites-dir" 2>/dev/null || echo "$BASE/caddy/sites")"
FEHLT=""
for d in /srv/sites/live/*/; do
  n="$(basename "$d")"; [ -d "$d" ] || continue
  [ -f "$CS/$n.caddy" ] || FEHLT="$FEHLT $n"
done
[ -z "$FEHLT" ] && z ok "Jede Kunden-Website ist beim Webserver eingetragen" || z fehler "Beim Webserver fehlt der Eintrag für:$FEHLT (Abhilfe: mkctl caddy-neu)"
# 5c) Webserver: ist seine Konfiguration gültig, und liefert er jede Kunden-Domain mit Zertifikat aus? (lokal geprüft, unabhängig von DNS und Zwischenspeichern)
MODE="$(cat "$BASE/mode" 2>/dev/null || echo own)"; CC="$(cat "$BASE/caddy-container" 2>/dev/null || true)"
case "$MODE" in
  docker) [ -n "$CC" ] && { docker exec "$CC" caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && z ok "Webserver-Konfiguration ($CC) ist gültig" || z fehler "Webserver-Konfiguration ($CC) ist ungültig: neue Domains werden nicht geladen"; } ;;
  own) docker compose --project-directory "$BASE" -f "$BASE/docker-compose.yml" exec -T caddy caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && z ok "Webserver-Konfiguration ist gültig" || z fehler "Webserver-Konfiguration ist ungültig: neue Domains werden nicht geladen" ;;
esac
MYIP="${SERVER_IPV4:-$(curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true)}"
for d in /srv/sites/live/*/; do
  n="$(basename "$d")"; [ -d "$d" ] || continue
  CODE="$(curl -sS -m 12 --resolve "$n:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$n/" 2>/dev/null || true)"
  case "$CODE" in
    2*|3*) z ok "$n: Zertifikat und Seite werden ausgeliefert" ;;
    *) DNSIP="$(getent ahostsv4 "$n" 2>/dev/null | awk '{print $1; exit}')"
       if [ -n "$MYIP" ] && [ "$DNSIP" = "$MYIP" ]; then z fehler "$n: DNS stimmt, aber der Webserver liefert keine Seite mit Zertifikat aus (Abhilfe: mkctl caddy-neu, dann Log des Caddy ansehen)"
       else z warn "$n: noch kein Zertifikat, weil die Domain (noch) nicht auf diesen Server zeigt"; fi ;;
  esac
done
# 6) Speicherplatz
USE="$(df --output=pcent / | tail -1 | tr -dc 0-9)"; [ "${USE:-0}" -lt 85 ] && z ok "Festplatte zu ${USE} % belegt" || z fehler "Festplatte zu ${USE} % voll"
echo
if [ "$FEHLER" -eq 0 ]; then echo "Ergebnis: alles in Ordnung."; exit 0; fi
echo "Ergebnis: $FEHLER Fehler."
docker exec mk-portal python -m app.cli alarm-mail warnung "Selbsttest nach Update: $FEHLER Fehler" "$(printf 'Der Selbsttest hat Probleme gefunden:\n\n%s\nBitte auf dem Server "mkctl selbsttest" ausführen und die Meldungen prüfen.' "$BERICHT")" >/dev/null 2>&1 || true
exit 1
