-- 001 Kern: Hilfsfunktionen, Kunden, Zugänge, Sitzungen, Audit-Log.
-- Mandantentrennung: jede Kundentabelle trägt kunden_id. Das Portal setzt pro Datenbank-Sitzung
--   app.rolle     = 'kunde' | 'admin' | 'system'   (system = n8n / Hintergrunddienste)
--   app.kunden_id = UUID des Kunden (nur bei rolle 'kunde')
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION app_rolle() RETURNS text LANGUAGE sql STABLE AS $$ SELECT coalesce(current_setting('app.rolle', true), '') $$;
CREATE OR REPLACE FUNCTION app_ist_admin() RETURNS boolean LANGUAGE sql STABLE AS $$ SELECT app_rolle() = 'admin' $$;
CREATE OR REPLACE FUNCTION app_intern() RETURNS boolean LANGUAGE sql STABLE AS $$ SELECT app_rolle() IN ('admin','system') $$;
CREATE OR REPLACE FUNCTION app_kunden_id() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.kunden_id', true), '')::uuid $$;
CREATE OR REPLACE FUNCTION set_geaendert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.geaendert_am = now(); RETURN NEW; END $$;

-- RLS-Helfer ------------------------------------------------------------
-- Kundentabelle: Kunde sieht nur eigene Zeilen. kunde_schreibt=true: darf auch ändern/anlegen.
CREATE OR REPLACE FUNCTION rls_kunde(t regclass, kunde_schreibt boolean DEFAULT false) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', t);
  EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', t);
  IF kunde_schreibt THEN
    EXECUTE format('CREATE POLICY trennung ON %s USING (app_intern() OR kunden_id = app_kunden_id()) WITH CHECK (app_intern() OR kunden_id = app_kunden_id())', t);
  ELSE
    EXECUTE format('CREATE POLICY lesen ON %s FOR SELECT USING (app_intern() OR kunden_id = app_kunden_id())', t);
    EXECUTE format('CREATE POLICY intern_schreiben ON %s FOR ALL USING (app_intern()) WITH CHECK (app_intern())', t);
  END IF;
END $$;

-- Nur intern (Admin und Hintergrunddienste); Kunden sehen nichts.
CREATE OR REPLACE FUNCTION rls_intern(t regclass) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', t);
  EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', t);
  EXECUTE format('CREATE POLICY intern ON %s FOR ALL USING (app_intern()) WITH CHECK (app_intern())', t);
END $$;

-- Katalogdaten: alle dürfen lesen, nur intern ändern.
CREATE OR REPLACE FUNCTION rls_katalog(t regclass) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', t);
  EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', t);
  EXECUTE format('CREATE POLICY lesen ON %s FOR SELECT USING (true)', t);
  EXECUTE format('CREATE POLICY intern_schreiben ON %s FOR ALL USING (app_intern()) WITH CHECK (app_intern())', t);
END $$;

-- Kunden --------------------------------------------------------------------
CREATE SEQUENCE kundennummer_seq START 1001;

CREATE TABLE kunden (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kundennummer    text NOT NULL UNIQUE DEFAULT ('MK-' || nextval('kundennummer_seq')),
  firma           text NOT NULL,
  rechtsform      text,
  ansprechpartner text,
  email           text,
  telefon         text,
  branche         text,
  strasse         text,
  plz             text,
  ort             text,
  domain          text,
  paket_code      text,                     -- Verweis auf produkte(code), wird in 010 gesetzt
  status          text NOT NULL DEFAULT 'onboarding' CHECK (status IN ('onboarding','aktiv','pausiert','gekuendigt','beendet')),
  vertriebspartner_id uuid,                 -- Verweis wird in 040 gesetzt
  notizen         text,
  erstellt_am     timestamptz NOT NULL DEFAULT now(),
  geaendert_am    timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER kunden_geaendert BEFORE UPDATE ON kunden FOR EACH ROW EXECUTE FUNCTION set_geaendert();
ALTER TABLE kunden ENABLE ROW LEVEL SECURITY; ALTER TABLE kunden FORCE ROW LEVEL SECURITY;
CREATE POLICY lesen ON kunden FOR SELECT USING (app_intern() OR id = app_kunden_id());
CREATE POLICY intern_schreiben ON kunden FOR ALL USING (app_intern()) WITH CHECK (app_intern());

CREATE TABLE benutzer (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email          text NOT NULL,
  name           text,
  passwort_hash  text,                      -- vom Portal erzeugt, nie Klartext
  rolle          text NOT NULL CHECK (rolle IN ('admin','kunde')),
  kunden_id      uuid REFERENCES kunden(id) ON DELETE CASCADE,
  aktiv          boolean NOT NULL DEFAULT true,
  einladung_token_hash text,
  einladung_ablauf     timestamptz,
  fehlversuche   int NOT NULL DEFAULT 0,
  gesperrt_bis   timestamptz,
  letzter_login  timestamptz,
  erstellt_am    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT benutzer_kunde_passt CHECK ((rolle = 'kunde' AND kunden_id IS NOT NULL) OR (rolle = 'admin' AND kunden_id IS NULL))
);
CREATE UNIQUE INDEX benutzer_email_uq ON benutzer (lower(email));
CREATE INDEX benutzer_kunden_idx ON benutzer (kunden_id);
SELECT rls_intern('benutzer');

CREATE TABLE sitzungen (
  token_hash   text PRIMARY KEY,
  benutzer_id  uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  erstellt_am  timestamptz NOT NULL DEFAULT now(),
  ablauf       timestamptz NOT NULL,
  ip           text
);
CREATE INDEX sitzungen_benutzer_idx ON sitzungen (benutzer_id);
SELECT rls_intern('sitzungen');

CREATE TABLE audit_log (
  id          bigserial PRIMARY KEY,
  zeit        timestamptz NOT NULL DEFAULT now(),
  benutzer_id uuid,
  kunden_id   uuid,
  aktion      text NOT NULL,
  details     jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX audit_zeit_idx ON audit_log (zeit DESC);
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY; ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;
CREATE POLICY lesen ON audit_log FOR SELECT USING (app_intern());
CREATE POLICY schreiben ON audit_log FOR INSERT WITH CHECK (true);   -- jeder darf protokollieren, niemand ändert oder löscht

COMMIT;
