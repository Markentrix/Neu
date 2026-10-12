@echo off
setlocal
title Markentrix - Demo hochladen

rem Benutzung: Den Ordner der Demo-Website (mit index.html) auf diese Datei ziehen
rem oder doppelklicken und die Fragen beantworten. Am Ende steht der Link da (und liegt in der Zwischenablage).
set "SERVER=deploy@5.75.146.212"
set "PAKET=%TEMP%\demo-dist.tar"
set "LINK="

echo.
set /p "ID=Name der Demo (z.B. mueller-kfz, nur kleine Buchstaben, Ziffern, Bindestrich): "
rem Name automatisch in Kleinbuchstaben umwandeln, Leerzeichen werden zu Bindestrichen
for /f "delims=" %%i in ('powershell -NoProfile -Command "('%ID%').ToLower().Trim().Replace(' ','-')"') do set "ID=%%i"
echo %ID%| findstr /r /x "[a-z0-9][a-z0-9-]*[a-z0-9]" >nul
if errorlevel 1 (
  echo FEHLER: "%ID%" ist kein gueltiger Name. Beispiel: mueller-kfz
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
echo Demo "%ID%" wird hochgeladen aus:
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
set "AUSGABE=%TEMP%\demo-ausgabe.txt"
ssh %SERVER% "/opt/neu/server/scripts/demo-anlegen.sh %ID%" > "%AUSGABE%" 2>&1
for /f "tokens=2 delims==" %%A in ('findstr "^LINK=" "%AUSGABE%"') do set "LINK=%%A"
if "%LINK%"=="" (
  echo FEHLER: Auf dem Server konnte keine Demo-Adresse angelegt werden. Meldung des Servers:
  type "%AUSGABE%"
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
ssh %SERVER% "tar -xf ~/demo-dist.tar -C /srv/sites/demos/%ID% && rm ~/demo-dist.tar"
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
echo  Fertig. Der Demo-Link fuer "%ID%" (liegt in der Zwischenablage):
echo.
echo    %LINK%
echo.
echo  Einfach dem Kunden schicken (Strg+V zum Einfuegen).
echo ============================================================
pause
