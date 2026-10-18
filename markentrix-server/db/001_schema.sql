-- Markentrix Datenbank: Kunden, Zugänge, Pakete/Module, Projekte, Anfragen, Termine,
-- Kontakte, Angebote, Verträge, Wochenangebote-Uploads, Chatverlauf, Berichte.
-- Jeder Kundendatensatz trägt kunde_id. Row-Level-Security trennt die Kunden:
-- Das Portal setzt pro Anfrage  app.rolle  ('admin' oder 'kunde')  und  app.kunde_id.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------ Hilfsfunktionen
CREATE OR REPLACE FUNCTION app_ist_admin() RETURNS boolean
  LANGUAGE sql STABLE AS $$ SELECT coalesce(current_setting('app.rolle', true), '') = 'admin' $$;

CREATE OR REPLACE FUNCTION app_kunde_id() RETURNS uuid
  LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.kunde_id', true), '')::uuid $$;

CREATE OR REPLACE FUNCTION set_geaendert() RETURNS trigger
  LANGUAGE plpgsql AS $$ BEGIN NEW.geaendert_am = now(); RETURN NEW; END $$;

-- ------------------------------------------------------------ Stammdaten
CREATE TABLE pakete (
  code        text PRIMARY KEY,
  name        text NOT NULL,
  sortierung  int  NOT NULL DEFAULT 0
);

CREATE TABLE module (
  code          text PRIMARY KEY,
  name          text NOT NULL,
  beschreibung  text NOT NULL DEFAULT '',
  sortierung    int  NOT NULL DEFAULT 0
);

-- Welche Module ein Paket von Haus aus mitbringt (im Admin-Bereich pro Kunde überschreibbar)
CREATE TABLE paket_module (
  paket_code  text NOT NULL REFERENCES pakete(code) ON UPDATE CASCADE ON DELETE CASCADE,
  modul_code  text NOT NULL REFERENCES module(code) ON UPDATE CASCADE ON DELETE CASCADE,
  PRIMARY KEY (paket_code, modul_code)
);

-- ------------------------------------------------------------ Kunden
CREATE SEQUENCE kundennummer_seq START 1001;

CREATE TABLE kunden (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kundennummer   text NOT NULL UNIQUE DEFAULT ('MK-' || nextval('kundennummer_seq')),
  firma          text NOT NULL,
  ansprechpartner text,
  email          text,
  telefon        text,
  branche        text,
  domain         text,
  paket_code     text REFERENCES pakete(code) ON UPDATE CASCADE,
  status         text NOT NULL DEFAULT 'onboarding' CHECK (status IN ('onboarding','aktiv','pausiert','beendet')),
  notizen        text,
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  geaendert_am   timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER kunden_geaendert BEFORE UPDATE ON kunden FOR EACH ROW EXECUTE FUNCTION set_geaendert();

CREATE TABLE benutzer (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email          text NOT NULL,
  passwort_hash  text,                       -- vom Portal erzeugt (Argon2/bcrypt), nie Klartext
  rolle          text NOT NULL CHECK (rolle IN ('admin','kunde')),
  kunde_id       uuid REFERENCES kunden(id) ON DELETE CASCADE,
  aktiv          boolean NOT NULL DEFAULT true,
  einladung_token_hash text,
  einladung_ablauf     timestamptz,
  letzter_login  timestamptz,
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT benutzer_kunde_passt CHECK ((rolle = 'kunde' AND kunde_id IS NOT NULL) OR (rolle = 'admin' AND kunde_id IS NULL))
);
CREATE UNIQUE INDEX benutzer_email_uq ON benutzer (lower(email));
CREATE INDEX benutzer_kunde_idx ON benutzer (kunde_id);

CREATE TABLE sitzungen (
  token_hash   text PRIMARY KEY,
  benutzer_id  uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  erstellt_am  timestamptz NOT NULL DEFAULT now(),
  ablauf       timestamptz NOT NULL,
  ip           text
);
CREATE INDEX sitzungen_benutzer_idx ON sitzungen (benutzer_id);

CREATE TABLE kunden_module (
  kunde_id      uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  modul_code    text NOT NULL REFERENCES module(code) ON UPDATE CASCADE ON DELETE CASCADE,
  aktiv         boolean NOT NULL DEFAULT false,
  geaendert_am  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kunde_id, modul_code)
);

