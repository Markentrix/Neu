# Anfragen messen

Stand 19.10.2026. Ziel: Sie sehen, woher Anfragen kommen und welche Seiten sie auslösen.

## Was die Website mitschreibt

| Signal | Wo | Bedingung |
|---|---|---|
| Aufruf von `/danke` | Google Analytics (Seitenaufruf) | nur nach Einwilligung in die Reichweitenmessung |
| Ereignis `form_submit` | beim Absenden | nur nach Einwilligung |
| Ereignis `generate_lead` mit Parameter `channel` | nach erfolgreichem Versand | nur nach Einwilligung |
| Feld „Wie sind Sie auf uns aufmerksam geworden?“ (`kanal`) | Kontaktformular und Potenzial-Check | immer, freiwillige Angabe der Person |
| `utm_source`, `utm_medium`, `utm_campaign` | in der Anfrage-Mail und im Protokoll | aus der Adresse; über Seitenwechsel nur nach Einwilligung in der Sitzung gemerkt |
| `utm_referrer` (verweisende Domain) | in der Anfrage-Mail | nur wenn keine utm-Parameter vorliegen |

Alle Felder erscheinen in der Mail „Neue Anfrage über markentrix.de“ und in `/srv/markentrix-daten/anfragen.log`.

## Einmalig einrichten (Google Analytics 4)

1. Verwaltung → Ereignisse: `generate_lead` als **Schlüsselereignis** markieren.
2. Ein Ereignis „danke_aufgerufen“ (Bedingung `page_location` enthält `/danke`) ist nur als Gegenprobe gedacht und wird **nicht** als Schlüsselereignis markiert, sonst zählt jede Anfrage doppelt.
2a. Als Schlüsselereignis markieren: ausschließlich `generate_lead`. `website_check`, `form_start`, `form_submit`, `phone_click` bleiben normale Ereignisse. Unter Verwaltung → Benutzerdefinierte Definitionen den Parameter `lead_type` als ereignisbezogene Dimension anlegen, damit Leads nach Art getrennt auswertbar sind (ohne diesen Schritt zeigt GA4 den Parameter nicht in Berichten).
3. Berichte → Akquisition → Traffic-Akquisition: Spalte „Schlüsselereignisse“ einblenden.

## Ereignisse (Stand 04.11.2026)

| Ereignis | Bedeutung | Parameter |
|---|---|---|
| `generate_lead` | **Die einzige Lead-Zählung.** Nur nach erfolgreichem Versand eines Formulars. | `lead_type`: `kontaktformular`, `website_check_bericht` (Kurzfassung angefordert), `rueckruf` (Rückruf-Karte), `checkliste_pdf` (Checkliste per E-Mail angefordert), `terminbuchung` (Termin im Portal-Kalender gebucht, Ereignis `mk-erstgespraech-gebucht` des Portal-Bausteins, ohne Termindaten); `location`, `channel` |
| `form_submit` | Absendeversuch, vor der Serverantwort. Kann höher sein als `generate_lead` (Fehler, Zeitüberschreitung). Nicht als Schlüsselereignis markieren. | `lead_type`, `location` |
| `website_check_start` | Adresse abgeschickt, Prüfung läuft. | – |
| `website_check` | Prüfung abgeschlossen, Ergebnis angezeigt (noch kein Kontakt). | `score` (hoch, mittel, niedrig) |
| `website_check_error` | Prüfung fehlgeschlagen (ungültige Adresse, Zeitüberschreitung, Server). | – |
| `form_start` | Erste Eingabe in einem Formular (Anfrage-Dialog, Kontaktformular, Check-Kurzfassung), einmal je Seitenaufruf. | `location` (Formularquelle) |
| `modal_open` | Dialog „Erstgespräch buchen“ (Portal-Kalender) geöffnet. | – |
| `phone_click`, `mail_click` | Klick auf Telefonnummer oder E-Mail-Adresse (getrennt von Formularen). | `location` (Seite) |
| `audio_intro_start`, `audio_intro_50`, `audio_intro_complete` | Audio „Kurz erklärt“ auf der Startseite: erster Start, Hälfte erreicht, bis zum Ende gehört. Nur normale Ereignisse, nicht als Schlüsselereignis markieren. Auswertung: Anteil `audio_intro_start` an den Seitenaufrufen der Startseite; Entscheidung nach vier Wochen (Richtwert unter 3 %: entfernen oder mit eigener Stimme neu aufnehmen). | `location` |

