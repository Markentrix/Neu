@echo off
setlocal
title Markentrix - Kundenwebsite veroeffentlichen

rem Benutzung: Den Ordner der Kundenseite (mit index.html) per Maus auf diese Datei ziehen
rem oder die Datei doppelklicken und die Fragen beantworten.
set "SERVER=deploy@5.75.146.212"
set "PAKET=%TEMP%\kunde-dist.tar"

echo.
set /p "ID=Kundennummer (z.B. MX-1007): "
echo %ID%| findstr /r /x "MX-[0-9][0-9][0-9][0-9]*" >nul
if errorlevel 1 (
  echo FEHLER: "%ID%" ist keine gueltige Kundennummer. Erwartet wird z.B. MX-1007.
  pause
  exit /b 1
)

set "SRC=%~1"
if "%SRC%"=="" (
  set /p "SRC=Ordner der Kundenseite (hierher ziehen oder Pfad einfuegen): "
)
set "SRC=%SRC:"=%"
if not exist "%SRC%\index.html" (
  echo FEHLER: In diesem Ordner liegt keine index.html:
  echo   %SRC%
  echo Gemeint ist der Ordner, der direkt die fertigen Seiten enthaelt.
  pause
  exit /b 1
)

echo.
echo Pruefe, ob %ID% auf dem Server angelegt ist ...
ssh %SERVER% "test -d /srv/sites/kunden/%ID%"
if errorlevel 1 (
  echo FEHLER: %ID% gibt es auf dem Server noch nicht oder der Server ist nicht erreichbar.
  echo Zuerst auf dem Server kunde-anlegen.sh fuer diesen Kunden ausfuehren.
  pause
  exit /b 1
)

echo.
echo Diese Seite wird jetzt fuer %ID% auf dem Server veroeffentlicht:
echo   %SRC%
echo Die Dateien dort werden ersetzt bzw. ergaenzt (nichts wird geloescht).
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
scp "%PAKET%" %SERVER%:~/kunde-dist.tar
if errorlevel 1 (
  echo FEHLER beim Upload. Die Seite auf dem Server wurde nicht veraendert.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)

echo [3/3] Dateien werden auf dem Server aktiviert ...
ssh %SERVER% "tar -xf ~/kunde-dist.tar -C /srv/sites/kunden/%ID% && rm ~/kunde-dist.tar"
if errorlevel 1 (
  echo FEHLER auf dem Server. Bitte die Meldung oben ansehen.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)

del "%PAKET%" >nul 2>&1
echo.
echo Fertig. Die Seite von %ID% ist aktualisiert.
echo Hinweis: Dateien, die du lokal geloescht hast, bleiben auf dem Server liegen.
pause
