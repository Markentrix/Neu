#!/usr/bin/env bash
# Tägliche Sicherung: Datenbank + Inhalte. Per Cron aufrufen, z. B.:
#   15 3 * * * /opt/elbdetail/deploy/backup.sh >> /var/log/elbdetail-backup.log 2>&1
# Empfehlung: Ordner BACKUP_DIR zusätzlich auf eine Hetzner Storage Box spiegeln (rsync/borg).
set -euo pipefail
cd "$(dirname "$0")"
BACKUP_DIR="${BACKUP_DIR:-/opt/elbdetail-backups}"
mkdir -p "$BACKUP_DIR"
FILE=$(docker compose exec -T app python3 /app/server/app.py backup | tail -n1)
docker compose cp "app:${FILE}" "$BACKUP_DIR/"
find "$BACKUP_DIR" -name 'elbdetail-*.tar.gz' -mtime +30 -delete
echo "$(date -Is) Sicherung: $BACKUP_DIR/$(basename "$FILE")"
