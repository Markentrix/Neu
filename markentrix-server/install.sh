#!/usr/bin/env bash
# Markentrix Server-Paket: ein Befehl installiert alles.
#   sudo bash install.sh
# Das Skript kann gefahrlos mehrfach gestartet werden. Vorhandene Zugangsdaten werden nicht überschrieben.
set -Eeuo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE=/opt/markentrix
SITES=/srv/sites

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$*"; }
warn() { printf '  \033[33mHinweis:\033[0m %s\n' "$*"; }
die()  { printf '\n\033[31mABBRUCH:\033[0m %s\n' "$*" >&2; exit 1; }
trap 'die "Fehler in Zeile $LINENO. Das Skript kann erneut gestartet werden. Schick mir die letzten Zeilen der Ausgabe."' ERR

ver_ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]; }  # $1 >= $2

set_env() { # Datei Schlüssel Wert
  local f="$1" k="$2" v="$3"
  if grep -qE "^${k}=" "$f"; then sed -i "s|^${k}=.*|${k}=${v}|" "$f"; else printf '%s=%s\n' "$k" "$v" >> "$f"; fi
}

# ---------------------------------------------------------------- 1. Prüfungen
say "1/8 Prüfungen"
[ "$(id -u)" -eq 0 ] || die "Bitte mit sudo starten:  sudo bash install.sh"
command -v apt-get >/dev/null || die "Dieses Skript ist für Ubuntu oder Debian gedacht."

missing=()
for c in curl git openssl ss awk sed; do command -v "$c" >/dev/null || missing+=("$c"); done
if [ "${#missing[@]}" -gt 0 ]; then
  apt-get update -qq
  apt-get install -y -qq curl git openssl iproute2 gawk sed ca-certificates >/dev/null
fi
ok "Grundwerkzeuge vorhanden"

if ! command -v docker >/dev/null; then
  warn "Docker fehlt und wird mit dem offiziellen Installer von docker.com eingerichtet."
  curl -fsSL https://get.docker.com | sh
fi
compose_ver="$(docker compose version --short 2>/dev/null || true)"
[ -n "$compose_ver" ] || die "Docker Compose fehlt. Bitte 'apt-get install docker-compose-plugin' ausführen und das Skript neu starten."
ver_ge "${compose_ver#v}" 2.24.0 || die "Docker Compose ${compose_ver} ist zu alt (benötigt 2.24 oder neuer). Bitte Docker aktualisieren."
ok "Docker Compose ${compose_ver}"

mem_mb="$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)"
[ "$mem_mb" -ge 1800 ] || warn "Nur ${mem_mb} MB Arbeitsspeicher. Datenbank und n8n zusammen brauchen mindestens 2 GB."
mkdir -p /opt
disk_gb="$(df -BG --output=avail /opt | tail -n1 | tr -dc '0-9')"
[ "${disk_gb:-0}" -ge 15 ] || die "Zu wenig freier Speicher (${disk_gb} GB). Es werden mindestens 15 GB gebraucht."
ok "Arbeitsspeicher ${mem_mb} MB, frei ${disk_gb} GB"

# Läuft schon ein Caddy (z. B. für markentrix.de)? Der wird NICHT angefasst.
CADDY_MODE=own
EXISTING=""
if docker ps --format '{{.Names}}' | grep -qx 'mk-caddy'; then
  CADDY_MODE=own
else
  EXISTING="$(docker ps --format '{{.Names}}\t{{.Image}}' | awk -F'\t' 'tolower($2) ~ /caddy/ {print $1; exit}')"
  if [ -n "$EXISTING" ]; then
    CADDY_MODE=docker
  elif systemctl is-active --quiet caddy 2>/dev/null; then
    CADDY_MODE=host
  elif ss -ltn | awk '{print $4}' | grep -Eq '[:.](80|443)$'; then
    echo; ss -ltnp | grep -E '[:.](80|443)\s' || true
    die "Auf Port 80/443 lauscht ein unbekannter Dienst. Es wurde nichts verändert. Schick mir die Zeilen oben."
  fi
fi
case "$CADDY_MODE" in
  own)    ok "Kein Webserver gefunden: es wird ein eigener Caddy mitinstalliert" ;;
  docker) ok "Vorhandener Caddy gefunden (Container $EXISTING): er bleibt unverändert" ;;
  host)   ok "Vorhandener Caddy gefunden (Systemdienst): er bleibt unverändert" ;;
esac

# ---------------------------------------------------------------- 2. Angaben
say "2/8 Angaben"
mkdir -p "$BASE"
if [ -f "$BASE/.env" ]; then
  set -a; . "$BASE/.env"; set +a
  ok "Vorhandene Einstellungen übernommen (Domain: $DOMAIN)"
