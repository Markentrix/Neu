-- 160 Terminvorschläge für ein Beratungsgespräch, ohne Angebot: an Kunden und Leads, mit Auswahl-Link in der Mail.
-- Der Empfänger bestätigt einen Vorschlag, daraus entsteht ein Eintrag in gespraechstermine (Kalender, Einladung, Erinnerungen).
BEGIN;
CREATE TABLE IF NOT EXISTS terminvorschlaege (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token        text NOT NULL UNIQUE,
  kunden_id    uuid REFERENCES kunden(id) ON DELETE CASCADE,
  lead_id      uuid REFERENCES leads(id) ON DELETE SET NULL,
  name         text NOT NULL,
  email        text NOT NULL,
  zeiten       jsonb NOT NULL,
  nachricht    text,
  status       text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','gewaehlt','zurueckgezogen')),
  gespraech_id uuid REFERENCES gespraechstermine(id) ON DELETE SET NULL,
  gesendet     boolean NOT NULL DEFAULT false,
  erstellt_von text,
  erstellt_am  timestamptz NOT NULL DEFAULT now(),
  CHECK (kunden_id IS NOT NULL OR lead_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS terminvorschlaege_kunde_idx ON terminvorschlaege (kunden_id) WHERE kunden_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS terminvorschlaege_lead_idx ON terminvorschlaege (lead_id) WHERE lead_id IS NOT NULL;
SELECT rls_intern('terminvorschlaege');
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS kunden_id uuid REFERENCES kunden(id) ON DELETE SET NULL;
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS vorschlag_id uuid;
COMMIT;
