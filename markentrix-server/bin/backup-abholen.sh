#!/usr/bin/env bash
# Abholdienst für Sicherungen (z. B. auf den eigenen PC). Wird NUR über den eingeschränkten SSH-Schlüssel des Benutzers
# "mkabholer" aufgerufen (siehe: mkctl abholschluessel). Dieser Schlüssel kann nichts anderes als die folgenden vier Befehle:
#   liste            fertige Sicherungen (Name pro Zeile, neueste zuletzt)
#   hash <Name>      SHA-256 der Sicherung als Tar-Strom
#   holen <Name>     Sicherung als Tar-Strom ausgeben
#   groesse <Name>   Größe der Sicherung in Byte
set -Eeuo pipefail
B=/opt/markentrix/backups
[[ "${1:-}" != *$'\n'* && "${1:-}" != *$'\r'* ]] || { echo "Ungültiger Aufruf." >&2; exit 2; }
read -r befehl name rest <<<"${1:-}"
[ -z "${rest:-}" ] || { echo "Ungültiger Aufruf." >&2; exit 2; }

fertige() {
  # Eine Sicherung ist fertig, wenn config.tar.gz (letzter Schritt von backup.sh) da ist
  for d in "$B"/*/; do
    n="$(basename "$d")"
    [[ "$n" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}$ ]] || continue
    [ -f "$d/config.tar.gz" ] && [ ! -L "${d%/}" ] && echo "$n"
  done | sort
}
pruefe() {
  [[ "${name:-}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}$ ]] || { echo "Ungültiger Name." >&2; exit 2; }
  fertige | grep -qx "$name" || { echo "Sicherung nicht gefunden oder noch nicht fertig." >&2; exit 3; }
}
strom() { tar --sort=name --numeric-owner -C "$B" -cf - "$name"; }

case "${befehl:-}" in
  liste) [ -z "${name:-}" ] || { echo "Ungültiger Aufruf." >&2; exit 2; }; fertige ;;
  hash) pruefe; strom | sha256sum | cut -d' ' -f1 ;;
  holen) pruefe; logger -t mk-abholen "Sicherung $name wird abgeholt"; strom ;;
  groesse) pruefe; du -sb "$B/$name" | cut -f1 ;;
  *) echo "Unbekannter Befehl." >&2; exit 2 ;;
esac
