#!/usr/bin/env bash
# Automatischer Test des Portals auf einer FRISCHEN Test-Datenbank (nie gegen den echten Server!).
# Braucht: PostgreSQL 16, Python-Pakete aus portal/requirements.txt + aiosmtpd + httpx + pyflakes, Root-Rechte (su postgres).
# Aufruf:  sudo bash tests/run.sh
set -u
HIER="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HIER")"
T=/var/tmp/pt            # Arbeitsordner der Tests (die Testskripte erwarten genau diesen Pfad)
PGD=/var/tmp/pgtest      # Testdatenbank (eigener Cluster, Port 54329)
PGB="$(ls -d /usr/lib/postgresql/*/bin | sort -V | tail -1)"
PSQL() { su postgres -c "$PGB/psql -q -h $PGD -p 54329 $*"; }

[ "$(id -u)" = 0 ] || { echo "Bitte als root starten (sudo)."; exit 2; }
pkill -f "uvicorn app.main:app" 2>/dev/null; pkill -f "$T/smtp.py" 2>/dev/null; pkill -f "$T/mock.py" 2>/dev/null
su postgres -c "$PGB/pg_ctl -D $PGD/data stop -m fast" >/dev/null 2>&1
rm -rf "$PGD" "$T"; mkdir -p "$PGD" "$T/up" "$T/s/live" "$T/sites" "$T/b/queue"; chown postgres "$PGD"
cp "$HIER"/*.py "$T"/
su postgres -c "$PGB/initdb -D $PGD/data -A trust -E UTF8 --locale=C.UTF-8" >/dev/null || exit 2
su postgres -c "$PGB/pg_ctl -D $PGD/data -o '-p 54329 -k $PGD' -l $PGD/log start -w" >/dev/null || exit 2
PSQL "postgres -c \"create role markentrix superuser login\" -c \"create database markentrix owner markentrix\" -c \"create role mk_app login nosuperuser nobypassrls password 'apppw'\"" || exit 2
for f in "$REPO"/db/[0-9]*.sql; do
  PSQL "markentrix -v ON_ERROR_STOP=1 -f $f" >/dev/null 2>"$T/mig.err" || { echo "MIGRATION FEHLER in $(basename "$f")"; cat "$T/mig.err"; exit 1; }
done
PSQL "markentrix -f $REPO/db/999_rechte.sql" >/dev/null

export DATABASE_URL="postgresql://mk_app:apppw@localhost:54329/markentrix?host=$PGD" PORTAL_BASE_URL=http://localhost:8000 PORTAL_COOKIE_SECURE=0 \
  UPLOAD_DIR=$T/up SITES_LIVE=$T/s/live SITES_ROOT=$T/s QUEUE_DIR=$T/b/queue PORTAL_SECRET=testgeheimnis123 ANTHROPIC_BASE_URL=http://127.0.0.1:8999 PORTAL_JOBS=0
cd "$REPO/portal" || exit 2
python3 -m app.cli admin-add chef@test.de | grep PASSWORT | cut -d= -f2 > "$T/adminpw"
[ -s "$T/adminpw" ] || { echo "Admin konnte nicht angelegt werden."; exit 1; }
(cd "$T" && nohup python3 smtp.py >/dev/null 2>&1 &)
(cd "$T" && nohup python3 mock.py >/dev/null 2>&1 &)
# Vorlage der frischen Datenbank (mit Admin) – jede Testgruppe startet mit einer frischen Kopie
pkill -f "uvicorn app.main:app"; sleep 1
PSQL "postgres -c \"alter database markentrix rename to mk_vorlage\"" >/dev/null
starten() {
  { pkill -f "uvicorn app.main:app"; } 2>/dev/null; sleep 1
  PSQL "postgres -c \"drop database if exists markentrix\" -c \"create database markentrix template mk_vorlage owner markentrix\"" >/dev/null
  rm -rf "$T/up"/* "$T/b/queue"/* "$T/mails.txt"
  (cd "$REPO/portal" && nohup python3 -m uvicorn app.main:app --port 8000 >"$T/log" 2>&1 &)
  for i in $(seq 1 30); do curl -fs localhost:8000/healthz >/dev/null && return 0; sleep 1; done
  echo "Portal startet nicht:"; tail -20 "$T/log"; return 1
}
FEHLER=0
cd "$T" || exit 2
for t in t4 t6 t7 t8 t9 t10 t11 t12 t13 t14 t15 t16 smoke; do
  starten || { FEHLER=1; break; }
  python3 "$t.py" >"out_$t.txt" 2>&1; rc=$?
  n=$(grep -c "^FAIL" "out_$t.txt"); grep -qE "Fehler [1-9]" "out_$t.txt" && n=$((n+1))
  if [ "$rc" != 0 ] || [ "$n" != 0 ]; then echo "[$t] FEHLER (Exitcode $rc, $n FAIL)"; grep -E "^FAIL|Traceback|Error" "out_$t.txt" | head -8; FEHLER=1
  else echo "[$t] ok ($(grep -c '^OK' "out_$t.txt") Prüfungen)"; fi
done
cd "$REPO/portal" && python3 -m pyflakes app && echo "[pyflakes] ok" || FEHLER=1
for f in static/js/*.js; do node --check "$f" 2>/dev/null || { echo "[js] Syntaxfehler in $f"; FEHLER=1; }; done
for f in $(ls "$REPO"/bin/* "$REPO"/install.sh | grep -v "\.py$"); do bash -n "$f" 2>/dev/null || { echo "[bash] Syntaxfehler in $f"; FEHLER=1; }; done
pkill -f "uvicorn app.main:app"; pkill -f "$T/smtp.py"; pkill -f "$T/mock.py"
su postgres -c "$PGB/pg_ctl -D $PGD/data stop -m fast" >/dev/null 2>&1
[ $FEHLER = 0 ] && echo "ALLES OK" || echo "FEHLER GEFUNDEN"
exit $FEHLER
