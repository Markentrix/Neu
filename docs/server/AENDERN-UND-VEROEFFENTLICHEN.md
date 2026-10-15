# Website ändern und veröffentlichen · Stand 15.10.2026

## Einmalige Einrichtung auf dem Windows-Rechner

1. Einen festen Ordner wählen, z. B. `C:\Users\chris\Desktop\Markentrix\Eigene Seite\Markentrix`.
2. `veroeffentlichen.bat` (aus diesem Ordner im Repository bzw. aus dem Chat) dort speichern.
3. Einmalig die Sperre für heruntergeladene Dateien aufheben (PowerShell):
   ```
   Unblock-File "C:\Users\chris\Desktop\Markentrix\Eigene Seite\Markentrix\veroeffentlichen.bat"
   ```
   Das ist nur nötig, wenn die Batch-Datei neu heruntergeladen wurde. Die ZIP braucht das nicht.

## Ablauf bei jeder Änderung

1. Änderung im Chat anfordern. Sie wird umgesetzt, geprüft, gebaut und als `markentrix-website.zip` geliefert.
2. Die ZIP in den Ordner neben `veroeffentlichen.bat` speichern, eine vorhandene gleichnamige Datei überschreiben.
3. Doppelklick auf `veroeffentlichen.bat`. Das Skript entpackt die ZIP nach `dist`, zeigt Datum der ZIP und Seitenzahl an und fragt nach. J veröffentlicht, N bricht ab.
4. Die drei Prüfzeilen am Ende müssen 200, 200 und 405 zeigen.

## Für die Erstellung der ZIP (Repository)

`tools/paket.sh` baut die Seite mit allen Prüfungen und packt `dist/` so, dass die Dateien direkt im Wurzelverzeichnis der ZIP liegen. Nur dieses Format versteht die Batch-Datei.

## Hinweise

- Nie direkt in `dist` ändern: Beim nächsten Start wird der Ordner aus der ZIP neu aufgebaut.
- Die Server-Konfiguration (Caddy, PHP, Mail) bleibt davon unberührt, siehe `EINSPIELEN.md`.
- Zeigt das Skript „ZIP wurde nicht gefunden“, liegt die Datei nicht neben der Batch-Datei oder heißt anders als `markentrix-website.zip`.
