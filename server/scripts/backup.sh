#!/usr/bin/env bash
# Tägliches Backup von Websites, Caddy-Konfig und Zertifikaten; behält 14 Tage.
# Zusätzlich empfohlen: Hetzner-Backups/Snapshots im Cloud-Panel aktivieren (off-site).
set -euo pipefail
OUT=/srv/backups/daily; mkdir -p "$OUT"
tar czf "$OUT/srv-$(date +%F).tar.gz" -C /srv sites caddy-sites
docker run --rm -v server_caddy_data:/data -v "$OUT":/out alpine \
  tar czf "/out/caddy-data-$(date +%F).tar.gz" -C /data . 2>/dev/null || true
find "$OUT" -name '*.tar.gz' -mtime +14 -delete
