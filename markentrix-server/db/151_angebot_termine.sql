-- Terminvorschläge im Angebot: bis zu 3 Zeiten für ein Beratungsgespräch; der Kunde wählt im Angebots-Link, der Termin landet im Admin-Kalender
ALTER TABLE belege ADD COLUMN IF NOT EXISTS terminvorschlaege jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS beleg_id uuid REFERENCES belege(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS gespraechstermine_beleg_idx ON gespraechstermine (beleg_id) WHERE beleg_id IS NOT NULL;