else
  read -r -p "Hauptdomain [markentrix.de]: " DOMAIN </dev/tty || true
  DOMAIN="${DOMAIN:-markentrix.de}"
  read -r -p "E-Mail für die HTTPS-Zertifikate [info@${DOMAIN}]: " ACME_EMAIL </dev/tty || true
  ACME_EMAIL="${ACME_EMAIL:-info@${DOMAIN}}"
fi
[[ "$DOMAIN" =~ ^([a-z0-9-]+\.)+[a-z]{2,}$ ]] || die "Ungültige Domain: $DOMAIN"

# ---------------------------------------------------------------- 3. Dateien
say "3/8 Dateien und Zugangsdaten anlegen"
install -d -m 755 "$BASE" "$BASE/bin" "$BASE/caddy/sites" "$SITES/live" "$SITES/demos"
install -d -m 700 "$BASE/backups"
cp "$SRC/templates/docker-compose.yml" "$BASE/docker-compose.yml"
cp "$SRC/templates/Caddyfile" "$BASE/Caddyfile"
rm -rf "$BASE/panel" && cp -r "$SRC/panel" "$BASE/panel"
rm -rf "$BASE/db" && cp -r "$SRC/db" "$BASE/db"
rm -rf "$BASE/portal" && cp -r "$SRC/portal" "$BASE/portal"
install -m 755 "$SRC/bin/backup.sh" "$SRC/bin/mkctl" "$BASE/bin/"
ln -sf "$BASE/bin/mkctl" /usr/local/bin/mkctl
[ -f "$BASE/caddy/sites/00-platzhalter.caddy" ] || echo "# Hier liegen die Kunden-Websites (mkctl site-add)" > "$BASE/caddy/sites/00-platzhalter.caddy"
echo "$CADDY_MODE" > "$BASE/mode"

NEW_PANEL_PW=""
if [ ! -f "$BASE/.env" ]; then
  NEW_PANEL_PW="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | cut -c1-20)"
  ( umask 077
    cat > "$BASE/.env" <<EOF
DOMAIN=$DOMAIN
ACME_EMAIL=$ACME_EMAIL
N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)
N8N_DB_PASSWORD=$(openssl rand -hex 16)
MK_DB_PASSWORD=$(openssl rand -hex 16)
MK_APP_PASSWORD=$(openssl rand -hex 16)
PANEL_PASSWORD=$NEW_PANEL_PW
EOF
  )
  ok "Zugangsdaten erzeugt (/opt/markentrix/.env, nur für root lesbar)"
fi
chmod 600 "$BASE/.env"
grep -q '^MK_DB_PASSWORD=' "$BASE/.env" || echo "MK_DB_PASSWORD=$(openssl rand -hex 16)" >> "$BASE/.env"
grep -q '^MK_APP_PASSWORD=' "$BASE/.env" || echo "MK_APP_PASSWORD=$(openssl rand -hex 16)" >> "$BASE/.env"
set -a; . "$BASE/.env"; set +a
chmod -R a+rX "$SITES"

# ---------------------------------------------------------------- 4./5. Datenbank
say "4/8 Eigene Datenbank (PostgreSQL) vorbereiten"
ok "PostgreSQL 16 wird auf diesem Server betrieben (kein externer Dienst, nur intern erreichbar)"

say "5/8 Datenbank starten"
cd "$BASE"
docker compose --project-directory "$BASE" -f "$BASE/docker-compose.yml" up -d mk-db
printf '  Warte auf die Datenbank '
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' mk-db 2>/dev/null || true)" = healthy ] && break
  printf '.'; sleep 3
done
echo
[ "$(docker inspect -f '{{.State.Health.Status}}' mk-db 2>/dev/null || true)" = healthy ] \
  || die "Die Datenbank ist nach 3 Minuten nicht bereit. Ausgabe von 'docker logs mk-db --tail 50' schicken."
ok "Datenbank läuft"
"$BASE/bin/mkctl" migrate
ok "Datenbankstruktur angelegt (Kunden, Zugänge, Pakete, Module, Projekte, Anfragen, Termine, Uploads ...)"
chown -R 10001:10001 "$SITES/live" 2>/dev/null || true

# ---------------------------------------------------------------- 6. n8n, Dashboard, Caddy
say "6/8 n8n, Server-Dashboard, Portal und Webserver starten"
cd "$BASE"
if [ "$CADDY_MODE" = own ]; then
  docker compose --project-directory "$BASE" -f "$BASE/docker-compose.yml" --profile own-caddy up -d --build
else
  docker compose --project-directory "$BASE" -f "$BASE/docker-compose.yml" up -d --build
fi
ok "Dienste gestartet"

