#!/usr/bin/env bash
# Erst-Einrichtung eines frischen Hetzner-Servers (Ubuntu 24.04 / Debian 12).
# Als root ausführen:  OWN_DOMAIN=markentrix.de ACME_EMAIL=du@markentrix.de bash bootstrap.sh
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Bitte als root ausführen"; exit 1; }
: "${OWN_DOMAIN:?OWN_DOMAIN fehlt (z.B. markentrix.de)}"
: "${ACME_EMAIL:?ACME_EMAIL fehlt (für Zertifikats-Benachrichtigungen)}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl git ufw fail2ban unattended-upgrades rsync

# --- Docker (offizielles Repo-Skript) ---
command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh

# --- Deploy-User (kein Root-Login mehr nötig) ---
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "$DEPLOY_USER"
  usermod -aG sudo,docker "$DEPLOY_USER"
  echo "$DEPLOY_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/90-$DEPLOY_USER"
  mkdir -p "/home/$DEPLOY_USER/.ssh"
  [ -f /root/.ssh/authorized_keys ] && cp /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/"
  chown -R "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
  chmod 700 "/home/$DEPLOY_USER/.ssh"; chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys" 2>/dev/null || true
fi

# --- SSH härten (nur wenn der Deploy-User einen Key hat, sonst Aussperr-Gefahr) ---
if [ -s "/home/$DEPLOY_USER/.ssh/authorized_keys" ]; then
  cat > /etc/ssh/sshd_config.d/99-hardening.conf <<CONF
PermitRootLogin no
PasswordAuthentication no
CONF
  systemctl reload ssh 2>/dev/null || systemctl reload sshd
else
  echo "WARNUNG: Kein SSH-Key gefunden – SSH-Härtung übersprungen."
fi

# --- Firewall + Fail2ban + Auto-Updates ---
ufw default deny incoming; ufw default allow outgoing
ufw allow 22/tcp; ufw allow 80/tcp; ufw allow 443/tcp; ufw allow 443/udp
ufw --force enable
systemctl enable --now fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades

# --- Verzeichnisse + Konfiguration ---
mkdir -p /srv/sites /srv/caddy-sites /srv/backups
cat > "$REPO_DIR/server/.env" <<ENV
ACME_EMAIL=$ACME_EMAIL
OWN_DOMAIN=$OWN_DOMAIN
ENV
chown -R "$DEPLOY_USER:$DEPLOY_USER" /srv/sites /srv/caddy-sites /srv/backups
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$REPO_DIR"
chmod +x "$REPO_DIR"/server/scripts/*.sh

# --- Caddy starten + eigene Website anlegen ---
cd "$REPO_DIR/server"
docker network inspect web >/dev/null 2>&1 || docker network create web
docker compose up -d
sudo -u "$DEPLOY_USER" "$REPO_DIR/server/scripts/add-site.sh" "$OWN_DOMAIN"

# Backup-Cron (täglich 03:30)
echo "30 3 * * * $DEPLOY_USER $REPO_DIR/server/scripts/backup.sh >> /var/log/backup.log 2>&1" > /etc/cron.d/markentrix-backup

echo
echo "Fertig. Teste: https://$OWN_DOMAIN  (DNS A/AAAA-Eintrag muss auf diesen Server zeigen)"
echo "Ab jetzt einloggen mit: ssh $DEPLOY_USER@<server-ip>"
