#!/bin/sh
# Täglich per Cron: DB sichern und (optional) auf Hetzner Storage Box kopieren
set -e
cd "$(dirname "$0")/.."
docker compose exec -T app node server/scripts/backup.js
# Optional: Kopie auf Storage Box (SSH-Key vorher einrichten)
# docker compose cp app:/data/backup ./backup && rsync -az -e "ssh -p23" ./backup/ uXXXXXX@uXXXXXX.your-storagebox.de:ic24-backup/
