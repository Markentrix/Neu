-- Kundenbenachrichtigung, sobald eine neue Website online ist oder ein Update eingespielt wurde
BEGIN;
CREATE TABLE IF NOT EXISTS website_meldungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  domain text NOT NULL,
  upload_id text NOT NULL,
  hinweis text NOT NULL DEFAULT '',
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  gesendet_am timestamptz,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','gesendet','verworfen'))
);
CREATE INDEX IF NOT EXISTS website_meldungen_offen_idx ON website_meldungen (status, erstellt_am);
SELECT rls_intern('website_meldungen');
COMMIT;
