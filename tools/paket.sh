#!/usr/bin/env bash
# Baut die Website und packt dist/ als markentrix-website.zip (Dateien direkt im Wurzelverzeichnis der ZIP).
# Die ZIP ist das Übergabeformat für veroeffentlichen.bat (docs/server). Aufruf: tools/paket.sh [Zielordner]
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/qa.py   # Qualitäts-Gate: bricht bei Fehlern ab (docs/QUALITAETSREGELN.md)
python3 tools/build.py   # qa.py baut zwischendurch mit anderem Datum, deshalb zum Schluss normal bauen
outdir="$(cd "${1:-.}" && pwd)"
out="$outdir/markentrix-website.zip"
rm -f "$out"
(cd dist && zip -qr -X "$out" . -x '.DS_Store' '*/.DS_Store')
echo "$(unzip -l "$out" | tail -1 | awk '{print $2}') Dateien → $out"