-- ------------------------------------------------------------ Kundendaten
CREATE TABLE projekte (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel       text NOT NULL,
  art         text NOT NULL DEFAULT 'website' CHECK (art IN ('website','landingpage','kampagne','automation','sonstiges')),
  status      text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','in_arbeit','live','pausiert','fertig')),
  url         text,
  beschreibung text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX projekte_kunde_idx ON projekte (kunde_id);
CREATE TRIGGER projekte_geaendert BEFORE UPDATE ON projekte FOR EACH ROW EXECUTE FUNCTION set_geaendert();

CREATE TABLE anfragen (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  name        text,
  kontakt     text,
  nachricht   text,
  quelle      text NOT NULL DEFAULT 'website' CHECK (quelle IN ('website','email','telefon','chat','sonstiges')),
  status      text NOT NULL DEFAULT 'neu' CHECK (status IN ('neu','in_bearbeitung','beantwortet','erledigt')),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX anfragen_kunde_idx ON anfragen (kunde_id, erstellt_am DESC);

CREATE TABLE termine (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  anfrage_id  uuid REFERENCES anfragen(id) ON DELETE SET NULL,
  titel       text NOT NULL,
  beginn      timestamptz NOT NULL,
  ende        timestamptz,
  status      text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','bestaetigt','abgesagt','erledigt','nicht_erschienen')),
  notiz       text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX termine_kunde_idx ON termine (kunde_id, beginn);

CREATE TABLE kontakte (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  name        text NOT NULL,
  firma       text,
  email       text,
  telefon     text,
  notiz       text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX kontakte_kunde_idx ON kontakte (kunde_id);

CREATE TABLE angebote (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  nummer      text,
  titel       text NOT NULL,
  betrag_cent bigint,
  status      text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','versendet','angenommen','abgelehnt')),
  dateipfad   text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX angebote_kunde_idx ON angebote (kunde_id);

CREATE TABLE vertraege (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel       text NOT NULL,
  paket_code  text REFERENCES pakete(code) ON UPDATE CASCADE,
  beginn      date,
  ende        date,
  status      text NOT NULL DEFAULT 'aktiv' CHECK (status IN ('entwurf','aktiv','gekuendigt','beendet')),
  dateipfad   text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX vertraege_kunde_idx ON vertraege (kunde_id);

CREATE TABLE wochenangebote_uploads (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  dateiname   text NOT NULL,
  mime        text NOT NULL CHECK (mime IN ('application/pdf','image/jpeg','image/png')),
  groesse     bigint NOT NULL CHECK (groesse > 0 AND groesse <= 10485760),
  dateipfad   text NOT NULL,
  status      text NOT NULL DEFAULT 'hochgeladen' CHECK (status IN ('hochgeladen','wird_verarbeitet','veroeffentlicht','fehler')),
  gueltig_von date,
  gueltig_bis date,
  fehlertext  text,
  hochgeladen_von uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  veroeffentlicht_am timestamptz
);
CREATE INDEX wochenangebote_kunde_idx ON wochenangebote_uploads (kunde_id, erstellt_am DESC);

CREATE TABLE chat_verlauf (
  id          bigserial PRIMARY KEY,
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  benutzer_id uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  absender    text NOT NULL CHECK (absender IN ('kunde','agent')),
  text        text NOT NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX chat_kunde_idx ON chat_verlauf (kunde_id, erstellt_am);

CREATE TABLE berichte (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunde_id    uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel       text NOT NULL,
  art         text NOT NULL DEFAULT 'werbung' CHECK (art IN ('werbung','website','social','sonstiges')),
  zeitraum_von date,
  zeitraum_bis date,
  daten       jsonb NOT NULL DEFAULT '{}'::jsonb,
  dateipfad   text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX berichte_kunde_idx ON berichte (kunde_id);

-- Nur für Admins sichtbar
CREATE TABLE audit_log (
  id          bigserial PRIMARY KEY,
  zeit        timestamptz NOT NULL DEFAULT now(),
  benutzer_id uuid,
  kunde_id    uuid,
  aktion      text NOT NULL,
  details     jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX audit_zeit_idx ON audit_log (zeit DESC);

-- ------------------------------------------------------------ Row-Level-Security
-- Tabellen mit kunde_id: Kunde sieht nur eigene Zeilen, Admin sieht alle.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['kunden_module','projekte','anfragen','termine','kontakte','angebote','vertraege',
                           'wochenangebote_uploads','chat_verlauf','berichte']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY trennung ON %I USING (app_ist_admin() OR kunde_id = app_kunde_id()) WITH CHECK (app_ist_admin() OR kunde_id = app_kunde_id())', t);
  END LOOP;
END $$;

-- Kunden: Kunde sieht nur den eigenen Datensatz (nur lesen), Admin alles
ALTER TABLE kunden ENABLE ROW LEVEL SECURITY;
ALTER TABLE kunden FORCE ROW LEVEL SECURITY;
CREATE POLICY lesen ON kunden FOR SELECT USING (app_ist_admin() OR id = app_kunde_id());
CREATE POLICY admin_schreiben ON kunden FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());

-- Stammdaten: alle dürfen lesen, nur Admin ändert
ALTER TABLE pakete ENABLE ROW LEVEL SECURITY; ALTER TABLE pakete FORCE ROW LEVEL SECURITY;
ALTER TABLE module ENABLE ROW LEVEL SECURITY; ALTER TABLE module FORCE ROW LEVEL SECURITY;
ALTER TABLE paket_module ENABLE ROW LEVEL SECURITY; ALTER TABLE paket_module FORCE ROW LEVEL SECURITY;
CREATE POLICY lesen ON pakete FOR SELECT USING (true);
CREATE POLICY lesen ON module FOR SELECT USING (true);
CREATE POLICY lesen ON paket_module FOR SELECT USING (true);
CREATE POLICY admin_schreiben ON pakete FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());
CREATE POLICY admin_schreiben ON module FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());
CREATE POLICY admin_schreiben ON paket_module FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());

-- Kunden-Module: Kunde darf nur lesen, nicht selbst Module einschalten
DROP POLICY trennung ON kunden_module;
CREATE POLICY lesen ON kunden_module FOR SELECT USING (app_ist_admin() OR kunde_id = app_kunde_id());
CREATE POLICY admin_schreiben ON kunden_module FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());

-- Angebote, Verträge, Berichte: Kunde nur lesen
DROP POLICY trennung ON angebote;  CREATE POLICY lesen ON angebote  FOR SELECT USING (app_ist_admin() OR kunde_id = app_kunde_id());
DROP POLICY trennung ON vertraege; CREATE POLICY lesen ON vertraege FOR SELECT USING (app_ist_admin() OR kunde_id = app_kunde_id());
DROP POLICY trennung ON berichte;  CREATE POLICY lesen ON berichte  FOR SELECT USING (app_ist_admin() OR kunde_id = app_kunde_id());
CREATE POLICY admin_schreiben ON angebote  FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());
CREATE POLICY admin_schreiben ON vertraege FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());
CREATE POLICY admin_schreiben ON berichte  FOR ALL USING (app_ist_admin()) WITH CHECK (app_ist_admin());

-- Zugänge, Sitzungen, Audit: nur das Portal-Backend (Rolle mk_app) und nur über Admin-Kontext
-- bzw. interne Funktionen. Kunden greifen darauf nie direkt zu.
ALTER TABLE benutzer ENABLE ROW LEVEL SECURITY; ALTER TABLE benutzer FORCE ROW LEVEL SECURITY;
ALTER TABLE sitzungen ENABLE ROW LEVEL SECURITY; ALTER TABLE sitzungen FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY; ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;
-- Login-Prüfung läuft vor der Anmeldung, daher im Kontext 'system'
CREATE POLICY system_oder_admin ON benutzer USING (app_ist_admin() OR coalesce(current_setting('app.rolle', true),'') = 'system')
  WITH CHECK (app_ist_admin() OR coalesce(current_setting('app.rolle', true),'') = 'system');
CREATE POLICY system_oder_admin ON sitzungen USING (app_ist_admin() OR coalesce(current_setting('app.rolle', true),'') = 'system')
  WITH CHECK (app_ist_admin() OR coalesce(current_setting('app.rolle', true),'') = 'system');
CREATE POLICY admin_lesen ON audit_log FOR SELECT USING (app_ist_admin());
CREATE POLICY schreiben ON audit_log FOR INSERT WITH CHECK (true);

-- ------------------------------------------------------------ Startdaten
INSERT INTO pakete (code, name, sortierung) VALUES
  ('KI_ONE','KI ONE',1), ('BUSINESS','BUSINESS',2), ('KOMPLETT','KOMPLETT',3);

INSERT INTO module (code, name, beschreibung, sortierung) VALUES
  ('email','E-Mail-Agent','Beantwortet eingehende E-Mails',1),
  ('chat','Website-Chat','Der Agent beantwortet Fragen auf der Website',2),
  ('kalender','Termine & Erinnerungen','Buchung und Erinnerungen per Kalender',3),
  ('wochenangebote','Wochenangebote-Upload','Kunde lädt Angebote hoch, Website wird aktualisiert',4),
  ('noshow','No-Show-Schutz','Weniger Terminausfälle',5),
  ('gbp','GBP-Post-Optimierer','Beiträge für das Google-Unternehmensprofil',6),
  ('radar','Branchen-Update-Radar','Wöchentliche Branchen-News per Mail',7),
  ('werbung','Werbeanzeigen','Anzeigen und Berichte im Kundenbereich',8);

COMMIT;
