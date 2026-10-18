#!/usr/bin/env bash
# Spielt die neueste Datenbank-Sicherung in einen Wegwerf-Container ein und prüft, ob sie brauchbar ist.
set -Eeuo pipefail
BASE=/opt/markentrix
LETZTE="$(ls -1 "$BASE/backups" | grep -E '^[0-9]{4}-' | sort | tail -1)"
[ -n "$LETZTE" ] || { echo "Keine Sicherung gefunden."; exit 1; }
DUMP="$BASE/backups/$LETZTE/markentrix-db.sql.gz"
[ -f "$DUMP" ] || { echo "Sicherung enthält keine Datenbank: $DUMP"; exit 1; }
NAME="mk-restore-test-$$"
status() { install -d -m 755 "$BASE/backup-status"; printf '%s\n' "$2" > "$BASE/backup-status/$1"; chmod 644 "$BASE/backup-status/$1"; }
cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
trap 'status restore_fehler "Wiederherstellungstest fehlgeschlagen ($LETZTE)"; echo "FEHLER beim Wiederherstellungstest" >&2' ERR

IMG="$(docker inspect -f '{{.Config.Image}}' mk-db)"
docker run -d --name "$NAME" -e POSTGRES_PASSWORD=test -e POSTGRES_USER=markentrix -e POSTGRES_DB=markentrix "$IMG" >/dev/null
for i in $(seq 1 40); do docker exec "$NAME" pg_isready -U markentrix -d markentrix >/dev/null 2>&1 && break; sleep 1; done
sleep 2
zcat "$DUMP" | docker exec -i "$NAME" psql -U markentrix -d markentrix -v ON_ERROR_STOP=0 -q >/dev/null 2>&1 || true
TABELLEN="$(docker exec "$NAME" psql -U markentrix -d markentrix -Atc "select count(*) from information_schema.tables where table_schema='public'")"
KUNDEN="$(docker exec "$NAME" psql -U markentrix -d markentrix -Atc "select count(*) from kunden")"
LIVE="$(docker exec mk-db psql -U markentrix -d markentrix -Atc "select count(*) from kunden")"
echo "Sicherung $LETZTE: $TABELLEN Tabellen, $KUNDEN Kunden (live: $LIVE)"
[ "$TABELLEN" -ge 50 ] || { status restore_fehler "Zu wenige Tabellen ($TABELLEN) in $LETZTE"; echo "FEHLER: zu wenige Tabellen"; exit 1; }
[ "$KUNDEN" -ge $(( LIVE > 0 ? LIVE - 5 : 0 )) ] || { status restore_fehler "Kundenzahl passt nicht ($KUNDEN statt $LIVE)"; echo "FEHLER: Kundenzahl passt nicht"; exit 1; }
status restore_last "$(date +%s)"; rm -f "$BASE/backup-status/restore_fehler"
echo "OK: Die Sicherung lässt sich wiederherstellen."
