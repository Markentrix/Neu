#!/usr/bin/env bash
# Neue Version aus Git holen, Container neu bauen, neue Inhalts-Vorlagen übernehmen und Website neu bauen.
set -euo pipefail
cd "$(dirname "$0")"
git -C .. pull --ff-only
docker compose up -d --build
sleep 3
docker compose exec -T app python3 /app/server/app.py inhalte-ergaenzen
docker compose exec -T app python3 /app/server/app.py build
echo "Update abgeschlossen."
