-- Verträge aus dem Portal: Referenzvertrag (Kunde) und Handelsvertretervertrag (Vertriebspartner), vorausgefüllt versendet, unterschrieben abgelegt
BEGIN;
CREATE TABLE IF NOT EXISTS vertragsdokumente (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL CHECK (art IN ('referenz','handelsvertreter')),
  kunden_id uuid REFERENCES kunden(id) ON DELETE CASCADE,
  partner_id uuid REFERENCES vertriebspartner(id) ON DELETE CASCADE,
  daten jsonb NOT NULL DEFAULT '{}'::jsonb,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  gesendet_am timestamptz,
  gesendet_an text,
  unterschrieben_am date,
  datei bytea, datei_name text, datei_typ text, hochgeladen_am timestamptz,
  CHECK ((art = 'referenz' AND kunden_id IS NOT NULL AND partner_id IS NULL) OR (art = 'handelsvertreter' AND partner_id IS NOT NULL AND kunden_id IS NULL))
);
CREATE INDEX IF NOT EXISTS vertragsdokumente_kunde_idx ON vertragsdokumente (kunden_id, erstellt_am DESC);
CREATE INDEX IF NOT EXISTS vertragsdokumente_partner_idx ON vertragsdokumente (partner_id, erstellt_am DESC);
SELECT rls_intern('vertragsdokumente');
COMMIT;
