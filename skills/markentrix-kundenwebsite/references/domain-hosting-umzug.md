# Domain, DNS und Umzug auf den Markentrix-Server (Hetzner Nürnberg)

Kundenseite: Das Dokument `assets/dokumente/domain-checkliste.html` (PDF `Markentrix_Domain_Checkliste.pdf`) geht **mit Angebot und Briefing** an jeden Kunden. Ohne ausgefüllte Checkliste und Vollmacht kein Livegangstermin.

## Benötigte Angaben (Kurzfassung)
1. Domainname(n), Registrar, Domain-Inhaber (muss zum Impressum passen, sonst Inhaberwechsel klären), Zugang oder eingeschränkter Zusatzzugang zur Domainverwaltung, 2FA-Übergabe.
2. DNS: aktueller Zonenstand (A, AAAA, CNAME, MX, TXT inkl. SPF/DKIM/DMARC/Verifizierungen, SRV), aktuelle Nameserver, DNSSEC ja/nein, CAA-Einträge, Subdomains.
3. E-Mail: wo liegt das Postfach (MX bleibt unverändert), Mail für Formular-Zustellung, Anfrage-/Impressum-Adresse.
4. Bisherige Website bei Relaunch: CMS-/Hosting-Zugang, URL-Liste für 301-Weiterleitungen, Search Console, Google-Unternehmensprofil, eingebundene Dienste.
5. Schriftliche Vollmacht (Textform), Ansprechpartner beim Provider/IT, Wunschtermin.
6. Altes Hosting und Domainvertrag **nicht** vor erfolgreichem Livegang kündigen.

## Was wir liefern (projektbezogen eintragen)
IPv4 (A), IPv6 (AAAA), www-Eintrag, ggf. Nameserver (nur wenn wir DNS verwalten), ggf. TXT (Verifizierung, SPF für Formularversand), Zeitplan. **Nie IP-Adressen oder Nameserver erfinden**: aus dem Hetzner-Projekt des Kunden übernehmen.

## Standardvariante (empfohlen)
Domain und DNS bleiben beim Kunden-Provider. Kunde (oder wir mit Vollmacht/Zusatzzugang) setzt nur A/AAAA/www auf unseren Server. Vorteile: Eigentum und E-Mail bleiben unberührt, kein Transfer, geringes Risiko.
Alternativen: (a) Nameserver auf Hetzner DNS umstellen, wenn der Provider-DNS ungeeignet ist (alle Einträge vorher 1:1 übernehmen, MX/SPF/DKIM zuerst, DNSSEC vorher am Registrar entfernen); (b) Domain-Transfer nur auf ausdrücklichen Wunsch (Auth-Code, Registrar-Sperre lösen, Inhaber-Bestätigung, Kosten klären).

## Ablauf (intern)
1. **Vor Projektstart:** Checkliste anfordern, Vollmacht ablegen (nicht im Repo), Zonenstand sichern (Screenshot/Export, im Projektordner ablegen).
2. **Vorbereitung:** Site auf Hetzner (Nürnberg) deployen, TLS-Zertifikat (z. B. Let's Encrypt) vorbereiten, `www`/Nicht-`www` und HTTP→HTTPS-Weiterleitungen, Security-Header (`performance.md`), Redirect-Map. Test über Hosts-Datei oder temporäre Domain, **vor** DNS-Änderung, mit Formular- und Mail-Test.
3. **48 h vorher:** TTL der betroffenen Einträge auf 300 s senken. CAA prüfen (muss das Zertifikatsverfahren erlauben). DNSSEC-Strategie festlegen.
4. **Cutover (Zeitfenster außerhalb Spitzenzeiten):** A/AAAA/www umstellen, MX/SPF/DKIM unverändert lassen. Zertifikat ausstellen, HTTPS erzwingen.
5. **Verifikation:** Erreichbarkeit mit/ohne www, IPv4/IPv6, Zertifikatskette, Redirects (301), Formular-Zustellung, Eingang beim Kunden, E-Mail senden/empfangen, Search Console, Lighthouse. Rollback-Plan: alter Zonenstand liegt vor.
6. **Nach Livegang:** TTL wieder erhöhen, Search Console Sitemap, Monitoring (Uptime, Zertifikatsablauf), altes Hosting erst nach Freigabe des Kunden und Ablauf der Beobachtungszeit (z. B. 14 Tage) kündigen lassen.
7. **Zugangsdaten:** nur über sichere Wege annehmen (Passwort-Manager-Freigabe, verschlüsselter Link), nie in Tickets/Chats/Repo; Rechte minimal; nach Projektende Zugriff löschen und Kunde Passwörter ändern lassen.

## Typische Fehler (vermeiden)
MX/TXT beim Umzug gelöscht (E-Mail fällt aus) · DNSSEC aktiv und Nameserver gewechselt (Domain offline) · CAA blockiert Zertifikat · TTL zu hoch (lange Umstellung) · altes Hosting zu früh gekündigt · Domain auf Agentur/Privatperson registriert · www-Variante vergessen · Formular-Mail ohne SPF/DKIM landet im Spam.

## Datenschutz
Kunden-Zugangsdaten und Vollmachten sind personenbezogen bzw. sicherheitskritisch: Zugriff nur Projektbeteiligte, Speicherung verschlüsselt, Löschung nach Projektende bzw. Ablauf der Aufbewahrungsfrist. Im AVV ist Hetzner (Nürnberg) als Unterauftragnehmer genannt.
