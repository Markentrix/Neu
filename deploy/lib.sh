# Gemeinsame Hilfsfunktionen für die Skripte in deploy/ (wird per „source“ geladen).
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${IMAGE:-aj-atelier:latest}"

# PHP aus dem Image ausführen – funktioniert auch, wenn der Container gerade nicht läuft.
php_in_image() {
  [ -f "$APP_DIR/app/config.local.php" ] || { echo "Fehlt: $APP_DIR/app/config.local.php" >&2; return 1; }
  docker run --rm --network web \
    -v "$APP_DIR/app/config.local.php:/var/www/site/app/config.local.php:ro" \
    -v aj-atelier_bookings:/var/www/site/app/data \
    "$@"
}

# Warnung per E-Mail (Empfänger: alertEmail in app/config.local.php)
alert() {
  php_in_image "$IMAGE" php /var/www/site/app/alert.php "$1" "$2" || echo "WARNUNG (Mail nicht möglich): $1 – $2" >&2
}
