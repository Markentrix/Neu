-- Gutschein-Anfragen von der Website: Zahlungslink (PayPal.Me) und Code per Mail im Namen des Betriebs.
-- Das Portal sieht PayPal-Zahlungen nicht. Den Code trägt deshalb der Inhaber nach dem Zahlungseingang ein.
BEGIN;
CREATE TABLE IF NOT EXISTS website_gutscheine (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  anfrage_id uuid,
  ref text NOT NULL,
  name text NOT NULL, email text, telefon text,
  betrag numeric(10,2),
  empfaenger text, widmung text,
  status text NOT NULL DEFAULT 'angefragt' CHECK (status IN ('angefragt','zahlungslink_gesendet','gesendet','storniert')),
  code text,
  zahlungslink_am timestamptz, gesendet_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS website_gutscheine_idx ON website_gutscheine (kunden_id, erstellt_am DESC);
SELECT rls_intern('website_gutscheine');
COMMIT;