if [ "$CADDY_MODE" = docker ]; then
  docker network connect markentrix_net "$EXISTING" 2>/dev/null || true
  ok "Vorhandener Caddy ist jetzt mit den neuen Diensten verbunden (nur Netzwerk, keine Einstellung geändert)"
fi

if [ "$CADDY_MODE" != own ]; then
  if [ "$CADDY_MODE" = docker ]; then U_N8N="mk-n8n:5678"; U_PANEL="mk-panel:8080"; U_PORTAL="mk-portal:8000"; else U_N8N="127.0.0.1:5678"; U_PANEL="127.0.0.1:8088"; U_PORTAL="127.0.0.1:8090"; fi
  cat > "$BASE/caddy-zusatz-fuer-bestehenden-caddy.txt" <<EOF
# Diese Blöcke in die vorhandene Caddyfile einfügen und Caddy neu laden.
n8n.${DOMAIN} {
	encode zstd gzip
	reverse_proxy ${U_N8N}
}
panel.${DOMAIN} {
	encode zstd gzip
	reverse_proxy ${U_PANEL}
}
portal.${DOMAIN} {
	encode zstd gzip
	reverse_proxy ${U_PORTAL}
}
EOF
  warn "Eintrag für den vorhandenen Caddy: /opt/markentrix/caddy-zusatz-fuer-bestehenden-caddy.txt"
fi

# Erster Admin für das Portal
ADMIN_OUT=""
for _ in $(seq 1 30); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' mk-portal 2>/dev/null || true)" = healthy ] && break
  sleep 2
done
if ! docker exec mk-db psql -U markentrix -d markentrix -tAc "select 1 from benutzer where rolle='admin' limit 1" | grep -q 1; then
  ADMIN_OUT="$(docker exec mk-portal python -m app.cli admin-add "$ACME_EMAIL" 2>&1 || true)"
  ADMIN_PW="$(echo "$ADMIN_OUT" | sed -n 's/^ADMIN_PASSWORT=//p')"
else
  ADMIN_PW="(Admin gibt es schon. Neues Passwort: mkctl admin-reset ${ACME_EMAIL})"
fi
[ -n "${ADMIN_PW:-}" ] || warn "Admin konnte nicht angelegt werden. Danach ausführen: mkctl admin-add ${ACME_EMAIL}"

# ---------------------------------------------------------------- 7. Sicherung
say "7/8 Tägliche Sicherung einrichten und einmal testen"
cat > /etc/cron.d/markentrix-backup <<'EOF'
15 3 * * * root /opt/markentrix/bin/backup.sh >> /var/log/markentrix-backup.log 2>&1
EOF
chmod 644 /etc/cron.d/markentrix-backup
"$BASE/bin/backup.sh"
ok "Sicherung funktioniert (täglich um 03:15 Uhr, 14 Tage Aufbewahrung)"

# ---------------------------------------------------------------- 8. Zusammenfassung
say "8/8 Fertig"
IP="$(curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
SHOW_PW="${NEW_PANEL_PW:-(unverändert, steht in /opt/markentrix/.env)}"

cat <<EOF

================================================================
 MARKENTRIX SERVER IST EINGERICHTET
================================================================
 1) DNS-Einträge anlegen (Typ A, Ziel: ${IP}):
      n8n.${DOMAIN}      panel.${DOMAIN}
      portal.${DOMAIN}   demo.${DOMAIN}
    Erst danach sind die Adressen von außen erreichbar.

 2) Adressen und Zugänge:
      Server-Dashboard   https://panel.${DOMAIN}
                         Benutzer: admin   Passwort: ${SHOW_PW}
      Portal (Admin)     https://portal.${DOMAIN}
                         E-Mail: ${ACME_EMAIL}   Passwort: ${ADMIN_PW:-siehe Hinweis oben}
                         (Kunden erhalten ihren Zugang über einen Einladungslink aus dem Admin-Bereich.)
      Datenbank          nur intern (Container mk-db), Zugang über mkctl psql
      n8n                https://n8n.${DOMAIN}
                         (Beim ersten Öffnen legst du dein Konto an.)

 3) Alle Zugangsdaten stehen in /opt/markentrix/.env.
    Diese Datei gehört in einen Passwortmanager. Ohne sie lässt sich nichts wiederherstellen.

 4) Hilfe im Alltag:  mkctl help
================================================================
EOF
if [ "$CADDY_MODE" != own ]; then
  echo " ACHTUNG: Es läuft schon ein Caddy. Die zwei Blöcke aus"
  echo " /opt/markentrix/caddy-zusatz-fuer-bestehenden-caddy.txt müssen"
  echo " noch in dessen Caddyfile eingefügt werden."
  echo
fi
