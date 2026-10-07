@echo off
setlocal
title Markentrix - Demo hochladen

rem Benutzung: Den Ordner der Demo-Website (mit index.html) auf diese Datei ziehen
rem oder doppelklicken und die Fragen beantworten. Am Ende steht der Link da (und liegt in der Zwischenablage).
set "SERVER=deploy@5.75.146.212"
set "PAKET=%TEMP%\demo-dist.tar"
set "LINK="

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
  set /p "SRC=Ordner der Demo (hierher ziehen oder Pfad einfuegen): "
)
set "SRC=%SRC:"=%"
if not exist "%SRC%\index.html" (
  echo FEHLER: In diesem Ordner liegt keine index.html:
  echo   %SRC%
  pause
  exit /b 1
)

echo.
echo Demo fuer %ID% wird hochgeladen aus:
echo   %SRC%
echo.
choice /c JN /m "Jetzt hochladen (J = ja, N = abbrechen)"
if errorlevel 2 (
  echo Abgebrochen. Es wurde nichts veraendert.
  pause
  exit /b 0
)

echo.
echo [1/3] Demo-Adresse wird auf dem Server bereitgestellt ...
for /f "tokens=2 delims==" %%A in ('ssh %SERVER% "/opt/neu/server/scripts/demo-anlegen.sh %ID%" ^| findstr "^LINK="') do set "LINK=%%A"
if "%LINK%"=="" (
  echo FEHLER: Auf dem Server konnte keine Demo-Adresse angelegt werden.
  pause
  exit /b 1
)

echo [2/3] Dateien werden gepackt und hochgeladen ...
tar -cf "%PAKET%" -C "%SRC%" .
if errorlevel 1 (
  echo FEHLER beim Packen.
  pause
  exit /b 1
)
scp "%PAKET%" %SERVER%:~/demo-dist.tar
if errorlevel 1 (
  echo FEHLER beim Upload.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)

echo [3/3] Dateien werden aktiviert ...
ssh %SERVER% "tar -xf ~/demo-dist.tar -C /srv/sites/kunden/%ID% && rm ~/demo-dist.tar"
if errorlevel 1 (
  echo FEHLER auf dem Server. Bitte die Meldung oben ansehen.
  del "%PAKET%" >nul 2>&1
  pause
  exit /b 1
)
del "%PAKET%" >nul 2>&1

echo %LINK%| clip
echo.
echo ============================================================
echo  Fertig. Der Demo-Link fuer %ID% (liegt in der Zwischenablage):
echo.
echo    %LINK%
echo.
echo  Einfach dem Kunden schicken (Strg+V zum Einfuegen).
echo ============================================================
pause