Auswertung der Terminbuchung: Untersuchen → Trichterauswertung `modal_open` → `generate_lead` mit `lead_type=terminbuchung`. Der Fragenassistent mit Preisangaben (`wizard_step`) wurde am 05.11.2026 durch den Portal-Kalender ersetzt.

## Anzeigen-Seiten (Stand 08.11.2026)

Für bezahlte Anzeigen gibt es zwei schlanke Seiten ohne Menü, mit genau einem Ziel (nicht im Suchindex, nicht in der Sitemap):

| Seite | Zweck | Ziel der Anzeige |
|---|---|---|
| `https://markentrix.de/lp/website-check` | Adresse prüfen, Kurzfassung, Termin | Lead-Magnet-Kampagne „Website-Check“ |
| `https://markentrix.de/lp/webdesign-celle` | Angebot, echte Projekte, Termin, Rückruf | Suchanzeigen „Webdesign Celle“, „Website erstellen lassen Celle“ |

Anzeigen-Links immer mit Herkunft versehen, zum Beispiel `?utm_source=google&utm_medium=cpc&utm_campaign=webdesign-celle`. Die Parameter landen in der Anfrage-Mail und (nach Einwilligung) in Analytics.

## Rückruf und Checkliste

- **Rückruf-Karte** (Startseite, Kontakt, Preise, Anzeigen-Seiten): Name und Telefonnummer genügen, keine E-Mail nötig. Die Mail an Sie zeigt „Jetzt anrufen“ als Hauptschaltfläche. Quelle `Rückruf`, `lead_type=rueckruf`.
- **Checkliste per E-Mail** (Seiten Website-Checkliste und SEO-Checkliste): Die PDFs (`static/downloads/`) entstehen mit `python3 tools/make_checklists.py` aus den Listen auf den Seiten und müssen nach Änderungen an den Listen neu erzeugt werden. Der Besucher bekommt genau eine E-Mail mit dem Link, keine Verteilerliste, keine Werbung. Quelle `Checkliste-PDF`, `lead_type=checkliste_pdf`. Der Ordner `/downloads/` ist in der robots.txt gesperrt.
- **Termin nach der Anfrage:** Die Danke-Seite (`/danke`) und die Bestätigung nach der Website-Check-Kurzfassung zeigen den Portal-Kalender. Bei Bewerbungen und Checklisten entfällt er.

## Eigene Besuche ausschließen

Die Website markiert Besuche, die vom eigenen Browser kommen, mit `traffic_type=internal`:

1. In jedem eigenen Browser (Laptop, Handy, Büro) einmal `https://markentrix.de/?intern=1` aufrufen und der Reichweitenmessung zustimmen. Aufheben mit `?intern=0`.
2. GA4: Verwaltung → Dateneinstellungen → Datenfilter → Filter „Interner Datenverkehr“ auf **Aktiv** stellen (steht anfangs auf „Testen“). Damit fließen markierte Besuche nicht mehr in die Berichte ein; rückwirkend gilt das nicht.
3. Testanfragen im Formular trotzdem nur mit einem erkennbaren Namen („Test“) absenden, damit sie in `anfragen.log` und im Wochenbericht auffallen.

## Search Console

- Property `markentrix.de` per DNS bestätigt, Sitemap `https://markentrix.de/sitemap.xml` einreichen.
- `/danke`, `/ki-checkliste` und `/404` sind absichtlich auf noindex und stehen nicht in der Sitemap.

## Links mit Herkunft

Für Beiträge in sozialen Netzwerken, Newsletter und Anzeigen immer Links mit Parametern verwenden (Vorlagen in `docs/SOCIAL.md`):

```
https://markentrix.de/?utm_source=instagram&utm_medium=social&utm_campaign=oktober-2026
```

Erlaubt sind Buchstaben, Ziffern, Leerzeichen, Punkt, Bindestrich und Unterstrich (bis 60 Zeichen).

## Leads aus dem Website-Check

