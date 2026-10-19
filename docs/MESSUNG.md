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

## Auswertung ohne Analytics

Auch ohne Einwilligung bleibt die Zählung möglich: Jede Anfrage steht mit Herkunft im Protokoll. Einmal im Monat auszählen:

```
cd /srv/markentrix-daten
grep -c '"quelle"' anfragen.log
grep -o '"kanal":"[^"]*"' anfragen.log | sort | uniq -c | sort -rn
```

## Hinweis Datenschutz

Das Merken der Kampagnenparameter in der Sitzung (`sessionStorage`) geschieht nur nach Einwilligung in die Reichweitenmessung. Das Feld „Wie sind Sie auf uns aufmerksam geworden?“ ist eine freiwillige Angabe und gehört zur Bearbeitung der Anfrage. Bitte beides bei der juristischen Prüfung der Datenschutzerklärung mitnennen.
