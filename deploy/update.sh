#!/usr/bin/env bash
# Sicheres Update des Buchungsdienstes (als deploy):
#   deploy/update.sh                                   nur Buchungsdienst aktualisieren
#   deploy/update.sh MX-1234 https://aj-atelier-wettmar.de   zusätzlich dist/ bauen und veröffentlichen
# Die neue Version wird zuerst getestet. Schlagen die Tests fehl, läuft die alte Version weiter.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
cd "$APP_DIR"

old=$(git rev-parse --short HEAD)
git pull --ff-only
new=$(git rev-parse --short HEAD)
echo "Version $old → $new"

docker build -q -t aj-atelier:neu . >/dev/null
echo "Teste neue Version …"
if ! docker run --rm -v "$APP_DIR:/src" -w /src aj-atelier:neu php tests/run.php; then
  echo "TESTS FEHLGESCHLAGEN – die bisherige Version läuft unverändert weiter."
  git reset --hard "$old" >/dev/null
  alert "Update abgebrochen" "Die neue Version $new hat die Tests nicht bestanden. Es läuft weiter Version $old."
  exit 1
fi

docker tag aj-atelier:neu aj-atelier:latest
docker compose up -d
echo "Buchungsdienst läuft mit Version $new."

if [ $# -ge 2 ]; then
  ID="$1"; URL="$2"
  [[ "$ID" =~ ^MX-[0-9]{4,}$ ]] || { echo "Ungültige Kundennummer: $ID"; exit 1; }
  docker run --rm -v "$APP_DIR:/src" -w /src -u "$(id -u):$(id -g)" aj-atelier:latest php tools/build-static.php --url="$URL"
  rsync -a --delete "$APP_DIR/dist/" "/srv/sites/kunden/$ID/"
  echo "dist/ veröffentlicht nach /srv/sites/kunden/$ID"
fi
