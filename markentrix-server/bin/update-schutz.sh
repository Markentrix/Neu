#!/usr/bin/env bash
# Wird von install.sh und "mkctl update" eingelesen (nicht direkt ausführen).
# Update mit Rückweg: vor dem Neubau die laufende Portal-Version merken, danach prüfen und bei einem Fehler automatisch zurückgehen.
# Gilt für das Portal (der Teil, der bei jedem Update neu gebaut wird). Datenbank-Änderungen bleiben bestehen, sie sind nur ergänzend.

portal_version_merken() {
  if docker image inspect markentrix-portal:local >/dev/null 2>&1; then
    docker tag markentrix-portal:local markentrix-portal:vorher 2>/dev/null && return 0
  fi
  return 1
}

portal_gesund() { # wartet bis zu 150 Sekunden auf "healthy", dann prüft ein Kurztest Portal und Anmeldung
  local i
  for i in $(seq 1 "${UPDATE_WARTEN:-50}"); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' mk-portal 2>/dev/null || true)" = healthy ] && break
    sleep "${UPDATE_PAUSE:-3}"
  done
  [ "$(docker inspect -f '{{.State.Health.Status}}' mk-portal 2>/dev/null || true)" = healthy ] || return 1
  # Nur Dinge, die vom Update abhängen (nicht Mail-Server oder Internet): Portal antwortet, und die Anmeldung weist falsche Daten sauber ab (das braucht die Datenbank)
  curl -fsS --max-time 10 http://127.0.0.1:8090/healthz >/dev/null 2>&1 || return 1
  local st
  st="$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' -H 'X-MK: 1' -H 'Content-Type: application/json' -d '{"email":"selbsttest@invalid.example","password":"falsch-falsch-falsch"}' http://127.0.0.1:8090/api/login 2>/dev/null || echo 0)"
  case "$st" in 400|401|403|429) return 0;; *) return 1;; esac
}

# Aufruf nach dem Neubau. Argument 1: Compose-Befehl als Text (z. B. "docker compose --project-directory ... -f ...")
update_pruefen_oder_zurueck() {
  local compose="$1"
  if portal_gesund; then echo "  Prüfung nach dem Update: Portal läuft und die Anmeldung antwortet."; return 0; fi
  echo "  WARNUNG: Das Portal ist nach dem Update nicht in Ordnung."
  if docker image inspect markentrix-portal:vorher >/dev/null 2>&1; then
    echo "  Ich gehe automatisch auf die vorherige Version zurück ..."
    docker tag markentrix-portal:vorher markentrix-portal:local
    # shellcheck disable=SC2086
    $compose up -d --no-build portal >/dev/null 2>&1
    if portal_gesund; then
      echo "  Die vorherige Version läuft wieder. Das Update wurde NICHT übernommen."
      echo "  Hinweis: Neue Datenbank-Einträge aus dem Update bleiben bestehen, das schadet der alten Version nicht."
      echo "  Bitte schicken Sie die Ausgabe von:  docker logs mk-portal --tail 80   (dann lässt sich der Fehler beheben)."
      docker exec mk-portal python -m app.cli alarm-mail warnung "Update zurückgenommen" "Das Portal war nach dem Update nicht in Ordnung. Es läuft wieder mit der vorherigen Version. Das Update wurde nicht übernommen." >/dev/null 2>&1 || true
      return 2
    fi
    echo "  Auch die vorherige Version läuft nicht. Bitte 'docker logs mk-portal --tail 80' ansehen oder die Sicherung zurückspielen (mkctl restore-test zeigt, ob sie lesbar ist)."
    return 3
  fi
  echo "  Es gibt keine vorherige Version zum Zurückgehen (Erstinstallation?). Bitte 'docker logs mk-portal --tail 80' ansehen."
  return 3
}
