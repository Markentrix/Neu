@echo off
setlocal
title Markentrix - Website veroeffentlichen

rem Dieses Skript liegt neben dem Ordner "dist". Nur "dist" wird hochgeladen.
set "SRC=%~dp0dist"
set "PAKET=%TEMP%\markentrix-dist.tar"
set "SERVER=deploy@5.75.146.212"

if not exist "%SRC%\index.html" (
  echo FEHLER: Der Ordner dist wurde nicht gefunden oder enthaelt keine index.html.
  echo Gesucht in: %SRC%
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
ssh %SERVER% "tar -xf ~/markentrix-dist.tar -C /srv/sites/markentrix && rm ~/markentrix-dist.tar"
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
echo.
echo Fertig. Die Aenderungen sind live.
echo Hinweis: Dateien, die du aus dist geloescht hast, bleiben auf dem Server liegen.
pause
