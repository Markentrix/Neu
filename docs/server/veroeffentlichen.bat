@echo off
setlocal
title Markentrix - Website veroeffentlichen

rem Dieses Skript liegt neben dem Ordner "dist". Nur "dist" wird hochgeladen.
rem Stand 15.10.2026: Auf dem Server werden Dateien, die in dist nicht mehr
rem existieren, jetzt entfernt (alte Seiten wie Preise.dc.html verschwinden).
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
echo Die Website aus diesem Ordner wird jetzt LIVE auf markentrix.de veroeffentlicht:
echo   %SRC%
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
