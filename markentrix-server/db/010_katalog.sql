-- 010 Katalog und Buchungen: Produkte und Preise (Preisliste Stand September 2026, netto), Konditionen,
-- Portal-Module, was ein Kunde gebucht hat. Preise gibt es NUR hier, alle Workflows lesen von hier.
BEGIN;

CREATE TABLE produkte (
  code            text PRIMARY KEY,
  kategorie       text NOT NULL CHECK (kategorie IN ('ki','website','ci','sichtbarkeit','personal_branding','lead')),
  name            text NOT NULL,
  beschreibung    text NOT NULL DEFAULT '',
  abrechnung      text NOT NULL CHECK (abrechnung IN ('monatlich','projekt','projekt_pflege')),
  laufzeit_monate int,                       -- Mindestlaufzeit (bei Websites: Pflege)
  inklusive_minuten     int,
  inklusive_nachrichten int,
  mehrminutenpreis_cent int,
  nur_auf_anfrage boolean NOT NULL DEFAULT false,
  einzeln_buchbar boolean NOT NULL DEFAULT true,
  aktiv           boolean NOT NULL DEFAULT true,
  sortierung      int NOT NULL DEFAULT 0
);

-- Preise versioniert: neuer Preis = neue Zeile mit späterem gueltig_ab. Alte Zeilen bleiben (Nachweis).
CREATE TABLE produkt_preise (
  id             bigserial PRIMARY KEY,
  produkt_code   text NOT NULL REFERENCES produkte(code) ON UPDATE CASCADE,
  gueltig_ab     date NOT NULL,
  einrichtung_cent bigint,
  monatlich_cent   bigint,                   -- bei Websites: Pflege je Monat
  projekt_cent     bigint,                   -- Einmalpreis (Website, CI)
  ab_preis       boolean NOT NULL DEFAULT false,   -- "ab 149 €"
  quelle         text NOT NULL DEFAULT '',
  freigegeben_von text,
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (produkt_code, gueltig_ab)
);

CREATE VIEW v_preise_aktuell WITH (security_invoker = true) AS
SELECT DISTINCT ON (p.code) p.code, p.kategorie, p.name, p.abrechnung, p.laufzeit_monate,
       pp.einrichtung_cent, pp.monatlich_cent, pp.projekt_cent, pp.ab_preis, pp.gueltig_ab,
       p.inklusive_minuten, p.inklusive_nachrichten, p.mehrminutenpreis_cent, p.nur_auf_anfrage
FROM produkte p
LEFT JOIN produkt_preise pp ON pp.produkt_code = p.code AND pp.gueltig_ab <= current_date
WHERE p.aktiv
ORDER BY p.code, pp.gueltig_ab DESC;

CREATE TABLE konditionen (
  schluessel  text PRIMARY KEY,
  wert_text   text,
  wert_zahl   bigint,
  beschreibung text NOT NULL DEFAULT '',
  geaendert_am timestamptz NOT NULL DEFAULT now()
);

-- Portal-Funktionen, die pro Kunde ein- und ausgeschaltet werden
CREATE TABLE module (
  code         text PRIMARY KEY,
  name         text NOT NULL,
  beschreibung text NOT NULL DEFAULT '',
  art          text NOT NULL DEFAULT 'portal' CHECK (art IN ('portal','agent')),  -- portal = Bereich im Kundenbereich, agent = Funktion/Agent
  sortierung   int NOT NULL DEFAULT 0
);
CREATE TABLE produkt_module (   -- Welche Module ein Produkt standardmäßig freischaltet
  produkt_code text NOT NULL REFERENCES produkte(code) ON UPDATE CASCADE ON DELETE CASCADE,
  modul_code   text NOT NULL REFERENCES module(code) ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY (produkt_code, modul_code)
);

ALTER TABLE kunden ADD CONSTRAINT kunden_paket_fk FOREIGN KEY (paket_code) REFERENCES produkte(code) ON UPDATE CASCADE;

