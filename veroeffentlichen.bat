@echo off
setlocal EnableDelayedExpansion
title Markentrix - Website veroeffentlichen

rem Dieses Skript liegt im Git-Checkout des Repositories Markentrix/Neu neben dem
rem Ordner "dist". Ablauf: aktuellen Stand aus dem Repository holen, dann nur "dist"
rem hochladen. Auf dem Server werden Dateien entfernt, die in dist nicht mehr existieren.
set "SRC=%~dp0dist"
set "PAKET=%TEMP%\markentrix-dist.tar"
set "SERVER=deploy@5.75.146.212"
set "ZIEL=/srv/sites/markentrix"

if not exist "%SRC%\index.html" (
  echo FEHLER: Der Ordner dist wurde nicht gefunden oder enthaelt keine index.html.
  echo Gesucht in: %SRC%
  pause
  exit /b 1
)
if not exist "%SRC%\blog\das-system-website-sichtbarkeit-ki-assistent.html" (
  echo WARNUNG: dist scheint nicht der neue Stand zu sein, der Blog-Ordner ist unvollstaendig.
  echo Bitte zuerst "git pull" ausfuehren oder den Inhalt der ZIP nach dist kopieren.
  pause
  exit /b 1
)

echo.
echo [0/3] Aktuellen Stand aus dem Repository holen ...
git -C "%~dp0." pull --ff-only
if errorlevel 1 (
  echo FEHLER: git pull ist fehlgeschlagen. Es wurde nichts hochgeladen.
  echo Moegliche Ursachen: keine Internetverbindung, Anmeldung bei GitHub noetig
  echo oder lokale Aenderungen im Ordner. Meldung oben lesen oder im Chat zeigen.
  pause
  exit /b 1
)
for /f "delims=" %%b in ('git -C "%~dp0." rev-parse --abbrev-ref HEAD') do set "BRANCH=%%b"
for /f "delims=" %%c in ('git -C "%~dp0." log -1 --format=%%s') do set "LETZTE=%%c"

echo.
echo Die Website aus diesem Ordner wird jetzt LIVE auf markentrix.de veroeffentlicht:
echo   %SRC%
echo   Branch: !BRANCH!
echo   Letzte Aenderung: !LETZTE!
echo.
choice /c JN /m "Jetzt veroeffentlichen (J = ja, N = abbrechen)"
if errorlevel 2 (
  echo Abgebrochen. Es wurde nichts veraendert.
  pause
  exit /b 0
)

echo.
echo [1/3] Dateien werden gepackt ...
tar -cf "%PAKET%" -C "%SRC%" .
if errorlevel 1 (
  echo FEHLER beim Packen. Es wurde nichts veraendert.
  pause
  exit /b 1
)

echo [2/3] Upload zum Server ...
scp "%PAKET%" %SERVER%:~/markentrix-dist.tar
if errorlevel 1 (
  echo FEHLER beim Upload. Die Live-Seite wurde nicht veraendert.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)

echo [3/3] Dateien werden auf dem Server aktiviert ...
rem Entpacken in einen frischen Ordner, dann in einem Schritt mit dem Webroot
rem abgleichen (rsync loescht, was in dist nicht mehr existiert). Ohne rsync:
rem Webroot leeren und neu befuellen (wenige Sekunden Unterbrechung).
ssh %SERVER% "set -e; rm -rf ~/markentrix-neu; mkdir ~/markentrix-neu; tar -xf ~/markentrix-dist.tar -C ~/markentrix-neu; if command -v rsync >/dev/null; then rsync -a --delete ~/markentrix-neu/ %ZIEL%/; else find %ZIEL% -mindepth 1 -delete; cp -a ~/markentrix-neu/. %ZIEL%/; fi; rm -rf ~/markentrix-neu ~/markentrix-dist.tar"
if errorlevel 1 (
  echo FEHLER auf dem Server. Bitte die Meldung oben ansehen.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)

del "%PAKET%" >nul 2>&1

echo.
echo Pruefung der Live-Seite ...
curl.exe -s -o NUL -w "markentrix.de antwortet mit Status %%{http_code}\n" https://markentrix.de/
curl.exe -s -o NUL -w "Blog antwortet mit Status %%{http_code}\n" https://markentrix.de/blog/das-system-website-sichtbarkeit-ki-assistent
curl.exe -s -o NUL -w "Formular-Endpunkt antwortet mit Status %%{http_code}, erwartet 405 oder 400, nicht 404\n" https://markentrix.de/api/anfrage.php
echo.
echo Fertig. Die Aenderungen sind live.
pause
