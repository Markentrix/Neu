# Pilot-Checkliste (Anadolu Market und erste Vertriebler)

Ziel: 4 Wochen echter Betrieb mit mindestens 3 Kunden und 2 Vertrieblern, ohne dass jemand mit Hilfe nachfragen muss. Alles, was hakt, kommt in die Fehlerliste unten.

## Vorher (einmalig, du)
- [ ] Server aktualisiert (`git pull`, `bash install.sh`), Strg+F5
- [ ] Admin-Passwort neu, 2FA eingerichtet
- [ ] Mail-Versand (SMTP) eingerichtet, `mkctl mail-check` ohne Fehler
- [ ] Offsite-Backup eingerichtet (`mkctl offsite-setup`), `mkctl restore-test` einmal von Hand erfolgreich
- [ ] Hetzner-Firewall 22/80/443, Repo auf privat, UptimeRobot
- [ ] Firmendaten vollständig (inkl. Logo), Gläubiger-ID und IBAN eingetragen
- [ ] Zum Üben: `mkctl demo-daten` (löscht mit `mkctl demo-daten-entfernen`)

## Kunde durchspielen
- [ ] Kunde anlegen, Einladung kommt an, Passwort setzen, Anmeldung
- [ ] Briefing ausfüllen, Dateien hochladen
- [ ] Nachricht an das Team, Antwort im Postfach, Benachrichtigung (Glocke/Push) kommt an
- [ ] Rechnung stellen, PDF prüfen, per Überweisung bezahlen (Zahlungseingang abgleichen)
- [ ] Lastschrift-Mandat im Kundenportal erteilen, Datei exportieren, **bei Finom Test-Upload** und Ergebnis notieren
- [ ] Famulor-Testanruf: Anruf erscheint unter „Anrufe"; in Einstellungen → Telefon-Assistent stehen die erkannten Felder (Screenshot an Claude schicken)
- [ ] Push auf iPhone (Home-Bildschirm-App) und Android: Testnachricht kommt an

## Vertriebler durchspielen
- [ ] Einladung, Anmeldung, „Heute anrufen" zeigt zugewiesene Leads
- [ ] Lead anrufen, Notiz, Wiedervorlage, Status ändern
- [ ] Gespräch buchen über /buchen, Benachrichtigung kommt an

## Fehlerliste (während des Piloten)
| Datum | Wer | Was ist passiert | Seite | Behoben am |
|---|---|---|---|---|
| | | | | |

## Abnahme
- [ ] 4 Wochen ohne kritischen Fehler (Datenverlust, falsche Rechnung, falsche Sichtbarkeit)
- [ ] Alle Fehler der Liste behoben oder bewusst verschoben
- [ ] Wiederherstellungstest in der Woche erfolgreich
