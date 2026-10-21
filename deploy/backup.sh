#!/usr/bin/env bash
# Tägliche Sicherung der Termin-Datenbank nach /srv/backups/daily (14 Tage, wie das Server-Backup).
#   Cron (als deploy):  45 3 * * * /srv/apps/aj-atelier/deploy/backup.sh >> /var/log/backup.log 2>&1
set -euo pipefail
OUT=/srv/backups/daily; mkdir -p "$OUT"
docker exec aj-atelier php -r '$p=new PDO("sqlite:/var/www/site/app/data/bookings.sqlite"); @unlink("/tmp/backup.sqlite"); $p->exec("VACUUM INTO \"/tmp/backup.sqlite\"");'
docker cp aj-atelier:/tmp/backup.sqlite "$OUT/aj-atelier-$(date +%F).sqlite"
find "$OUT" -name 'aj-atelier-*.sqlite' -mtime +14 -delete
