# Sicherheits-Header: Vorschlag (nicht eingeführt)

Stand 05.10.2026. `dist/_headers` wurde nicht verändert. Dort gesetzt sind bereits: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (63072000, includeSubDomains, preload), COOP und `Content-Security-Policy: frame-ancestors 'none'`.

Vorschläge zur Prüfung:

- **Vollständige CSP:** zuerst als `Content-Security-Policy-Report-Only` testen. Ausgangspunkt: `default-src 'self'; img-src 'self' data:; font-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://markentrix.app.n8n.cloud; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`. Google Analytics und Metricool (laden erst nach Einwilligung) müssen in `script-src`/`connect-src` ergänzt werden. Wegen der Inline-Skripte der Startseite bleibt `'unsafe-inline'` vorerst nötig (Ziel: ausgelagerte Skripte oder Nonces).
- **HSTS-Preload:** nur beibehalten, wenn alle Subdomains dauerhaft HTTPS ausliefern.
- **Cross-Origin-Resource-Policy:** `same-site` für Bilder und Schriften prüfen.
