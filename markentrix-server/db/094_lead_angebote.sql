-- Angebot direkt an einen Lead: Beleg ohne Kunde, mit Annahme-Link für den Empfänger
ALTER TABLE belege ALTER COLUMN kunden_id DROP NOT NULL;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS lead_id uuid REFERENCES leads(id) ON DELETE SET NULL;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS annahme_hash text;          -- SHA-256 des geheimen Links, der Link selbst wird nicht gespeichert
ALTER TABLE belege ADD COLUMN IF NOT EXISTS angesehen_am timestamptz;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS angenommen_am timestamptz;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS angenommen_von text;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS abgelehnt_am timestamptz;
CREATE UNIQUE INDEX IF NOT EXISTS belege_annahme_idx ON belege (annahme_hash) WHERE annahme_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS belege_lead_idx ON belege (lead_id) WHERE lead_id IS NOT NULL;
ALTER TABLE belege DROP CONSTRAINT IF EXISTS belege_empfaenger_chk;
ALTER TABLE belege ADD CONSTRAINT belege_empfaenger_chk CHECK (kunden_id IS NOT NULL OR art = 'angebot');

-- Wird ein Lead gelöscht (Löschfrist, Widerspruch), verschwinden auch seine Angebote, die noch an keinen Kunden gebunden sind
CREATE OR REPLACE FUNCTION lead_angebote_loeschen() RETURNS trigger AS $$
BEGIN
  DELETE FROM belege WHERE lead_id = OLD.id AND kunden_id IS NULL;
  RETURN OLD;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS leads_angebote_loeschen ON leads;
CREATE TRIGGER leads_angebote_loeschen BEFORE DELETE ON leads FOR EACH ROW EXECUTE FUNCTION lead_angebote_loeschen();
