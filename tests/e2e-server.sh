#!/usr/bin/env bash
# Startet den Server mit frischen Testdaten (wird von Playwright aufgerufen).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
cp -r "$ROOT/content" "$TMP/content"
rm -rf "$TMP/content/.media-cache"
export ELB_DATA="$TMP/data" ELB_CONTENT="$TMP/content" ELB_SITE_ROOT="$TMP/site" ELB_SERVE_STATIC=1 \
       ADMIN_USER=admin ADMIN_PASSWORD="E2E-Test-Passwort" COOKIE_SECURE=0 RATE_LIMIT_ANFRAGEN=1000 \
       PUBLIC_URL=http://127.0.0.1:8099 HOST=127.0.0.1 PORT=8099
exec python3 "$ROOT/server/app.py"
