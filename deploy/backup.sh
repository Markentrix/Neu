#!/usr/bin/env bash
# Tägliche Sicherung der Termin-Datenbank, z. B. per Cron:
#   15 3 * * * /opt/aj-atelier/deploy/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
docker compose exec -T web php -r '$p=new PDO("sqlite:/var/www/site/app/data/bookings.sqlite"); $p->exec("VACUUM INTO \"/tmp/backup.sqlite\"");'
docker compose cp web:/tmp/backup.sqlite "backups/bookings-$(date +%F).sqlite"
find backups -name 'bookings-*.sqlite' -mtime +30 -delete
