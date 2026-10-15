@echo off
setlocal EnableDelayedExpansion
title Markentrix - Website veroeffentlichen

rem Dieses Skript liegt in einem beliebigen Ordner auf dem Windows-Rechner. Ablauf:
rem   1. Die Datei "markentrix-website.zip" aus dem Chat in denselben Ordner speichern
rem      (eine vorhandene gleichnamige Datei einfach ueberschreiben).
rem   2. Doppelklick auf dieses Skript, J druecken. Fertig.
rem Das Skript entpackt die ZIP nach "dist", prueft den Inhalt und laedt "dist" hoch.
rem Auf dem Server werden Dateien entfernt, die in der ZIP nicht mehr existieren.
set "SRC=%~dp0dist"
set "ZIP=%~dp0markentrix-website.zip"
set "PAKET=%TEMP%\markentrix-dist.tar"
set "SERVER=deploy@5.75.146.212"
set "ZIEL=/srv/sites/markentrix"

if not exist "%ZIP%" (
  echo FEHLER: Die Datei markentrix-website.zip wurde nicht gefunden.
  echo Erwartet in: %~dp0
  echo Bitte die ZIP aus dem Chat in diesen Ordner speichern und erneut starten.
  pause
  exit /b 1
)

echo.
echo [0/3] ZIP wird nach dist entpackt ...
if exist "%SRC%" rmdir /s /q "%SRC%"
mkdir "%SRC%"
tar -xf "%ZIP%" -C "%SRC%"
if errorlevel 1 (
  echo FEHLER beim Entpacken der ZIP. Es wurde nichts hochgeladen.
  pause
  exit /b 1
)
if not exist "%SRC%\index.html" (
  echo FEHLER: In der ZIP fehlt die index.html. Es wurde nichts hochgeladen.
  pause
  exit /b 1
)
if not exist "%SRC%\api\anfrage.php" (
  echo FEHLER: In der ZIP fehlt der Formular-Endpunkt api\anfrage.php. Es wurde nichts hochgeladen.
  pause
  exit /b 1
)
for /f "delims=" %%d in ('dir /b /a-d "%SRC%\*.html" ^| find /c /v ""') do set "SEITEN=%%d"
for %%z in ("%ZIP%") do set "ZIPDATUM=%%~tz"

echo.
echo Die Website aus dieser ZIP wird jetzt LIVE auf markentrix.de veroeffentlicht:
echo   %ZIP%
echo   Stand der ZIP: !ZIPDATUM!
echo   Seiten im Hauptordner: !SEITEN!
echo.
choice /c JN /m "Jetzt veroeffentlichen (J = ja, N = abbrechen)"
if errorlevel 2 (
  echo Abgebrochen. Es wurde nichts veraendert.
  pause
  exit /b 0
)

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
