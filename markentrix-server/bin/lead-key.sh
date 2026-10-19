#!/bin/bash
# Hinterlegt den Website-Check-Schlüssel für die Lead-Anbindung (ohne Sonderzeichen tippen zu müssen).
# Aufruf:  bash bin/lead-key.sh   -> Schlüssel einfügen, Enter.
set -e
D=/srv/markentrix-daten
mkdir -p "$D"
read -r -p "Schlüssel aus dem Portal einfügen und Enter: " K
K=$(printf '%s' "$K" | tr -d '[:space:]')
if [ ${#K} -lt 20 ]; then echo "Zu kurz - nichts gespeichert."; exit 1; fi
printf '%s' "$K" > "$D/lead-secret"
chown 82:82 "$D/lead-secret"
chmod 600 "$D/lead-secret"
echo "Gespeichert ($(wc -c < "$D/lead-secret") Zeichen)."