Wer den Bericht anfordert, erscheint wie jede Anfrage in der Mail „Neue Anfrage über markentrix.de“ (Quelle „Website-Check“) und im Protokoll. Die Mail enthält zusätzlich die Gesamtwertung, die sechs Bereichswerte und die Liste der mangelhaften Befunde, damit das Gespräch vorbereitet ist. Das Kästchen `kontakt_gewuenscht` ist freiwillig (Kopplungsverbot, Art. 7 Abs. 4 DSGVO) und erscheint nur, wenn der Wert unter 100 von 100 liegt (Hinweis: „Wenn Sie möchten, melden wir uns bei Ihnen“). Nur bei `ja` ist Ihr Rückruf oder Ihre E-Mail zum Ergebnis gedeckt; bei `nein` bekommt die Person nur den Bericht. Die Telefonnummer ist ebenfalls freiwillig. Werbe-E-Mails darüber hinaus (Newsletter) nur mit gesonderter Einwilligung.

Der Kunde erhält eine Kurzfassung (Gesamtwert, Bereichswerte, Zahl der offenen Punkte je Bereich, davon mit hohem Gewicht, und was bereits in Ordnung ist) als E-Mail; die einzelnen Befunde zu offenen Punkten stehen nur in der internen Mail an Sie und werden im Erstgespräch besprochen (HTML und Text, Absender info@markentrix.de, Antworten gehen an Sie). Pro E-Mail-Adresse höchstens drei Berichte in 24 Stunden. Im Protokoll steht `"bericht":true`, wenn der Bericht rausging. In Analytics zählt das Ereignis `generate_lead` mit `location = Website-Check`; eine Weiterleitung auf `/danke` findet hier bewusst nicht statt, weil die Befunde direkt angezeigt werden.

Monatlich auszählen: `grep -c '"quelle":"Website-Check"' anfragen.log` (Berichtsanforderungen) und `grep -c '"kontakt_gewuenscht":"ja"' anfragen.log` (Kontaktwunsch).

## Bewerbungen

Bewerbungen von der Seite `/partner-werden` tragen die Quelle „Bewerbung“ (Mail „Neue Bewerbung über markentrix.de“, Betreff „[markentrix.de] Bewerbung: Name“). Zählen: `grep -c '"quelle":"Bewerbung"' anfragen.log`, nach Rolle: `grep -o '"rolle":"[^"]*"' anfragen.log | sort | uniq -c`. Nach Abschluss des Verfahrens die Einträge im Protokoll und die Mails löschen (Löschfrist laut Datenschutzerklärung: spätestens sechs Monate).

### Benachrichtigung bei jedem Check

Jeder durchgeführte Check löst eine interne Mail „[markentrix.de] Website-Check: <Adresse> (<Wert> von 100)“ an `MX_MAIL_TO` aus (Adresse, Zeitpunkt, Wert, Bereichswerte, offene Punkte mit Status und Gewicht; ohne Name, ohne IP). Dieselbe Adresse höchstens einmal in 6 Stunden, insgesamt höchstens 40 Mails je Stunde. Abschalten: Umgebungsvariable `MX_CHECK_NOTIFY=0` im PHP-Container. Die Mail wird erst nach der Antwort an den Besucher gesendet. Fordert der Besucher die Kurzfassung an, kommt zusätzlich wie bisher die Mail „Neue Anfrage über markentrix.de“ mit seinen Kontaktdaten.

## Wochenbericht

Jeden Montag kommt eine Mail „Wochenbericht markentrix.de: N Anfragen“ mit Quellen, Herkunft, Vorwochenvergleich und allen Eingängen der letzten sieben Tage. Einrichtung und Test: `docs/server/WOCHENBERICHT.md`. Die Auswertung am Monatsende unten bleibt als Gegenprobe möglich.

## Auswertung ohne Analytics

Auch ohne Einwilligung bleibt die Zählung möglich: Jede Anfrage steht mit Herkunft im Protokoll. Einmal im Monat auszählen:

```
cd /srv/markentrix-daten
grep -c '"quelle"' anfragen.log
grep -o '"kanal":"[^"]*"' anfragen.log | sort | uniq -c | sort -rn
```

## Hinweis Datenschutz

Das Merken der Kampagnenparameter in der Sitzung (`sessionStorage`) geschieht nur nach Einwilligung in die Reichweitenmessung. Das Feld „Wie sind Sie auf uns aufmerksam geworden?“ ist eine freiwillige Angabe und gehört zur Bearbeitung der Anfrage. Bitte beides bei der juristischen Prüfung der Datenschutzerklärung mitnennen.