CREATE TABLE kunden_module (
  kunden_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  modul_code   text NOT NULL REFERENCES module(code) ON UPDATE CASCADE ON DELETE CASCADE,
  aktiv        boolean NOT NULL DEFAULT false,
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kunden_id, modul_code)
);

-- Was der Kunde gebucht hat (mit dem damals gültigen Preis eingefroren)
CREATE TABLE buchungen (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id       uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  produkt_code    text NOT NULL REFERENCES produkte(code) ON UPDATE CASCADE,
  preis_id        bigint REFERENCES produkt_preise(id),
  einrichtung_cent bigint,
  monatlich_cent   bigint,
  projekt_cent     bigint,
  rabatt_cent      bigint NOT NULL DEFAULT 0,
  rabatt_grund     text,
  beginn          date,
  mindestlaufzeit_ende date,
  ende            date,
  status          text NOT NULL DEFAULT 'angefragt' CHECK (status IN ('angefragt','beauftragt','in_einrichtung','aktiv','pausiert','gekuendigt','beendet')),
  standort        text,                      -- pro Standort ein eigener Vertrag
  notiz           text,
  erstellt_am     timestamptz NOT NULL DEFAULT now(),
  geaendert_am    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX buchungen_kunde_idx ON buchungen (kunden_id, status);
CREATE TRIGGER buchungen_geaendert BEFORE UPDATE ON buchungen FOR EACH ROW EXECUTE FUNCTION set_geaendert();

SELECT rls_katalog('produkte'); SELECT rls_katalog('produkt_preise'); SELECT rls_katalog('konditionen');
SELECT rls_katalog('module');   SELECT rls_katalog('produkt_module');
SELECT rls_kunde('kunden_module', false);
SELECT rls_kunde('buchungen', false);

-- ----------------------------------------------------------------- Startdaten (Preisliste Stand September 2026, netto)
INSERT INTO produkte (code,kategorie,name,beschreibung,abrechnung,laufzeit_monate,inklusive_minuten,inklusive_nachrichten,mehrminutenpreis_cent,nur_auf_anfrage,einzeln_buchbar,sortierung) VALUES
 ('KI_ONE','ki','ONE','WhatsApp oder E-Mail, 1.500 Nachrichten, ohne Telefonagent','monatlich',12,NULL,1500,NULL,false,true,10),
 ('KI_BUSINESS','ki','BUSINESS','Telefon und WhatsApp, 600 Minuten, 3.000 Nachrichten','monatlich',12,600,3000,55,false,true,11),
 ('KI_KOMPLETT','ki','KOMPLETT','Telefon, WhatsApp, E-Mail, 1.000 Minuten, 5.000 Nachrichten','monatlich',12,1000,5000,49,false,true,12),
 ('KI_ENTERPRISE','ki','ENTERPRISE','Mehrere Standorte, hohes Volumen, individuelle Anbindung','monatlich',NULL,NULL,NULL,NULL,true,true,13),
 ('WEB_LANDING_START','website','LANDING START','Eine Seite auf Vorlagenbasis, Texte und Bilder liefert der Kunde','projekt_pflege',12,NULL,NULL,NULL,false,true,20),
 ('WEB_LANDING','website','LANDING','Conversion-Onepager mit Texten, Bildern und Terminbuchung','projekt_pflege',12,NULL,NULL,NULL,false,true,21),
 ('WEB_BUSINESS','website','BUSINESS WEB','Bis sieben Inhaltsseiten, Struktur, Texte und Bilder','projekt_pflege',12,NULL,NULL,NULL,false,true,22),
 ('WEB_FUNNEL','website','WEB + FUNNEL','Bis zwölf Seiten mit Anfrage- oder Verkaufsstrecke','projekt_pflege',12,NULL,NULL,NULL,false,true,23),
 ('CI_BASIC','ci','CI BASIC','Logo, Farbwelt und Schriftwelt','projekt',NULL,NULL,NULL,NULL,false,true,30),
 ('CI_BUSINESS','ci','CI BUSINESS','Zusätzlich Visitenkarte, Briefbogen, Vorlagen','projekt',NULL,NULL,NULL,NULL,false,true,31),
 ('CI_PREMIUM','ci','CI PREMIUM','Zusätzlich Markenhandbuch und Social-Kit','projekt',NULL,NULL,NULL,NULL,false,true,32),
 ('SOCIAL_MEDIA','sichtbarkeit','SOCIAL MEDIA','Vier Beiträge auf zwei Kanälen, Redaktionsplan, Reporting','monatlich',12,NULL,NULL,NULL,false,true,40),
 ('LOCAL_VISIBILITY','sichtbarkeit','LOCAL VISIBILITY','Google-Profil, lokale Suchmaschinenoptimierung, Bewertungen','monatlich',12,NULL,NULL,NULL,false,true,41),
 ('BEWERTUNGSANFRAGEN','sichtbarkeit','Bewertungsanfragen','Automatisiert nach Auftragsabschluss','monatlich',12,NULL,NULL,NULL,false,true,42),
 ('NEWSLETTER','sichtbarkeit','Newsletter-System','Aufbau, Versand, Vorlagen, Auswertung','monatlich',12,NULL,NULL,NULL,false,true,43),
 ('GBP_POSTINGS','sichtbarkeit','Google-Business-Postings','Regelmäßige Beiträge im Google-Profil','monatlich',12,NULL,NULL,NULL,false,true,44),
 ('PB_ESSENTIAL','personal_branding','ESSENTIAL','Vier Beiträge, Profilaufbau, Redaktionsplan','monatlich',3,NULL,NULL,NULL,false,true,50),
 ('PB_GROWTH','personal_branding','GROWTH','Acht Inhalte, Themenplanung, Grafiken','monatlich',3,NULL,NULL,NULL,false,true,51),
 ('PB_AUTHORITY','personal_branding','AUTHORITY','12–16 Inhalte, Strategie und Positionierung','monatlich',3,NULL,NULL,NULL,false,true,52),
 ('LEAD_AGENT','lead','LEAD-AGENT','Automatisierte Leadrecherche, mandantenfähig, White-Label','monatlich',12,NULL,NULL,NULL,false,true,60),
 ('GOOGLE_ADS_AGENT','lead','GOOGLE ADS AGENT','Kampagnenentwürfe und Optimierung zur Freigabe (Mediabudget zahlt der Kunde direkt an Google)','monatlich',12,NULL,NULL,NULL,false,true,61);

INSERT INTO produkt_preise (produkt_code,gueltig_ab,einrichtung_cent,monatlich_cent,projekt_cent,ab_preis,quelle) VALUES
 ('KI_ONE','2026-09-01',149000,34900,NULL,false,'Preisliste Stand September 2026'),
 ('KI_BUSINESS','2026-09-01',249000,69900,NULL,false,'Preisliste Stand September 2026'),
 ('KI_KOMPLETT','2026-09-01',349000,119000,NULL,false,'Preisliste Stand September 2026'),
 ('WEB_LANDING_START','2026-09-01',NULL,5900,129000,false,'Preisliste Stand September 2026'),
 ('WEB_LANDING','2026-09-01',NULL,5900,229000,false,'Preisliste Stand September 2026'),
 ('WEB_BUSINESS','2026-09-01',NULL,8900,449000,false,'Preisliste Stand September 2026'),
 ('WEB_FUNNEL','2026-09-01',NULL,12900,699000,false,'Preisliste Stand September 2026'),
 ('CI_BASIC','2026-09-01',NULL,NULL,129000,false,'Preisliste Stand September 2026'),
 ('CI_BUSINESS','2026-09-01',NULL,NULL,249000,false,'Preisliste Stand September 2026'),
 ('CI_PREMIUM','2026-09-01',NULL,NULL,449000,false,'Preisliste Stand September 2026'),
 ('SOCIAL_MEDIA','2026-09-01',NULL,74900,NULL,false,'Preisliste Stand September 2026'),
 ('LOCAL_VISIBILITY','2026-09-01',NULL,44900,NULL,false,'Preisliste Stand September 2026'),
 ('BEWERTUNGSANFRAGEN','2026-09-01',NULL,14900,NULL,true,'Preisliste Stand September 2026'),
 ('NEWSLETTER','2026-09-01',NULL,24900,NULL,true,'Preisliste Stand September 2026'),
 ('GBP_POSTINGS','2026-09-01',NULL,19900,NULL,true,'Preisliste Stand September 2026'),
 ('PB_ESSENTIAL','2026-09-01',99000,69000,NULL,false,'Preisliste Stand September 2026'),
 ('PB_GROWTH','2026-09-01',149000,169000,NULL,false,'Preisliste Stand September 2026'),
 ('PB_AUTHORITY','2026-09-01',299000,349000,NULL,false,'Preisliste Stand September 2026'),
 ('LEAD_AGENT','2026-09-01',249000,89000,NULL,false,'Preisliste Stand September 2026'),
 ('GOOGLE_ADS_AGENT','2026-09-01',149000,59900,NULL,false,'Preisliste Stand September 2026');

INSERT INTO konditionen (schluessel,wert_text,wert_zahl,beschreibung) VALUES
 ('preisstand','Stand September 2026',NULL,'Alle Preise netto zuzüglich gesetzlicher Umsatzsteuer'),
 ('kombi_web_ki_cent',NULL,50000,'Nachlass Website und KI-Kommunikation zusammen (ab Paket BUSINESS)'),
 ('kombi_ci_web_cent',NULL,50000,'Nachlass Corporate Identity und Website gleichzeitig'),
 ('anzahlung_prozent',NULL,50,'Projekte: Anzahlung bei Auftragserteilung'),
 ('restzahlung_prozent',NULL,50,'Projekte: Rest bei Abnahme'),
 ('zahlungsziel_tage_min',NULL,7,'Zahlungsziel bei Rechnungen, von'),
 ('zahlungsziel_tage_max',NULL,14,'Zahlungsziel bei Rechnungen, bis'),
 ('mindestlaufzeit_monate',NULL,12,'Monatliche Leistungen, danach monatlich kündbar'),
 ('mindestlaufzeit_personal_branding_monate',NULL,3,'Personal Branding'),
 ('abbuchung','SEPA-Lastschrift zu Monatsbeginn für den laufenden Monat',NULL,'Keine Vorauszahlung für die gesamte Laufzeit');

INSERT INTO module (code,name,beschreibung,art,sortierung) VALUES
 ('email_agent','E-Mail-Agent','Beantwortet eingehende E-Mails','agent',20),
 ('website_chat','Website-Chat','Der Agent beantwortet Fragen auf der Website','agent',21),
 ('kalender','Termine und Erinnerungen','Buchung und Erinnerungen per Kalender','agent',22),
 ('noshow','No-Show-Schutz','Weniger Terminausfälle','agent',23),
 ('gbp_optimierer','GBP-Post-Optimierer','Beiträge für das Google-Unternehmensprofil','agent',24),
 ('branchen_radar','Branchen-Update-Radar','Wöchentliche Branchen-News per Mail','agent',25),
 ('werbeanzeigen','Werbeanzeigen','Anzeigen und Berichte im Kundenbereich','agent',26);
INSERT INTO module (code,name,beschreibung,sortierung) VALUES
 ('ki_chat','KI-Assistent und Chatverlauf','Gespräche mit dem Agenten im Kundenbereich',1),
 ('anfragen_termine','Anfragen und Termine','Eingehende Anfragen und gebuchte Termine',2),
 ('kontakte_angebote_vertraege','Kontakte, Angebote, Verträge','Eigene Kontakte und Dokumente einsehen',3),
 ('werbung_berichte','Werbung und Berichte','Anzeigen, Auswertungen und Berichte',4),
 ('website','Website und Landingpages','Status und Verwaltung der Kunden-Website',5),
 ('wochenangebote','Wochenangebote-Upload','Kunde lädt Angebote hoch (PDF, JPG, PNG), Website wird aktualisiert',6),
 ('automationen','Automationen','Übersicht der laufenden Agenten und Abläufe',7),
 ('einstellungen','Einstellungen','Firmendaten und Zugänge',8);

COMMIT;
