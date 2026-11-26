# Sicherheits-Kopfzeilen der Kundenseiten (Stand 26.11.2026)

Alle Kundenseiten senden jetzt sechs Sicherheits-Kopfzeilen: Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy und die Content-Security-Policy (CSP). Die Zeilen stehen im Code (`bin/worker.py`, Funktion `kopfzeilen()`), nicht in einem Snippet im Caddyfile: Jede Domain-Datei unter `/srv/caddy-sites/<domain>.caddy` bekommt den `header`-Block selbst. Das gilt für neue Domains sofort und für bestehende, unveränderte Dateien automatisch (der Worker läuft jede Minute und prüft vor dem Neuladen, ob Caddy die Datei akzeptiert; sonst bleibt die alte Fassung).

## Bedienung (auf dem Server als root)
- Nach dem Update (`git pull`, `sudo bash install.sh`) passiert alles von selbst. Kontrolle: `mkctl selbsttest` meldet je Kundendomain „alle 6 Sicherheits-Kopfzeilen werden gesendet“.
- Die CSP steht zuerst im **Testmodus** (`Content-Security-Policy-Report-Only`): Verstöße erscheinen nur in der Browser-Konsole (F12), nichts wird blockiert.
- Nach 3 bis 7 Tagen ohne Meldungen: `mkctl kunden-csp scharf`. Zurück: `mkctl kunden-csp testen`. Anzeige: `mkctl kunden-csp`.
- Vor dem Scharfschalten auf einigen Kundenseiten mit offener Konsole prüfen: Kontakt- und Terminformular absenden, Fotos hochladen, Bewertungen und PayPal-Knopf, Karte laden, Einwilligung „Alle erlauben“ (Google Analytics und Ads).

## Wichtig
- **Von Hand geänderte Domain-Dateien** (zum Beispiel eine Kundenseite mit eigenen Zusätzen) bleiben unangetastet und bekommen die Kopfzeilen nicht. Der Selbsttest warnt dann („nur n von 6“). Dort den `header { … }`-Block aus `bin/worker.py` von Hand einfügen.
- Nutzt eine Kundenseite weitere externe Dienste (YouTube, Calendly, Metricool …), muss deren Domain in die CSP, sonst blockiert sie diese im scharfen Modus. Dafür diese Domain-Datei von Hand pflegen.
- HSTS ohne `includeSubDomains`, mit Absicht.
- Die Seite `markentrix.de` selbst ist nicht betroffen (hat eigene Kopfzeilen).
- Rückweg: In der Domain-Datei den `header`-Block entfernen und `mkctl caddy-neu`. Wird die Datei danach von Hand geändert, rührt der Worker sie nicht mehr an.
