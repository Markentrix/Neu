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
2. Optional zusätzlich ein Ereignis „danke_aufgerufen“ anlegen: Bedingung `page_location` enthält `/danke`. Als Schlüsselereignis markieren. Das ist die robustere Zählung, weil sie auch bei langsamer Verbindung greift.
3. Berichte → Akquisition → Traffic-Akquisition: Spalte „Schlüsselereignisse“ einblenden.

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

Wer den Bericht anfordert, erscheint wie jede Anfrage in der Mail „Neue Anfrage über markentrix.de“ (Quelle „Website-Check“) und im Protokoll. Die Mail enthält zusätzlich die Gesamtwertung, die sechs Bereichswerte und die Liste der mangelhaften Befunde, damit das Gespräch vorbereitet ist. Das Feld `kontakt_gewuenscht` zeigt, ob die Person ausdrücklich um Kontakt gebeten hat (`ja`) oder nur den Bericht möchte (`nein`). Nur bei `ja` ist ein Anruf oder eine persönliche Nachricht gedeckt; Werbe-E-Mails darüber hinaus nur mit gesonderter Einwilligung.

Der Kunde erhält einen Bericht mit allen Befunden als E-Mail (HTML und Text, Absender info@markentrix.de, Antworten gehen an Sie). Pro E-Mail-Adresse höchstens drei Berichte in 24 Stunden. Im Protokoll steht `"bericht":true`, wenn der Bericht rausging. In Analytics zählt das Ereignis `generate_lead` mit `location = Website-Check`; eine Weiterleitung auf `/danke` findet hier bewusst nicht statt, weil die Befunde direkt angezeigt werden.

Monatlich auszählen: `grep -c '"quelle":"Website-Check"' anfragen.log` (Berichtsanforderungen) und `grep -c '"kontakt_gewuenscht":"ja"' anfragen.log` (Kontaktwunsch).

## Bewerbungen

Bewerbungen von der Seite `/partner-werden` tragen die Quelle „Bewerbung“ (Mail „Neue Bewerbung über markentrix.de“, Betreff „[markentrix.de] Bewerbung: Name“). Zählen: `grep -c '"quelle":"Bewerbung"' anfragen.log`, nach Rolle: `grep -o '"rolle":"[^"]*"' anfragen.log | sort | uniq -c`. Nach Abschluss des Verfahrens die Einträge im Protokoll und die Mails löschen (Löschfrist laut Datenschutzerklärung: spätestens sechs Monate).

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
