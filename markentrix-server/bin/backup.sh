#!/usr/bin/env bash
# Tägliche Sicherung: Datenbank, n8n, Websites, Zugangsdaten.
# Läuft automatisch jede Nacht (cron) und kann mit "mkctl backup" von Hand gestartet werden.
set -Eeuo pipefail

BASE=/opt/markentrix
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y-%m-%d_%H%M)"
DEST="$BASE/backups/$STAMP"

umask 077
mkdir -p "$DEST"

fail() {
  echo "[$(date '+%F %T')] FEHLER: $*" >&2
  rm -rf "$DEST"
  exit 1
}
trap 'fail "Zeile $LINENO"' ERR

echo "[$(date '+%F %T')] Sicherung startet -> $DEST"

# 1) Markentrix-Datenbank (Kunden, Portal)
docker exec mk-db pg_dump -U markentrix -d markentrix | gzip > "$DEST/markentrix-db.sql.gz"
gzip -t "$DEST/markentrix-db.sql.gz"

# 2) n8n-Datenbank
docker exec mk-n8n-db pg_dump -U n8n -d n8n | gzip > "$DEST/n8n-db.sql.gz"
gzip -t "$DEST/n8n-db.sql.gz"

# 3) Dateien: n8n-Daten, Websites
if [ -d /srv/sites ]; then
  tar -czf "$DEST/sites.tar.gz" -C /srv sites
fi
docker run --rm -v markentrix_n8n_data:/data:ro -v "$DEST":/out alpine \
  tar -czf /out/n8n-data.tar.gz -C /data .

docker run --rm -v markentrix_portal_uploads:/data:ro -v "$DEST":/out alpine \
  tar -czf /out/portal-uploads.tar.gz -C /data . 2>/dev/null || true

# 4) Zugangsdaten und Konfiguration (ohne diese lässt sich nichts wiederherstellen)
tar -czf "$DEST/config.tar.gz" -C "$BASE" .env docker-compose.yml Caddyfile caddy 2>/dev/null || \
  tar -czf "$DEST/config.tar.gz" -C "$BASE" .env docker-compose.yml

# 5) Alte Sicherungen löschen
find "$BASE/backups" -mindepth 1 -maxdepth 1 -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} +

date +%s > "$BASE/backups/last_success"
echo "[$(date '+%F %T')] Sicherung fertig: $(du -sh "$DEST" | cut -f1)"
