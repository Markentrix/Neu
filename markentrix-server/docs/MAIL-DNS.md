# Mail-Zustellbarkeit: SPF, DKIM, DMARC

Das Portal verschickt Rechnungen, Einladungen, Berichte und Alarme. Damit diese Mails nicht im Spam landen, muss die Absender-Domain (z. B. markentrix.de) drei DNS-Einträge haben. Prüfen mit `mkctl mail-check` (auf dem Server).

| Eintrag | Wo | Zweck |
|---|---|---|
| SPF | TXT auf `markentrix.de` | Welche Server dürfen für die Domain senden. Der Wert kommt vom Mail-Anbieter (SMTP), z. B. `v=spf1 include:<anbieter> ~all` |
| DKIM | TXT auf `<selektor>._domainkey.markentrix.de` | Unterschrift der Mails. Schlüssel und Selektor gibt der Mail-Anbieter vor |
| DMARC | TXT auf `_dmarc.markentrix.de` | Regel bei Fehlern. Start: `v=DMARC1; p=none; rua=mailto:info@markentrix.de`, nach einigen Wochen ohne Probleme auf `p=quarantine` |

Ablauf: 1. SMTP-Zugang im Portal unter Einstellungen eintragen. 2. Beim Mail-Anbieter die SPF-/DKIM-Werte abrufen und bei Hetzner DNS (oder dem DNS-Anbieter) eintragen. 3. `mkctl mail-check markentrix.de <selektor>`. 4. Testmail an eine Gmail-Adresse senden, dort „Original anzeigen": SPF, DKIM und DMARC müssen „PASS" zeigen (oder https://www.mail-tester.com nutzen).

Hinweis: Absender im Portal und Domain der SPF/DKIM-Einträge müssen zusammenpassen.
