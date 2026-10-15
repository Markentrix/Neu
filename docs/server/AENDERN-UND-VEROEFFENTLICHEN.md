# Website ändern und veröffentlichen · Weg 2 (manuell, ein Klick) · Stand 15.10.2026

## Einmalige Einrichtung auf dem Windows-Rechner

1. Git für Windows installieren, falls `git --version` in PowerShell einen Fehler zeigt: https://git-scm.com/download/win (Standardeinstellungen).
2. Repository als neuen Ordner holen (PowerShell):
   ```
   cd "C:\Users\chris\Desktop\Markentrix\Eigene Seite"
   git clone https://github.com/Markentrix/Neu.git Website
   cd Website
   git checkout claude/hopeful-bell-fov3tm
   ```
   Beim ersten Mal öffnet sich ein Browserfenster zur Anmeldung bei GitHub.
3. Fertig. Der Ordner `Website` enthält Quellen (`src`, `static`), Werkzeuge (`tools`), die fertige Seite (`dist`) und `veroeffentlichen.bat`.
   Der alte Ordner `Markentrix` mit der bisherigen Batch-Datei wird nicht mehr gebraucht.

## Ablauf bei jeder Änderung

1. Änderung im Chat anfordern. Sie wird umgesetzt, geprüft, gebaut und ins Repository geschoben.
2. `veroeffentlichen.bat` im Ordner `Website` doppelklicken. Das Skript holt den neuen Stand, zeigt Branch und letzte Änderung an und fragt nach. Mit J geht die Seite live, mit N passiert nichts.
3. Die drei Prüfzeilen am Ende müssen 200, 200 und 405 zeigen.

## Hinweise

- Nie direkt in `dist` ändern: Der nächste Build überschreibt es. Quellen liegen in `src` und `static`.
- Zeigt das Skript „git pull ist fehlgeschlagen“, meist liegt es an lokalen Änderungen im Ordner. In PowerShell im Ordner `Website`: `git status` zeigt sie, `git checkout -- .` verwirft sie.
- Wird die Arbeit später auf den Branch `main` zusammengeführt, einmalig `git checkout main` im Ordner `Website`. Danach holt das Skript automatisch von dort.
- Die Server-Konfiguration (Caddy, PHP, Mail) bleibt davon unberührt, siehe `EINSPIELEN.md`.
