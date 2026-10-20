# Löschkonzept (Entwurf, vom Anwalt zu prüfen)

Die Fristen stehen in der Datenbank (`loeschregeln`, im Portal unter „Datenschutz & Qualität" sichtbar) und werden **täglich automatisch** umgesetzt (Job `fristen_loeschen`, ab 02:00 UTC). Jede Löschung steht im Löschprotokoll.

| Daten | Frist | Umsetzung |
|---|---|---|
| Leads (ohne Kundenbezug) | 12 Monate nach letzter Aktivität (`loeschen_nach`); tote/verlorene Leads nach 365 Tagen | automatisch; Leads im Status Termin/Angebot/Gewonnen bleiben |
| Lead-Finder-Rohdaten ohne Lead | 180 Tage | automatisch |
| Akquise-Antworten | 365 Tage | automatisch |
| Chatverlauf im Kundenbereich | 180 Tage (6 Monate, laut AVV) | automatisch |
| Audit-Log (Protokoll wesentlicher Aktionen) | 12 Monate (laut AVV) | automatisch |
| Anrufprotokoll (Rufnummer, Name, Zusammenfassung) | 180 Tage | automatisch (Angaben werden entfernt, der Zähler bleibt) |
| Glocke (Benachrichtigungen) | 60 Tage | automatisch |
| Abgelaufene Sitzungen | beim nächsten Login | automatisch |
| Kunden nach Vertragsende | Offboarding: Inhalte, Benutzer und Dateien werden gelöscht, Stammdaten anonymisiert; vorher Datenexport (ZIP) für den Kunden | per Knopfdruck im Admin (Offboarding) |
| Rechnungen und Belege | gesetzliche Aufbewahrungsfrist | **offen: Anwalt/Steuerberater bestätigt die Frist.** Bis dahin werden Belege nicht gelöscht |
| SEPA-Mandate | Widerruf/Vertragsende, Nachweisfrist nach Anwaltsvorgabe | **offen** |
| Sicherungen (Backups) | rotierend nach Aufbewahrungsregel des Backup-Skripts | gelöschte Daten verschwinden mit dem Ablauf der Sicherungen |

Auskunft und Export: Pro Kunde ZIP-Export im Admin (Kundenseite → Offboarding). Für Leads und Anfragende: Anfragen im Portal unter „Datenschutz & Qualität" erfassen.
