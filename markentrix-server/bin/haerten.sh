#!/usr/bin/env bash
# Server-Härtung: zeigt den Stand (--status) oder richtet die sicheren Teile ein (--anwenden).
# Die Firewall wird nur mit --firewall und nach Rückfrage eingeschaltet (sonst droht Aussperren).
set -u
[ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo starten."; exit 1; }
modus="${1:---status}"
z() { printf '  %-9s %s\n' "$1" "$2"; }

status() {
  echo "Sicherheits-Stand dieses Servers"
  if dpkg -s unattended-upgrades >/dev/null 2>&1 && grep -qs 'Unattended-Upgrade "1"' /etc/apt/apt.conf.d/20auto-upgrades; then z OK "Automatische Sicherheitsupdates aktiv"; else z OFFEN "Automatische Sicherheitsupdates fehlen (mkctl haerten --anwenden)"; fi
  if systemctl is-active --quiet fail2ban 2>/dev/null; then z OK "fail2ban läuft (sperrt Angreifer nach Fehlversuchen)"; else z OFFEN "fail2ban fehlt (mkctl haerten --anwenden)"; fi
  pw="$(sshd -T 2>/dev/null | awk '/^passwordauthentication/{print $2}')"
  if [ "$pw" = no ]; then z OK "SSH nur mit Schlüssel"; else z OFFEN "SSH erlaubt noch Passwörter (mkctl ssh-haerten, erst nach Schlüssel-Test)"; fi
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then z OK "Firewall (ufw) aktiv"; else z HINWEIS "Keine lokale Firewall aktiv. Empfohlen: Hetzner-Firewall (Cloud-Konsole) mit 22, 80, 443, oder mkctl haerten --firewall"; fi
  if [ -f /var/run/reboot-required ]; then z OFFEN "Neustart nötig (Kernel-/Systemupdate eingespielt): in einem ruhigen Moment 'reboot'"; else z OK "Kein Neustart nötig"; fi
  n="$(apt list --upgradable 2>/dev/null | grep -c upgradable || true)"; z INFO "$n Paket(e) mit Updates verfügbar"
}

anwenden() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq && apt-get install -y -qq unattended-upgrades fail2ban >/dev/null || { echo "Installation fehlgeschlagen."; exit 1; }
  printf 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";\n' > /etc/apt/apt.conf.d/20auto-upgrades
  # Kein automatischer Neustart: das entscheidest du selbst (Hinweis kommt im Selbsttest)
  printf 'Unattended-Upgrade::Automatic-Reboot "false";\n' > /etc/apt/apt.conf.d/52markentrix
  p="$(sshd -T 2>/dev/null | awk '/^port /{print $2}')"; p="${p:-22}"
  printf '[DEFAULT]\nbantime = 1h\nfindtime = 10m\nmaxretry = 5\n\n[sshd]\nenabled = true\nport = %s\n' "$p" > /etc/fail2ban/jail.d/markentrix.local
  systemctl enable --now fail2ban >/dev/null 2>&1; systemctl restart fail2ban
  echo "Eingerichtet: automatische Sicherheitsupdates (ohne Neustart) und fail2ban für SSH (Port $p)."
  echo; status
}

firewall() {
  command -v ufw >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y -qq ufw >/dev/null; }
  p="$(sshd -T 2>/dev/null | awk '/^port /{print $2}')"; p="${p:-22}"
  echo "Das schaltet die Firewall ein: erlaubt bleiben SSH (Port $p), 80 und 443. Alles andere wird von außen blockiert."
  echo "Hinweis: Docker veröffentlicht Ports an ufw vorbei. Die Container-Ports sind nur an 127.0.0.1 gebunden und deshalb nicht betroffen."
  read -r -p "Fortfahren? Die Hetzner-Konsole im Browser bleibt als Notzugang. (ja/nein): " a
  [ "$a" = ja ] || { echo "Abgebrochen. Nichts verändert."; exit 0; }
  ufw default deny incoming >/dev/null; ufw default allow outgoing >/dev/null
  ufw allow "$p"/tcp >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
  ufw --force enable >/dev/null && echo "Firewall ist an. Teste in einem zweiten Fenster, ob SSH noch geht. Zurück: ufw disable"
}

case "$modus" in
  --status|status) status ;;
  --anwenden|anwenden) anwenden ;;
  --firewall|firewall) firewall ;;
  *) echo "Aufruf: mkctl haerten [--status | --anwenden | --firewall]"; exit 1 ;;
esac
