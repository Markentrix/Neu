-- Vertriebler-Login und verschlüsselte Portal-Einstellungen (E-Mail-Zugang, API-Schlüssel)
BEGIN;
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS vertriebspartner_id uuid REFERENCES vertriebspartner(id) ON DELETE CASCADE;
ALTER TABLE benutzer DROP CONSTRAINT IF EXISTS benutzer_rolle_check;
ALTER TABLE benutzer DROP CONSTRAINT IF EXISTS benutzer_kunde_passt;
ALTER TABLE benutzer ADD CONSTRAINT benutzer_rolle_check CHECK (rolle IN ('admin','kunde','vertrieb'));
ALTER TABLE benutzer ADD CONSTRAINT benutzer_kunde_passt CHECK (
  (rolle = 'kunde'    AND kunden_id IS NOT NULL AND vertriebspartner_id IS NULL) OR
  (rolle = 'admin'    AND kunden_id IS NULL     AND vertriebspartner_id IS NULL) OR
  (rolle = 'vertrieb' AND kunden_id IS NULL     AND vertriebspartner_id IS NOT NULL));
CREATE INDEX IF NOT EXISTS benutzer_partner_idx ON benutzer (vertriebspartner_id);

CREATE TABLE portal_einstellungen (
  schluessel   text PRIMARY KEY,
  wert         text NOT NULL,            -- verschlüsselt (Fernet), Schlüssel liegt nur in .env
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('portal_einstellungen');
COMMIT;
